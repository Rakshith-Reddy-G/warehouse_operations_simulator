-- Warehouse Operations Database Triggers
USE warehouse_db;

DELIMITER $$

-- 1. Trigger to ensure order item price matches product sale price if not specified
DROP TRIGGER IF EXISTS before_order_item_insert$$
CREATE TRIGGER before_order_item_insert
BEFORE INSERT ON order_items
FOR EACH ROW
BEGIN
    IF NEW.unit_price IS NULL OR NEW.unit_price = 0.00 THEN
        SET NEW.unit_price = (SELECT sale_price FROM products WHERE product_id = NEW.product_id);
    END IF;
END$$

-- 2. Trigger to update location current capacity when inventory is modified
DROP TRIGGER IF EXISTS after_inventory_insert$$
CREATE TRIGGER after_inventory_insert
AFTER INSERT ON inventory
FOR EACH ROW
BEGIN
    UPDATE warehouse_locations
    SET current_capacity = current_capacity + NEW.quantity_on_hand + NEW.quantity_allocated + NEW.quantity_reserved
    WHERE location_id = NEW.location_id;
END$$

DROP TRIGGER IF EXISTS after_inventory_update$$
CREATE TRIGGER after_inventory_update
AFTER UPDATE ON inventory
FOR EACH ROW
BEGIN
    DECLARE total_old INT;
    DECLARE total_new INT;
    SET total_old = OLD.quantity_on_hand + OLD.quantity_allocated + OLD.quantity_reserved;
    SET total_new = NEW.quantity_on_hand + NEW.quantity_allocated + NEW.quantity_reserved;
    
    UPDATE warehouse_locations
    SET current_capacity = current_capacity + (total_new - total_old)
    WHERE location_id = NEW.location_id;
END$$

DROP TRIGGER IF EXISTS after_inventory_delete$$
CREATE TRIGGER after_inventory_delete
AFTER DELETE ON inventory
FOR EACH ROW
BEGIN
    UPDATE warehouse_locations
    SET current_capacity = current_capacity - (OLD.quantity_on_hand + OLD.quantity_allocated + OLD.quantity_reserved)
    WHERE location_id = OLD.location_id;
END$$

DELIMITER ;
