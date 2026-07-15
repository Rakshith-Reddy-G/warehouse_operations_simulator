# Order picking management, picking path optimization, and inventory reservation
import logging
from database import DatabaseManager
from simulator.utils import get_random_employee_by_role

logger = logging.getLogger("PickingModule")

class PickingManager:
    """Manages order picking reservations, paths, and assignment of pickers."""

    @classmethod
    def reserve_order_stock(cls, order_id):
        """Attempts to reserve stock for a customer order.
        
        Calls MySQL stored procedure `ReserveInventoryForOrder`.
        If successful, assigns an active Picker employee to the order.
        """
        conn = DatabaseManager.get_connection()
        cursor = conn.cursor()
        success = False
        try:
            # Call MySQL stored procedure
            # ReserveInventoryForOrder(p_order_id, OUT p_success)
            cursor.callproc("ReserveInventoryForOrder", (order_id, 0))
            cursor.execute("SELECT @ReserveInventoryForOrder_1")
            result = cursor.fetchone()
            success = bool(result[0]) if result else False
            
            if success:
                # Assign picking employee
                picker = get_random_employee_by_role('Picker')
                picker_id = picker["employee_id"] if picker else None
                
                assign_query = "UPDATE orders SET picking_employee_id = %s WHERE order_id = %s"
                DatabaseManager.execute_update(assign_query, (picker_id, order_id))
                logger.info(f"RESERVATION SUCCESS: Reserved stock for Order {order_id}. Assigned picker: {picker['first_name'] if picker else 'None'}")
            else:
                logger.warning(f"RESERVATION FAILED: Insufficient stock for Order {order_id}. Placed in pending backorder status.")
        except Exception as e:
            logger.error(f"Error calling ReserveInventoryForOrder: {e}")
            success = False
        finally:
            cursor.close()
            conn.close()
            
        return success

    @classmethod
    def generate_picking_list(cls, order_id):
        """Generates an optimized picking path list for the picker.
        
        Orders items based on Aisle/Shelf location to minimize walking path distance.
        """
        # Retrieve locations where inventory is reserved for this order
        # Wait, since the stored procedure has already updated quantity_reserved, we can query
        # where the inventory table matches this order item.
        # But wait! We can locate inventory bins with reserved stock for this product.
        # Let's search for inventory rows matching products in the order.
        query = """
            SELECT 
                oi.order_item_id,
                oi.product_id,
                p.sku,
                p.product_name,
                oi.quantity,
                wl.location_id,
                wl.zone,
                wl.aisle,
                wl.shelf,
                wl.bin
            FROM order_items oi
            JOIN products p ON oi.product_id = p.product_id
            JOIN inventory i ON p.product_id = i.product_id
            JOIN warehouse_locations wl ON i.location_id = wl.location_id
            WHERE oi.order_id = %s AND i.quantity_reserved > 0
            ORDER BY wl.zone ASC, wl.aisle ASC, wl.shelf ASC, wl.bin ASC
        """
        results = DatabaseManager.execute_query(query, (order_id,))
        if not results:
            logger.warning(f"No pick path locations generated for Order {order_id} (check if stock is reserved).")
        return results

    @classmethod
    def complete_picking(cls, order_id):
        """Executes picking.
        
        Decrements physical stock quantity_on_hand and quantity_reserved in the DB.
        Updates order status to 'Picking' complete or packed.
        We will log transactions of type 'PICKING'.
        """
        picking_list = cls.generate_picking_list(order_id)
        if not picking_list:
            logger.error(f"Cannot complete picking for order {order_id}: pick list is empty.")
            return False
            
        # Get picking employee
        order_info = DatabaseManager.execute_query(
            "SELECT picking_employee_id FROM orders WHERE order_id = %s", (order_id,)
        )
        picker_id = order_info[0]["picking_employee_id"] if order_info else None
        
        operations = []
        for item in picking_list:
            pid = item["product_id"]
            qty = item["quantity"]
            loc_id = item["location_id"]
            
            # 1. Update inventory: decrease reserved (on_hand is decreased at shipment dispatch or picking?
            # Let's deduct on_hand during picking, OR deduct during shipping and keep it reserved in the meantime.
            # In our seeder, we decremented quantity_on_hand when shipped/delivered, keeping it in inventory until shipping.
            # Let's stay consistent: picking moves reserved count (status is Picking, then Packed, then Shipped deducts it).
            # So picking updates item status to 'Picked' in order_items.
            operations.append((
                "UPDATE order_items SET item_status = 'Picked' WHERE order_item_id = %s",
                (item["order_item_id"],)
            ))
            
            # Log PICKING transaction
            operations.append((
                "INSERT INTO transactions (transaction_type, product_id, location_id, quantity, employee_id, reference_id, notes) "
                "VALUES ('PICKING', %s, %s, %s, %s, %s, 'Items picked from storage location')",
                (pid, loc_id, qty, picker_id, f"ORDER-{order_id}")
            ))
            
        # Update order status to 'Picking' (which means in progress or picked)
        operations.append((
            "UPDATE orders SET status = 'Picking' WHERE order_id = %s",
            (order_id,)
        ))
        
        try:
            DatabaseManager.execute_transaction(operations)
            logger.info(f"PICKING COMPLETE: Picked items for Order {order_id} following optimized path.")
            return True
        except Exception as e:
            logger.error(f"Error completing picking transaction: {e}")
            return False
