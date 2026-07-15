# Power BI Dashboard Specification Guide

This guide provides instructions on loading datasets, modeling relationships, and building KPI measures for the **Warehouse Operations Dashboard** using the exported CSV files.

---

## 1. Data Connection & Modeling
Export files from `sample_data/` and load them into Power BI:
*   `products.csv` (DimProduct)
*   `customers.csv` (DimCustomer)
*   `employees.csv` (DimEmployee)
*   `warehouse_locations.csv` (DimLocation)
*   `orders.csv` (FactOrder)
*   `transactions.csv` (FactTransaction)

### Relationships (Star Schema):
*   `DimProduct[product_id]` $1 \rightarrow *$ `FactOrder[product_id]` (via order items if denormalized, or create a bridge table)
*   `DimCustomer[customer_id]` $1 \rightarrow *$ `FactOrder[customer_id]`
*   `DimEmployee[employee_id]` $1 \rightarrow *$ `FactOrder[picking_employee_id]` (Active relationship)
*   `DimEmployee[employee_id]` $1 \rightarrow *$ `FactOrder[packing_employee_id]` (Inactive relationship)
*   `DimProduct[product_id]` $1 \rightarrow *$ `FactTransaction[product_id]`
*   `DimLocation[location_id]` $1 \rightarrow *$ `FactTransaction[location_id]`

---

## 2. Recommended Dashboard Pages & Visuals

### Page 1: Executive Summary
*   **KPI Cards**:
    *   Total Sales Revenue: `SUM(FactOrder[total_amount])`
    *   Total Orders: `DISTINCTCOUNT(FactOrder[order_id])`
    *   Fulfillment Rate: (see DAX below)
    *   Return Rate: (see DAX below)
*   **Visuals**:
    *   *Revenue Trend (Line Chart)*: Monthly Sales trend using `order_date` as Axis and `total_amount` as Value.
    *   *Sales by Product Category (Donut Chart)*: Category on legend, Revenue on values.
    *   *Top 10 Customers (Table)*: Customer Name, Total Spent, Order count.

### Page 2: Inventory & Capacity
*   **KPI Cards**:
    *   Total Units On Hand
    *   Total Inventory Valuation (Cost vs Retail)
    *   Average Location Occupancy (%)
*   **Visuals**:
    *   *Zone Utilization (Bar Chart)*: Zone on Y-Axis, average capacity usage on X-Axis.
    *   *Low Stock Alert Matrix (Table)*: SKU, Product Name, Category, Available Quantity, Reorder Level.
    *   *Storage Occupancy (Treemap)*: Zone $\rightarrow$ Aisle $\rightarrow$ Bin sized by current occupancy.

### Page 3: Shipping & Carrier Logistics
*   **KPI Cards**:
    *   Average Time-to-Ship (hours)
    *   Average Transit Time (days)
    *   Late Dispatch Rate (%)
*   **Visuals**:
    *   *Carrier Speed vs Cost (Scatter Plot)*: X-Axis = Avg Delivery Days, Y-Axis = Avg Shipping Cost, Bubble Size = Total Shipments.
    *   *Delivery Status Breakdown (Pie Chart)*: Delivered vs In-Transit vs Failed.

### Page 4: Employee Performance
*   **KPI Cards**:
    *   Active Staff count
    *   Avg Picker efficiency (orders picked per hour/day)
    *   Avg Packer efficiency
*   **Visuals**:
    *   *Productivity Leaderboard (Clustered Bar)*: Employee Name on Y-Axis, Task Count (Picked + Packed) on X-Axis, colored by Employee Role.

---

## 3. Core DAX Measures

### Order Fulfillment Rate
```dax
Fulfillment Rate = 
DIVIDE(
    CALCULATE(COUNT(FactOrder[order_id]), FactOrder[status] IN {"Shipped", "Delivered"}),
    COUNT(FactOrder[order_id]),
    0
)
```

### Customer Return Rate
```dax
Return Rate % = 
DIVIDE(
    CALCULATE(SUM(FactTransaction[quantity]), FactTransaction[transaction_type] = "RETURN_INSPECTED"),
    CALCULATE(SUM(FactTransaction[quantity]), FactTransaction[transaction_type] = "SHIPPING"),
    0
)
```

### Inventory Turn Ratio
```dax
Inventory Turnover = 
VAR CostOfGoodsSold = CALCULATE(
    SUM(FactOrder[total_amount]) * 0.60 -- Proxy: assuming average 40% gross margins
)
VAR AverageInventory = SUM(FactTransaction[quantity]) -- Average over time series
RETURN 
DIVIDE(CostOfGoodsSold, AverageInventory, 0)
```

### Average Delivery Time (Days)
```dax
Average Delivery Days = 
AVERAGEX(
    FILTER(FactShipment, NOT(ISBLANK(FactShipment[delivery_date]))),
    DATEDIFF(FactShipment[ship_date], FactShipment[delivery_date], DAY)
)
```
