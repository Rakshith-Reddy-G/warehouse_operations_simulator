-- Warehouse Database Performance Indexes
USE warehouse_db;

-- 1. Index for Order Date and Status (very common search criteria for warehouse tracking)
CREATE INDEX idx_orders_status_date ON orders(status, order_date);

-- 2. Index for Inventory level queries (alert thresholds, stock calculations)
CREATE INDEX idx_inventory_qty_hand ON inventory(quantity_on_hand);

-- 3. Index for Order Items lookups
CREATE INDEX idx_order_items_product ON order_items(product_id);

-- 4. Index for Shipments status and carrier tracking
CREATE INDEX idx_shipments_status_carrier ON shipments(status, carrier);
CREATE INDEX idx_shipments_dates ON shipments(ship_date, delivery_date);

-- 5. Index for auditing ledger (transactions)
CREATE INDEX idx_transactions_type_date ON transactions(transaction_type, transaction_date);
CREATE INDEX idx_transactions_ref_id ON transactions(reference_id);

-- 6. Index for Returns
CREATE INDEX idx_returns_date ON returns(return_date);
CREATE INDEX idx_returns_product ON returns(product_id);

-- 7. Index for Employees
CREATE INDEX idx_employees_role_status ON employees(role, status);
