-- Professional SQL Analytical Reports
-- Target Database: warehouse_db
USE warehouse_db;

-- ====================================================================
-- 1. TOP SELLING PRODUCTS
-- Returns the top 10 products by gross sales volume and revenue.
-- Uses: GROUP BY, ORDER BY.
-- ====================================================================
-- QUERY: Top Selling Products
SELECT 
    p.product_id,
    p.sku,
    p.product_name,
    c.category_name,
    SUM(oi.quantity) AS total_units_sold,
    SUM(oi.quantity * oi.unit_price) AS gross_revenue
FROM order_items oi
JOIN products p ON oi.product_id = p.product_id
JOIN categories c ON p.category_id = c.category_id
JOIN orders o ON oi.order_id = o.order_id
WHERE o.status NOT IN ('Cancelled')
GROUP BY p.product_id, p.sku, p.product_name, c.category_name
ORDER BY gross_revenue DESC
LIMIT 10;


-- ====================================================================
-- 2. LOWEST INVENTORY (LOW STOCK ALERTS)
-- Shows products with available stock <= reorder level.
-- Uses: GROUP BY, HAVING.
-- ====================================================================
-- QUERY: Lowest Inventory
SELECT 
    p.product_id,
    p.sku,
    p.product_name,
    COALESCE(SUM(i.quantity_on_hand), 0) AS total_on_hand,
    COALESCE(SUM(i.quantity_reserved), 0) AS total_reserved,
    COALESCE(SUM(i.quantity_on_hand - i.quantity_reserved), 0) AS total_available,
    p.reorder_level
FROM products p
LEFT JOIN inventory i ON p.product_id = i.product_id
GROUP BY p.product_id, p.sku, p.product_name, p.reorder_level
HAVING total_available <= p.reorder_level
ORDER BY total_available ASC;


-- ====================================================================
-- 3. INVENTORY VALUE (VALUATION)
-- Computes the total cost and retail valuation of current inventory.
-- Uses: JOIN, SUM.
-- ====================================================================
-- QUERY: Inventory Value
SELECT 
    c.category_name,
    SUM(i.quantity_on_hand) AS total_units_in_stock,
    SUM(i.quantity_on_hand * p.cost_price) AS total_inventory_cost_value,
    SUM(i.quantity_on_hand * p.sale_price) AS total_inventory_retail_value,
    SUM(i.quantity_on_hand * (p.sale_price - p.cost_price)) AS potential_profit_margin
FROM inventory i
JOIN products p ON i.product_id = p.product_id
JOIN categories c ON p.category_id = c.category_id
GROUP BY c.category_name
ORDER BY total_inventory_cost_value DESC;


-- ====================================================================
-- 4. DAILY ORDERS (TRENDS)
-- Analyzes daily order volume and value.
-- Uses: DATE(), GROUP BY.
-- ====================================================================
-- QUERY: Daily Orders
SELECT 
    DATE(order_date) AS order_day,
    COUNT(order_id) AS total_orders,
    SUM(total_amount) AS daily_revenue,
    AVG(total_amount) AS average_order_value
FROM orders
GROUP BY DATE(order_date)
ORDER BY order_day DESC
LIMIT 30;


-- ====================================================================
-- 5. MONTHLY ORDERS & REVENUE
-- Summarizes order volumes and gross revenues month-over-month.
-- Uses: DATE_FORMAT, GROUP BY.
-- ====================================================================
-- QUERY: Monthly Orders
SELECT 
    DATE_FORMAT(order_date, '%Y-%m') AS order_month,
    COUNT(order_id) AS total_orders,
    SUM(total_amount) AS monthly_revenue,
    AVG(total_amount) AS average_order_value
FROM orders
GROUP BY DATE_FORMAT(order_date, '%Y-%m')
ORDER BY order_month DESC;


