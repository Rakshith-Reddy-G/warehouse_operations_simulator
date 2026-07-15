# Shipping, tracking number generation, logistics carrier assignment, and delivery simulations
import random
import logging
from datetime import datetime, timedelta
from database import DatabaseManager
from simulator.utils import generate_random_tracking_number

logger = logging.getLogger("ShippingModule")

class ShippingManager:
    """Handles dispatching, logistics carrier assignment, tracking, and customer deliveries."""

    @classmethod
    def ship_order(cls, order_id, carrier=None):
        """Dispatches a packed order to the carrier.
        
        1. Generates tracking number.
        2. Assigns carrier (FedEx, UPS, DHL, USPS).
        3. Updates order status to 'Shipped'.
        4. Creates shipment record.
        5. Deducts inventory quantity_on_hand and quantity_reserved.
        6. Logs shipping transactions.
        """
        order = DatabaseManager.execute_query("SELECT status, total_amount FROM orders WHERE order_id = %s", (order_id,))
        if not order or order[0]["status"] != "Packed":
            logger.error(f"Order {order_id} cannot be shipped. Current status: {order[0]['status'] if order else 'None'}")
            return False

        if not carrier:
            carrier = random.choice(['FedEx', 'UPS', 'DHL', 'USPS'])
            
        tracking = generate_random_tracking_number()
        ship_cost = round(random.uniform(5.00, 35.00), 2)
        ship_date = datetime.now()
        
        # Retrieve products in the order
        items = DatabaseManager.execute_query("SELECT product_id, quantity FROM order_items WHERE order_id = %s", (order_id,))
        
        # Deduct reserved and on_hand stock from inventory locations
        # We need to find where this order had reserved stock
        # For simplicity, we deduct from inventory rows matching product_id where quantity_reserved > 0
        operations = [
            # Create shipment row
            ("INSERT INTO shipments (order_id, tracking_number, carrier, shipping_cost, ship_date, status) "
             "VALUES (%s, %s, %s, %s, %s, 'In Transit')", (order_id, tracking, carrier, ship_cost, ship_date)),
             
            # Update order details
            ("UPDATE orders SET status = 'Shipped' WHERE order_id = %s", (order_id,)),
            ("UPDATE order_items SET item_status = 'Shipped' WHERE order_id = %s", (order_id,))
        ]
        
        # Process stock deductions
        ref_id = f"ORDER-{order_id}"
        for item in items:
            pid = item["product_id"]
            qty = item["quantity"]
            
            # Find the locations where reserved stock exists for this product
            inv_rows = DatabaseManager.execute_query(
                "SELECT inventory_id, location_id, quantity_reserved FROM inventory WHERE product_id = %s AND quantity_reserved > 0",
                (pid,)
            )
            
            remaining_to_deduct = qty
            for inv in inv_rows:
                if remaining_to_deduct <= 0:
                    break
                deduct_amt = min(remaining_to_deduct, inv["quantity_reserved"])
                
                # Update inventory: deduct from on_hand and reserved
                operations.append((
                    "UPDATE inventory SET quantity_on_hand = quantity_on_hand - %s, "
                    "quantity_reserved = quantity_reserved - %s "
                    "WHERE inventory_id = %s",
                    (deduct_amt, deduct_amt, inv["inventory_id"])
                ))
                
                # Log SHIPPING transaction referencing location
                operations.append((
                    "INSERT INTO transactions (transaction_type, product_id, location_id, quantity, employee_id, reference_id, notes) "
                    "VALUES ('SHIPPING', %s, %s, %s, NULL, %s, %s)",
                    (pid, inv["location_id"], deduct_amt, ref_id, f"Dispatched via {carrier}. Tracking: {tracking}")
                ))
                
                remaining_to_deduct -= deduct_amt
                
        try:
            DatabaseManager.execute_transaction(operations)
            logger.info(f"DISPATCH SUCCESS: Shipped Order {order_id} via {carrier}. Tracking: {tracking}")
            return True
        except Exception as e:
            logger.error(f"Error shipping Order {order_id}: {e}")
            return False

    @classmethod
    def simulate_delivery(cls, order_id):
        """Simulates transit and marks the order as delivered."""
        shipment = DatabaseManager.execute_query("SELECT shipment_id, status FROM shipments WHERE order_id = %s", (order_id,))
        if not shipment or shipment[0]["status"] != "In Transit":
            logger.error(f"No shipment in transit found for Order {order_id}.")
            return False
            
        delivery_date = datetime.now()
        
        # Retrieve products in order to log delivery
        items = DatabaseManager.execute_query("SELECT product_id, quantity FROM order_items WHERE order_id = %s", (order_id,))
        
        operations = [
            ("UPDATE shipments SET status = 'Delivered', delivery_date = %s WHERE order_id = %s", (delivery_date, order_id)),
            ("UPDATE orders SET status = 'Delivered' WHERE order_id = %s", (order_id,))
        ]
        
        ref_id = f"ORDER-{order_id}"
        for item in items:
            operations.append((
                "INSERT INTO transactions (transaction_type, product_id, location_id, quantity, employee_id, reference_id, notes) "
                "VALUES ('DELIVERY', %s, NULL, %s, NULL, %s, 'Successfully delivered to customer')",
                (item["product_id"], item["quantity"], ref_id)
            ))
            
        try:
            DatabaseManager.execute_transaction(operations)
            logger.info(f"DELIVERY SUCCESS: Order {order_id} has been marked delivered.")
            return True
        except Exception as e:
            logger.error(f"Error processing delivery for Order {order_id}: {e}")
            return False
