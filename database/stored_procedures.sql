-- Warehouse Stored Procedures
USE warehouse_db;

DELIMITER $$

-- 1. Stored Procedure to Allocate Inventory to Locations based on Max Capacity
DROP PROCEDURE IF EXISTS AllocateInventoryLocation$$
CREATE PROCEDURE AllocateInventoryLocation(
    IN p_product_id INT,
    IN p_quantity INT,
    IN p_employee_id INT,
    IN p_reference_id VARCHAR(50),
    OUT p_success BOOLEAN
)
BEGIN
    DECLARE v_remaining_qty INT DEFAULT p_quantity;
    DECLARE v_location_id INT;
    DECLARE v_capacity_left INT;
    DECLARE v_qty_to_put INT;
    DECLARE done INT DEFAULT FALSE;
    
    -- Cursor to find locations with capacity
    DECLARE loc_cursor CURSOR FOR 
        SELECT location_id, (max_capacity - current_capacity) AS capacity_left
        FROM warehouse_locations
        WHERE current_capacity < max_capacity
        ORDER BY zone ASC, aisle ASC, shelf ASC, bin ASC;
        
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;
    
    SET p_success = FALSE;
    
    START TRANSACTION;
    
    OPEN loc_cursor;
    
    read_loop: LOOP
        FETCH loc_cursor INTO v_location_id, v_capacity_left;
        IF done OR v_remaining_qty <= 0 THEN
            LEAVE read_loop;
        END IF;
        
        -- Calculate how much we can put in this location
        IF v_capacity_left >= v_remaining_qty THEN
            SET v_qty_to_put = v_remaining_qty;
        ELSE
            SET v_qty_to_put = v_capacity_left;
        END IF;
        
        -- Insert or Update Inventory
        INSERT INTO inventory (product_id, location_id, quantity_on_hand)
        VALUES (p_product_id, v_location_id, v_qty_to_put)
        ON DUPLICATE KEY UPDATE quantity_on_hand = quantity_on_hand + v_qty_to_put;
        
        -- Write to transactions table
        INSERT INTO transactions (transaction_type, product_id, location_id, quantity, employee_id, reference_id, notes)
        VALUES ('PUT_AWAY', p_product_id, v_location_id, v_qty_to_put, p_employee_id, p_reference_id, 'Auto allocated via stored procedure');
        
        SET v_remaining_qty = v_remaining_qty - v_qty_to_put;
    END LOOP;
    
    CLOSE loc_cursor;
    
    IF v_remaining_qty = 0 THEN
        COMMIT;
        SET p_success = TRUE;
    ELSE
        -- Rollback if we can't allocate all inventory due to space constraints
        ROLLBACK;
        SET p_success = FALSE;
    END IF;
END$$

-- 2. Stored Procedure to Reserve Inventory for a Customer Order
DROP PROCEDURE IF EXISTS ReserveInventoryForOrder$$
CREATE PROCEDURE ReserveInventoryForOrder(
    IN p_order_id INT,
    OUT p_success BOOLEAN
)
BEGIN
    DECLARE v_product_id INT;
    DECLARE v_quantity_needed INT;
    DECLARE v_quantity_available INT;
    DECLARE v_location_id INT;
    DECLARE v_allocated_qty INT;
    DECLARE done INT DEFAULT FALSE;
    
    -- Cursor for items in the order
    DECLARE item_cursor CURSOR FOR 
        SELECT product_id, quantity
        FROM order_items
        WHERE order_id = p_order_id;
        
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;
    
    SET p_success = TRUE;
    
    START TRANSACTION;
    
    OPEN item_cursor;
    
    item_loop: LOOP
        FETCH item_cursor INTO v_product_id, v_quantity_needed;
        IF done THEN
            LEAVE item_loop;
        END IF;
        
        -- Check total on-hand stock for the product across all locations
        SELECT SUM(quantity_on_hand - quantity_reserved) INTO v_quantity_available
        FROM inventory
        WHERE product_id = v_product_id;
        
        IF v_quantity_available IS NULL OR v_quantity_available < v_quantity_needed THEN
            -- Insufficient stock, abort reservation and rollback
            SET p_success = FALSE;
            LEAVE item_loop;
        END IF;
        
        -- Allocate/Reserve stock location by location
        BEGIN
            DECLARE v_sub_remaining INT DEFAULT v_quantity_needed;
            DECLARE v_sub_loc_id INT;
            DECLARE v_sub_qty_on_hand INT;
            DECLARE v_sub_qty_reserved INT;
            DECLARE sub_done INT DEFAULT FALSE;
            
            DECLARE loc_stock_cursor CURSOR FOR
                SELECT location_id, quantity_on_hand, quantity_reserved
                FROM inventory
                WHERE product_id = v_product_id AND (quantity_on_hand - quantity_reserved) > 0
                ORDER BY quantity_on_hand DESC;
                
            DECLARE CONTINUE HANDLER FOR NOT FOUND SET sub_done = TRUE;
            
            OPEN loc_stock_cursor;
            
            sub_loop: LOOP
                FETCH loc_stock_cursor INTO v_sub_loc_id, v_sub_qty_on_hand, v_sub_qty_reserved;
                IF sub_done OR v_sub_remaining <= 0 THEN
                    LEAVE sub_loop;
                END IF;
                
                IF (v_sub_qty_on_hand - v_sub_qty_reserved) >= v_sub_remaining THEN
                    SET v_allocated_qty = v_sub_remaining;
                ELSE
                    SET v_allocated_qty = v_sub_qty_on_hand - v_sub_qty_reserved;
                END IF;
                
                -- Update inventory to reserve the quantity
                UPDATE inventory
                SET quantity_reserved = quantity_reserved + v_allocated_qty
                WHERE inventory_id = (
                    SELECT i.inventory_id FROM (SELECT inventory_id FROM inventory WHERE product_id = v_product_id AND location_id = v_sub_loc_id) i
                );
                
                -- Write transaction
                INSERT INTO transactions (transaction_type, product_id, location_id, quantity, reference_id, notes)
                VALUES ('RESERVATION', v_product_id, v_sub_loc_id, v_allocated_qty, CONCAT('ORDER-', p_order_id), 'Inventory reserved for order');
                
                SET v_sub_remaining = v_sub_remaining - v_allocated_qty;
            END LOOP;
            
            CLOSE loc_stock_cursor;
        END;
        
    END LOOP;
    
    CLOSE item_cursor;
    
    IF p_success THEN
        -- Update order status to Picking
        UPDATE orders SET status = 'Picking' WHERE order_id = p_order_id;
        UPDATE order_items SET item_status = 'Reserved' WHERE order_id = p_order_id;
        COMMIT;
    ELSE
        ROLLBACK;
    END IF;
END$$

DELIMITER ;
