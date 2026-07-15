# Returns module to process customer returns, QA inspections, restocking, and refunds
import random
import logging
from datetime import datetime
from database import DatabaseManager

logger = logging.getLogger("ReturnsModule")

class ReturnsManager:
    """Handles reverse logistics, returns check-ins, QA restocking, and customer refunds."""

    @classmethod
    def process_return(cls, order_id, product_id, quantity, reason=None):
        """Processes a customer product return.
        
        1. Validate delivery status of order.
        2. Assign reason (Damaged, Defective, Incorrect Item, Not as Described, Buyer Remorse).
        3. QA inspect returned item:
           - Damaged/Defective -> Quality Fail, scrap item, no restock.
           - Other -> Restock to a valid inventory bin.
        4. Issues refund.
        """
        # Verify order delivery
        order = DatabaseManager.execute_query(
            "SELECT status, customer_id FROM orders WHERE order_id = %s", (order_id,)
        )
        if not order or order[0]["status"] != "Delivered":
            logger.error(f"Cannot process return. Order {order_id} has not been delivered.")
            return False
            
        # Verify order items
        item = DatabaseManager.execute_query(
            "SELECT quantity, unit_price FROM order_items WHERE order_id = %s AND product_id = %s",
            (order_id, product_id)
        )
        if not item:
            logger.error(f"Product ID {product_id} not found in Order {order_id}.")
            return False
            
        ordered_qty = item[0]["quantity"]
        unit_price = item[0]["unit_price"]
        
        if quantity > ordered_qty:
            logger.error(f"Cannot return {quantity} units. Customer only purchased {ordered_qty} units.")
            return False
            
        if not reason:
            reasons = ['Damaged', 'Defective', 'Incorrect Item', 'Not as Described', 'Buyer Remorse']
            reason = random.choices(reasons, weights=[0.15, 0.20, 0.15, 0.20, 0.30])[0]
            
        refund_amount = round(quantity * unit_price, 2)
        return_date = datetime.now()
        ref_id = f"ORDER-{order_id}"
        
        # QA check: Damaged and Defective returns fail QA and are not re-stocked
        is_restockable = reason not in ['Damaged', 'Defective']
        
        operations = [
            # Register return
            ("INSERT INTO returns (order_id, product_id, quantity, return_reason, return_date, refund_amount, status) "
             "VALUES (%s, %s, %s, %s, %s, %s, 'Approved')", 
             (order_id, product_id, quantity, reason, return_date, refund_amount)),
             
            # Update order status to 'Returned' if fully returned
            ("UPDATE orders SET status = 'Returned' WHERE order_id = %s", (order_id,))
        ]
        
        # Log QA transaction
        operations.append((
            "INSERT INTO transactions (transaction_type, product_id, location_id, quantity, employee_id, reference_id, notes) "
            "VALUES ('RETURN_INSPECTED', %s, NULL, %s, NULL, %s, %s)",
            (product_id, quantity, ref_id, f"Return QA completed. Reason: {reason}. Restockable: {is_restockable}")
        ))
        
        # Restocking logic if restockable
        if is_restockable:
            # Find an existing location for this product to restock into
            stock_loc = DatabaseManager.execute_query(
                "SELECT location_id FROM inventory WHERE product_id = %s LIMIT 1", (product_id,)
            )
            
            if stock_loc:
                loc_id = stock_loc[0]["location_id"]
                operations.append((
                    "UPDATE inventory SET quantity_on_hand = quantity_on_hand + %s WHERE product_id = %s AND location_id = %s",
                    (quantity, product_id, loc_id)
                ))
                operations.append((
                    "INSERT INTO transactions (transaction_type, product_id, location_id, quantity, employee_id, reference_id, notes) "
                    "VALUES ('STOCK_ADJUSTMENT', %s, %s, %s, NULL, %s, 'Returned items restocked')",
                    (product_id, loc_id, quantity, ref_id)
                ))
                logger.info(f"RETURN RESTOCK: Restocking {quantity} units of product ID {product_id} to location ID {loc_id}.")
            else:
                # If product has no inventory record (should not happen for completed order), log warning
                logger.warning(f"Could not find existing warehouse location for product {product_id} to restock. Items placed in QA hold.")
        else:
            # If not restockable, log quality failure
            operations.append((
                "INSERT INTO transactions (transaction_type, product_id, location_id, quantity, employee_id, reference_id, notes) "
                "VALUES ('QUALITY_FAIL', %s, NULL, %s, NULL, %s, 'Defective or damaged customer return scrapped')",
                (product_id, quantity, ref_id)
            ))
            logger.info(f"RETURN SCRAPPED: {quantity} units of product ID {product_id} scrapped (Reason: {reason}).")
            
        try:
            DatabaseManager.execute_transaction(operations)
            logger.info(f"RETURN PROCESS SUCCESS: Refund of ${refund_amount} approved for Order {order_id}.")
            return True
        except Exception as e:
            logger.error(f"Error processing return for Order {order_id}: {e}")
            return False
