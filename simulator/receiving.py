# Receiving module for supplier shipment intake
import random
import logging
from database import DatabaseManager
from simulator.utils import get_random_employee_by_role
import config

logger = logging.getLogger("ReceivingModule")

class ReceivingManager:
    """Manages intake of product supplies, QA, and initial warehousing allocation."""
    
    @classmethod
    def receive_shipment(cls, supplier_id, product_id, quantity, reference_id):
        """Processes an incoming supplier shipment.
        
        1. Validate supplier.
        2. Perform QA check (based on failure probability).
        3. If QA passes: Allocate location and increase stock.
        4. If QA fails: Reject stock, log quality failure.
        """
        # Validate supplier
        supplier = DatabaseManager.execute_query("SELECT supplier_name FROM suppliers WHERE supplier_id = %s", (supplier_id,))
        if not supplier:
            logger.error(f"Supplier ID {supplier_id} not found in database. Aborting receiving.")
            return False
            
        product = DatabaseManager.execute_query("SELECT product_name FROM products WHERE product_id = %s", (product_id,))
        if not product:
            logger.error(f"Product ID {product_id} not found in database. Aborting receiving.")
            return False
            
        supplier_name = supplier[0]["supplier_name"]
        product_name = product[0]["product_name"]
        
        # Get operations staff
        receiver = get_random_employee_by_role('Receiver')
        inspector = get_random_employee_by_role('Inspector')
        
        recv_id = receiver["employee_id"] if receiver else None
        insp_id = inspector["employee_id"] if inspector else None
        
        logger.info(f"Incoming: {quantity} units of '{product_name}' from supplier '{supplier_name}' (Ref: {reference_id})")
        
        # QA check
        qa_passed = random.random() > config.QA_FAIL_PROBABILITY
        
        if not qa_passed:
            logger.warning(f"QA FAILED: Shipment {reference_id} of product '{product_name}' failed quality inspection.")
            # Record quality failure in transactions
            tx_query = """
                INSERT INTO transactions (transaction_type, product_id, location_id, quantity, employee_id, reference_id, notes) 
                VALUES ('QUALITY_FAIL', %s, NULL, %s, %s, %s, 'QA inspection failed: Items damaged or incorrect specifications')
            """
            DatabaseManager.execute_update(tx_query, (product_id, quantity, insp_id, reference_id))
            return False
            
        # Log QA pass / check-in
        tx_query = """
            INSERT INTO transactions (transaction_type, product_id, location_id, quantity, employee_id, reference_id, notes) 
            VALUES ('RECEIVING', %s, NULL, %s, %s, %s, 'QA inspection passed, ready for put-away')
        """
        DatabaseManager.execute_update(tx_query, (product_id, quantity, recv_id, reference_id))
        
        # Run put-away allocation using the stored procedure
        conn = DatabaseManager.get_connection()
        cursor = conn.cursor()
        success = False
        try:
            # Call MySQL stored procedure
            # AllocateInventoryLocation(p_product_id, p_quantity, p_employee_id, p_reference_id, OUT p_success)
            cursor.callproc("AllocateInventoryLocation", (product_id, quantity, recv_id, reference_id, 0))
            # Get out parameters
            cursor.execute("SELECT @_AllocateInventoryLocation_4")
            result = cursor.fetchone()
            success = bool(result[0]) if result else False
            
            if success:
                logger.info(f"PUT-AWAY SUCCESS: Allocated {quantity} units of product ID {product_id} into warehouse racks.")
            else:
                logger.error(f"PUT-AWAY FAILED: Warehouse at maximum capacity. Cannot store {quantity} units.")
                # Rollback or log adjustment
                adjust_query = """
                    INSERT INTO transactions (transaction_type, product_id, location_id, quantity, employee_id, reference_id, notes)
                    VALUES ('STOCK_ADJUSTMENT', %s, NULL, %s, %s, %s, 'Rejected put-away: Warehouse full capacity')
                """
                DatabaseManager.execute_update(adjust_query, (product_id, quantity, recv_id, reference_id))
        except Exception as e:
            logger.error(f"Error calling AllocateInventoryLocation procedure: {e}")
            success = False
        finally:
            cursor.close()
            conn.close()
            
        return success