-- ====================================================================
-- 6. ORDER FULFILLMENT RATE
-- Analyzes the ratio of fulfilled (Delivered/Shipped) vs pending/cancelled orders.
-- Uses: CASE WHEN, CTEs.
-- ====================================================================
-- QUERY: Order Fulfillment Rate
WITH OrderStatusCounts AS (
    SELECT 
        COUNT(order_id) AS total_orders,
        SUM(CASE WHEN status IN ('Shipped', 'Delivered') THEN 1 ELSE 0 END) AS fulfilled_orders,
        SUM(CASE WHEN status = 'Cancelled' THEN 1 ELSE 0 END) AS cancelled_orders,
        SUM(CASE WHEN status = 'Pending' THEN 1 ELSE 0 END) AS pending_orders
    FROM orders
)
SELECT 
    total_orders,
    fulfilled_orders,
    cancelled_orders,
    pending_orders,
    ROUND((fulfilled_orders / total_orders) * 100, 2) AS fulfillment_rate_percentage,
    ROUND((cancelled_orders / total_orders) * 100, 2) AS cancellation_rate_percentage
FROM OrderStatusCounts;


-- ====================================================================
-- 7. AVERAGE SHIPPING TIME BY CARRIER
-- Measures average transit time (Ship Date to Delivery Date) in days by carrier.
-- Uses: TIMESTAMPDIFF, GROUP BY.
-- ====================================================================
-- QUERY: Average Shipping Time
SELECT 
    carrier,
    COUNT(shipment_id) AS total_shipments,
    ROUND(AVG(TIMESTAMPDIFF(SECOND, ship_date, delivery_date) / 86400), 2) AS avg_delivery_time_days,
    ROUND(AVG(shipping_cost), 2) AS avg_shipping_cost
FROM shipments
WHERE status = 'Delivered' AND ship_date IS NOT NULL AND delivery_date IS NOT NULL
GROUP BY carrier
ORDER BY avg_delivery_time_days ASC;


-- ====================================================================
-- 8. EMPLOYEE PRODUCTIVITY (PICKING & PACKING)
-- Ranks employees by the volume of tasks they completed.
-- Uses: Window Functions (DENSE_RANK), Common Table Expressions (CTEs).
-- ====================================================================
-- QUERY: Employee Productivity
WITH PickingStats AS (
    SELECT 
        picking_employee_id AS employee_id,
        COUNT(order_id) AS orders_picked
    FROM orders
    WHERE picking_employee_id IS NOT NULL AND status NOT IN ('Cancelled')
    GROUP BY picking_employee_id
),
PackingStats AS (
    SELECT 
        packing_employee_id AS employee_id,
        COUNT(order_id) AS orders_packed
    FROM orders
    WHERE packing_employee_id IS NOT NULL AND status NOT IN ('Cancelled')
    GROUP BY packing_employee_id
)
SELECT 
    e.employee_id,
    CONCAT(e.first_name, ' ', e.last_name) AS employee_name,
    e.role,
    COALESCE(p.orders_picked, 0) AS total_orders_picked,
    COALESCE(pa.orders_packed, 0) AS total_orders_packed,
    DENSE_RANK() OVER (PARTITION BY e.role ORDER BY COALESCE(p.orders_picked, 0) + COALESCE(pa.orders_packed, 0) DESC) AS productivity_rank
FROM employees e
LEFT JOIN PickingStats p ON e.employee_id = p.employee_id
LEFT JOIN PackingStats pa ON e.employee_id = pa.employee_id
WHERE e.status = 'Active' AND e.role IN ('Picker', 'Packer')
ORDER BY e.role, productivity_rank;


-- ====================================================================
-- 9. WAREHOUSE CAPACITY UTILIZATION
-- Shows detailed bin occupancy rates across warehouse zones.
-- Uses: CASE WHEN, HAVING.
-- ====================================================================
-- QUERY: Warehouse Utilization
SELECT 
    zone,
    COUNT(location_id) AS total_bins,
    SUM(max_capacity) AS max_storage_capacity,
    SUM(current_capacity) AS current_occupied_capacity,
    ROUND((SUM(current_capacity) / SUM(max_capacity)) * 100, 2) AS utilization_rate_percentage,
    SUM(CASE WHEN current_capacity = 0 THEN 1 ELSE 0 END) AS empty_bins,
    SUM(CASE WHEN current_capacity >= max_capacity THEN 1 ELSE 0 END) AS fully_occupied_bins
FROM warehouse_locations
GROUP BY zone
ORDER BY utilization_rate_percentage DESC;


