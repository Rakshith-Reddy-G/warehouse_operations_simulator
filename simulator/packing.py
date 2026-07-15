# Packing module to prepare orders for shipping
import logging
from database import DatabaseManager
from simulator.utils import get_random_employee_by_role

logger = logging.getLogger("PackingModule")

class PackingManager:
    """Manages order packaging, packer assignments, and status updates."""

    @classmethod
    def pack_order(cls, order_id):
        """Packs a picked order.
        
        1. Allocates an active Packer employee.
        2. Updates order status to 'Packed'.
        3. Updates order items status to 'Packed'.
        4. Logs transaction audits.
        """
        # Verify order is in Picking state
        order = DatabaseManager.execute_query("SELECT status FROM orders WHERE order_id = %s", (order_id,))
        if not order:
            logger.error(f"Order {order_id} not found.")
            return False
            
        if order[0]["status"] != "Picking":
            logger.error(f"Order {order_id} cannot be packed. Current status: {order[0]['status']}")
            return False
            
        packer = get_random_employee_by_role('Packer')
        packer_id = packer["employee_id"] if packer else None
        
        # Retrieve products in the order
        items = DatabaseManager.execute_query("SELECT product_id, quantity FROM order_items WHERE order_id = %s", (order_id,))
        
        operations = [
            # Update order details
            ("UPDATE orders SET status = 'Packed', packing_employee_id = %s WHERE order_id = %s", (packer_id, order_id)),
            ("UPDATE order_items SET item_status = 'Packed' WHERE order_id = %s", (order_id,))
        ]
        
        # Add audit logs
        ref_id = f"ORDER-{order_id}"
        for item in items:
            operations.append((
                "INSERT INTO transactions (transaction_type, product_id, location_id, quantity, employee_id, reference_id, notes) "
                "VALUES ('PACKING', %s, NULL, %s, %s, %s, 'Items packaged in shipping cartons')",
                (item["product_id"], item["quantity"], packer_id, ref_id)
            ))
            
        try:
            DatabaseManager.execute_transaction(operations)
            logger.info(f"PACKING COMPLETE: Packed Order {order_id}. Assigned packer: {packer['first_name'] if packer else 'None'}")
            return True
        except Exception as e:
            logger.error(f"Error packing Order {order_id}: {e}")
            return False
