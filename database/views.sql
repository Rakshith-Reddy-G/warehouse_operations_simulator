-- Warehouse Analytical Views
USE warehouse_db;

-- 1. View for Warehouse Location Capacity and Utilization
CREATE OR REPLACE VIEW v_inventory_utilization AS
SELECT 
    zone,
    COUNT(location_id) AS total_bins,
    SUM(max_capacity) AS total_max_capacity,
    SUM(current_capacity) AS total_current_capacity,
    ROUND((SUM(current_capacity) / SUM(max_capacity)) * 100, 2) AS utilization_percentage
FROM warehouse_locations
GROUP BY zone;

-- 2. View for Low Stock Alerts
CREATE OR REPLACE VIEW v_low_stock_alerts AS
SELECT 
    p.product_id,
    p.sku,
    p.product_name,
    c.category_name,
    COALESCE(SUM(i.quantity_on_hand), 0) AS quantity_on_hand,
    COALESCE(SUM(i.quantity_reserved), 0) AS quantity_reserved,
    COALESCE(SUM(i.quantity_on_hand - i.quantity_reserved), 0) AS quantity_available,
    p.reorder_level
FROM products p
LEFT JOIN categories c ON p.category_id = c.category_id
LEFT JOIN inventory i ON p.product_id = i.product_id
GROUP BY p.product_id, p.sku, p.product_name, c.category_name, p.reorder_level
HAVING quantity_available <= p.reorder_level;

-- 3. View for Customer Order Fulfillment Lifecycle Times
CREATE OR REPLACE VIEW v_order_fulfillment_kpis AS
SELECT 
    o.order_id,
    o.status,
    o.order_date,
    s.ship_date,
    s.delivery_date,
    o.total_amount,
    TIMESTAMPDIFF(MINUTE, o.order_date, s.ship_date) AS minutes_to_ship,
    TIMESTAMPDIFF(HOUR, o.order_date, s.delivery_date) AS hours_to_deliver,
    s.carrier,
    s.shipping_cost
FROM orders o
LEFT JOIN shipments s ON o.order_id = s.order_id;

-- 4. View for Employee Performance KPI
CREATE OR REPLACE VIEW v_employee_productivity AS
SELECT 
    e.employee_id,
    CONCAT(e.first_name, ' ', e.last_name) AS employee_name,
    e.role,
    e.status,
    (SELECT COUNT(*) FROM orders o WHERE o.picking_employee_id = e.employee_id) AS orders_picked,
    (SELECT COUNT(*) FROM orders o WHERE o.packing_employee_id = e.employee_id) AS orders_packed,
    (SELECT COUNT(*) FROM transactions t WHERE t.employee_id = e.employee_id AND t.transaction_type = 'RECEIVING') AS shipments_received
FROM employees e;

-- 5. View for Category Sales and Margin
CREATE OR REPLACE VIEW v_category_sales AS
SELECT 
    c.category_id,
    c.category_name,
    COUNT(DISTINCT oi.order_id) AS total_orders,
    SUM(oi.quantity) AS total_units_sold,
    SUM(oi.quantity * oi.unit_price) AS gross_revenue,
    SUM(oi.quantity * p.cost_price) AS total_cost,
    SUM(oi.quantity * (oi.unit_price - p.cost_price)) AS net_profit,
    ROUND((SUM(oi.quantity * (oi.unit_price - p.cost_price)) / SUM(oi.quantity * oi.unit_price)) * 100, 2) AS profit_margin_percentage
FROM categories c
JOIN products p ON c.category_id = p.category_id
JOIN order_items oi ON p.product_id = oi.product_id
JOIN orders o ON oi.order_id = o.order_id
WHERE o.status NOT IN ('Cancelled')
GROUP BY c.category_id, c.category_name;

-- 6. View for Inventory Value by Location
CREATE OR REPLACE VIEW v_inventory_value_by_location AS
SELECT 
    wl.zone,
    wl.aisle,
    wl.shelf,
    wl.bin,
    p.sku,
    p.product_name,
    i.quantity_on_hand,
    i.quantity_reserved,
    (i.quantity_on_hand * p.cost_price) AS inventory_value_cost,
    (i.quantity_on_hand * p.sale_price) AS inventory_value_retail
FROM inventory i
JOIN warehouse_locations wl ON i.location_id = wl.location_id
JOIN products p ON i.product_id = p.product_id;