-- ====================================================================
-- 10. SUPPLIER PERFORMANCE ANALYSIS
-- Evaluates supplier based on their product cost metrics and ratings.
-- Uses: AVG, COUNT, GROUP BY.
-- ====================================================================
-- QUERY: Supplier Performance
SELECT 
    s.supplier_id,
    s.supplier_name,
    s.performance_rating,
    COUNT(p.product_id) AS total_supplied_products,
    ROUND(AVG(p.cost_price), 2) AS avg_product_cost,
    (SELECT COUNT(*) FROM transactions t WHERE t.reference_id LIKE CONCAT('RECV-SUPP-', s.supplier_id, '%') AND t.transaction_type = 'RECEIVING') AS total_shipments_received,
    (SELECT COUNT(*) FROM transactions t WHERE t.reference_id LIKE CONCAT('RECV-SUPP-', s.supplier_id, '%') AND t.transaction_type = 'QUALITY_FAIL') AS total_quality_failures
FROM suppliers s
LEFT JOIN products p ON s.supplier_id = p.supplier_id
GROUP BY s.supplier_id, s.supplier_name, s.performance_rating
ORDER BY s.performance_rating DESC;


-- ====================================================================
-- 11. RETURN PERCENTAGE BY CATEGORY
-- Identifies category return profiles.
-- Uses: CTEs, Window Functions, Percentage Calculations.
-- ====================================================================
-- QUERY: Return Percentage
WITH CategorySales AS (
    SELECT 
        p.category_id,
        SUM(oi.quantity) AS units_sold
    FROM order_items oi
    JOIN products p ON oi.product_id = p.product_id
    GROUP BY p.category_id
),
CategoryReturns AS (
    SELECT 
        p.category_id,
        SUM(r.quantity) AS units_returned
    FROM returns r
    JOIN products p ON r.product_id = p.product_id
    GROUP BY p.category_id
)
SELECT 
    c.category_name,
    COALESCE(s.units_sold, 0) AS total_units_sold,
    COALESCE(r.units_returned, 0) AS total_units_returned,
    ROUND((COALESCE(r.units_returned, 0) / COALESCE(s.units_sold, 0)) * 100, 2) AS return_rate_percentage
FROM categories c
LEFT JOIN CategorySales s ON c.category_id = s.category_id
LEFT JOIN CategoryReturns r ON c.category_id = r.category_id
ORDER BY return_rate_percentage DESC;


-- ====================================================================
-- 12. CATEGORY SALES PERFORMANCE
-- Summarizes sales details across categories.
-- Uses: joins, SUM.
-- ====================================================================
-- QUERY: Category Sales
SELECT 
    c.category_name,
    COUNT(DISTINCT oi.order_id) AS total_orders,
    SUM(oi.quantity) AS total_items_sold,
    SUM(oi.quantity * oi.unit_price) AS gross_sales_revenue,
    SUM(oi.quantity * p.cost_price) AS cost_of_goods_sold,
    SUM(oi.quantity * (oi.unit_price - p.cost_price)) AS net_profit
FROM categories c
JOIN products p ON c.category_id = p.category_id
JOIN order_items oi ON p.product_id = oi.product_id
JOIN orders o ON oi.order_id = o.order_id
WHERE o.status NOT IN ('Cancelled')
GROUP BY c.category_id, c.category_name
ORDER BY gross_sales_revenue DESC;


-- ====================================================================
-- 13. FAST MOVING PRODUCTS
-- Identifies products with high transaction velocities in the last 60 days.
-- Uses: Date filters, window function RANK().
-- ====================================================================
-- QUERY: Fast Moving Products
WITH RecentSales AS (
    SELECT 
        oi.product_id,
        SUM(oi.quantity) AS recent_units_sold
    FROM order_items oi
    JOIN orders o ON oi.order_id = o.order_id
    WHERE o.order_date >= DATE_SUB('2026-07-15 20:59:55', INTERVAL 60 DAY) AND o.status NOT IN ('Cancelled')
    GROUP BY oi.product_id
)
SELECT 
    p.sku,
    p.product_name,
    c.category_name,
    COALESCE(rs.recent_units_sold, 0) AS units_sold_60_days,
    RANK() OVER (ORDER BY COALESCE(rs.recent_units_sold, 0) DESC) AS sales_velocity_rank
FROM products p
JOIN categories c ON p.category_id = c.category_id
LEFT JOIN RecentSales rs ON p.product_id = rs.product_id
ORDER BY sales_velocity_rank ASC
LIMIT 15;


-- ====================================================================
-- 14. SLOW MOVING PRODUCTS
-- Identifies products with zero or extremely low sales in the last 90 days.
-- Uses: LEFT JOIN, DATE_SUB, WHERE NULL checks.
-- ====================================================================
-- QUERY: Slow Moving Products
SELECT 
    p.sku,
    p.product_name,
    c.category_name,
    COALESCE(SUM(i.quantity_on_hand), 0) AS current_inventory,
    COALESCE(SUM(i.quantity_on_hand * p.cost_price), 0.00) AS dead_stock_value_cost
FROM products p
JOIN categories c ON p.category_id = c.category_id
LEFT JOIN inventory i ON p.product_id = i.product_id
LEFT JOIN order_items oi ON p.product_id = oi.product_id
LEFT JOIN orders o ON oi.order_id = o.order_id AND o.order_date >= DATE_SUB('2026-07-15 20:59:55', INTERVAL 90 DAY)
WHERE o.order_id IS NULL
GROUP BY p.product_id, p.sku, p.product_name, c.category_name
ORDER BY dead_stock_value_cost DESC
LIMIT 15;


-- ====================================================================
-- 15. INVENTORY TURNOVER RATE
-- Measures how many times a category's inventory is sold and replaced.
-- Cost of Goods Sold (COGS) / Average Inventory Value
-- Uses: CTEs.
-- ====================================================================
-- QUERY: Inventory Turnover
WITH CategoryCOGS AS (
    SELECT 
        p.category_id,
        SUM(oi.quantity * p.cost_price) AS cogs
    FROM order_items oi
    JOIN products p ON oi.product_id = p.product_id
    JOIN orders o ON oi.order_id = o.order_id
    WHERE o.status NOT IN ('Cancelled')
    GROUP BY p.category_id
),
CategoryStock AS (
    SELECT 
        p.category_id,
        SUM(i.quantity_on_hand * p.cost_price) AS stock_value
    FROM inventory i
    JOIN products p ON i.product_id = p.product_id
    GROUP BY p.category_id
)
SELECT 
    c.category_name,
    COALESCE(cg.cogs, 0) AS cost_of_goods_sold,
    COALESCE(cs.stock_value, 0) AS current_stock_value,
    -- Inventory Turnover Ratio = COGS / Avg Inventory (using current stock as proxy)
    ROUND(COALESCE(cg.cogs, 0) / NULLIF(cs.stock_value, 0), 2) AS inventory_turnover_ratio
FROM categories c
LEFT JOIN CategoryCOGS cg ON c.category_id = cg.category_id
LEFT JOIN CategoryStock cs ON c.category_id = cs.category_id
ORDER BY inventory_turnover_ratio DESC;


-- ====================================================================
-- 16. CUSTOMER PURCHASE FREQUENCY
-- Segments customers based on their purchase count and lifetime value.
-- Uses: NTILE or Window functions, CASE statement.
-- ====================================================================
-- QUERY: Customer Purchase Frequency
WITH CustomerMetrics AS (
    SELECT 
        c.customer_id,
        CONCAT(c.first_name, ' ', c.last_name) AS customer_name,
        c.membership_tier,
        COUNT(o.order_id) AS total_orders,
        SUM(o.total_amount) AS lifetime_value
    FROM customers c
    LEFT JOIN orders o ON c.customer_id = o.customer_id AND o.status NOT IN ('Cancelled')
    GROUP BY c.customer_id, c.first_name, c.last_name, c.membership_tier
)
SELECT 
    customer_id,
    customer_name,
    membership_tier,
    total_orders,
    ROUND(lifetime_value, 2) AS customer_lifetime_value,
    CASE 
        WHEN total_orders >= 15 THEN 'VIP Frequent Buyer'
        WHEN total_orders >= 8 THEN 'Regular Customer'
        WHEN total_orders >= 3 THEN 'Occasional Buyer'
        ELSE 'One-Time / Inactive'
    END AS customer_segment
FROM CustomerMetrics
ORDER BY lifetime_value DESC
LIMIT 20;


-- ====================================================================
-- 17. REVENUE BY MONTH & GROWTH TRENDS
-- Computes monthly revenue along with month-over-month growth values.
-- Uses: LAG() Window Function, CTEs.
-- ====================================================================
-- QUERY: Revenue by Month
WITH MonthlyRevenue AS (
    SELECT 
        DATE_FORMAT(order_date, '%Y-%m') AS order_month,
        SUM(total_amount) AS monthly_revenue
    FROM orders
    WHERE status NOT IN ('Cancelled')
    GROUP BY DATE_FORMAT(order_date, '%Y-%m')
)
SELECT 
    order_month,
    ROUND(monthly_revenue, 2) AS revenue,
    ROUND(LAG(monthly_revenue, 1) OVER (ORDER BY order_month), 2) AS previous_month_revenue,
    ROUND(
        (monthly_revenue - LAG(monthly_revenue, 1) OVER (ORDER BY order_month)) / 
        LAG(monthly_revenue, 1) OVER (ORDER BY order_month) * 100, 2
    ) AS mom_growth_percentage
FROM MonthlyRevenue
ORDER BY order_month DESC;


-- ====================================================================
-- 18. TOP CUSTOMERS BY REVENUE
-- Ranks customers by revenue and identifies their primary purchase category.
-- Uses: CTEs, ROW_NUMBER() Window functions.
-- ====================================================================
-- QUERY: Top Customers
WITH CustomerSpend AS (
    SELECT 
        customer_id,
        SUM(total_amount) AS total_spent
    FROM orders
    WHERE status NOT IN ('Cancelled')
    GROUP BY customer_id
),
CustomerFavCategory AS (
    SELECT 
        o.customer_id,
        p.category_id,
        COUNT(oi.order_item_id) AS items_bought,
        ROW_NUMBER() OVER (PARTITION BY o.customer_id ORDER BY COUNT(oi.order_item_id) DESC) as rn
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    JOIN products p ON oi.product_id = p.product_id
    GROUP BY o.customer_id, p.category_id
)
SELECT 
    c.customer_id,
    CONCAT(c.first_name, ' ', c.last_name) AS customer_name,
    ROUND(cs.total_spent, 2) AS total_spent,
    cat.category_name AS favorite_product_category
FROM customers c
JOIN CustomerSpend cs ON c.customer_id = cs.customer_id
LEFT JOIN CustomerFavCategory fv ON c.customer_id = fv.customer_id AND fv.rn = 1
LEFT JOIN categories cat ON fv.category_id = cat.category_id
ORDER BY total_spent DESC
LIMIT 10;


-- ====================================================================
-- 19. MOST RETURNED PRODUCTS
-- Analyzes products with highest customer return counts.
-- Uses: SUM, COUNT, GROUP BY.
-- ====================================================================
-- QUERY: Most Returned Products
SELECT 
    p.sku,
    p.product_name,
    c.category_name,
    COUNT(r.return_id) AS total_return_events,
    SUM(r.quantity) AS total_units_returned,
    ROUND(SUM(r.refund_amount), 2) AS total_refunded_capital
FROM returns r
JOIN products p ON r.product_id = p.product_id
JOIN categories c ON p.category_id = c.category_id
GROUP BY p.product_id, p.sku, p.product_name, c.category_name
ORDER BY total_units_returned DESC
LIMIT 10;


-- ====================================================================
-- 20. SHIPPING DELAYS ANALYSIS
-- Identifies carriers and dates where orders were shipped/delivered late.
-- Expected Ship Time is 24 hours from Order. Expected Delivery is 3 days from Ship.
-- Uses: TIMESTAMPDIFF, CASE WHEN.
-- ====================================================================
-- QUERY: Shipping Delays
SELECT 
    s.carrier,
    COUNT(s.shipment_id) AS total_shipments,
    SUM(CASE WHEN TIMESTAMPDIFF(HOUR, o.order_date, s.ship_date) > 24 THEN 1 ELSE 0 END) AS late_dispatches_count,
    SUM(CASE WHEN TIMESTAMPDIFF(DAY, s.ship_date, s.delivery_date) > 3 THEN 1 ELSE 0 END) AS late_deliveries_count,
    ROUND((SUM(CASE WHEN TIMESTAMPDIFF(DAY, s.ship_date, s.delivery_date) > 3 THEN 1 ELSE 0 END) / COUNT(s.shipment_id)) * 100, 2) AS delay_rate_percentage
FROM shipments s
JOIN orders o ON s.order_id = o.order_id
WHERE s.status = 'Delivered' AND s.ship_date IS NOT NULL AND s.delivery_date IS NOT NULL
GROUP BY s.carrier
ORDER BY delay_rate_percentage DESC;
