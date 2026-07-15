# Inventory management, stock movements, and valuation calculations
import logging
from database import DatabaseManager

logger = logging.getLogger("InventoryModule")

class InventoryManager:
    """Manages stock level checks, internal warehouse movements, valuation, and search operations."""

    @classmethod
    def get_product_stock_summary(cls, product_id):
        """Retrieves total stock on-hand, reserved, and available for a product."""
        query = """
            SELECT 
                COALESCE(SUM(quantity_on_hand), 0) AS total_on_hand,
                COALESCE(SUM(quantity_reserved), 0) AS total_reserved,
                COALESCE(SUM(quantity_on_hand - quantity_reserved), 0) AS total_available
            FROM inventory
            WHERE product_id = %s
        """
        results = DatabaseManager.execute_query(query, (product_id,))
        return results[0] if results else {"total_on_hand": 0, "total_reserved": 0, "total_available": 0}

    @classmethod
    def move_stock(cls, product_id, from_location_id, to_location_id, quantity, employee_id=None):
        """Moves physical stock between locations. Maintains integrity constraints and capacity rules."""
        # 1. Verify from_location stock availability
        from_stock = DatabaseManager.execute_query(
            "SELECT quantity_on_hand, quantity_reserved FROM inventory WHERE product_id = %s AND location_id = %s",
            (product_id, from_location_id)
        )
        if not from_stock:
            logger.error(f"Stock not found at source location {from_location_id} for product {product_id}.")
            return False
            
        avail_qty = from_stock[0]["quantity_on_hand"] - from_stock[0]["quantity_reserved"]
        if avail_qty < quantity:
            logger.error(f"Insufficient unreserved stock at source location: {avail_qty} available, {quantity} requested.")
            return False

        # 2. Check destination location capacity
        dest_loc = DatabaseManager.execute_query(
            "SELECT max_capacity, current_capacity FROM warehouse_locations WHERE location_id = %s",
            (to_location_id,)
        )
        if not dest_loc:
            logger.error(f"Destination location {to_location_id} does not exist.")
            return False

        capacity_left = dest_loc[0]["max_capacity"] - dest_loc[0]["current_capacity"]
        if capacity_left < quantity:
            logger.error(f"Insufficient capacity at destination location: {capacity_left} units left, {quantity} requested.")
            return False

        # 3. Execute database updates as a single transaction
        operations = [
            # Deduct from source inventory
            ("UPDATE inventory SET quantity_on_hand = quantity_on_hand - %s WHERE product_id = %s AND location_id = %s", 
             (quantity, product_id, from_location_id)),
             
            # Insert or update destination inventory
            ("INSERT INTO inventory (product_id, location_id, quantity_on_hand) VALUES (%s, %s, %s) "
             "ON DUPLICATE KEY UPDATE quantity_on_hand = quantity_on_hand + %s", 
             (product_id, to_location_id, quantity, quantity)),
             
            # Record move transaction
            ("INSERT INTO transactions (transaction_type, product_id, location_id, quantity, employee_id, reference_id, notes) "
             "VALUES ('STOCK_ADJUSTMENT', %s, %s, %s, %s, 'INTERNAL_MOVE', %s)",
             (product_id, to_location_id, quantity, employee_id, f"Moved from location {from_location_id}"))
        ]
        
        try:
            DatabaseManager.execute_transaction(operations)
            logger.info(f"MOVE SUCCESS: Moved {quantity} units of product ID {product_id} from location {from_location_id} to {to_location_id}.")
            return True
        except Exception as e:
            logger.error(f"Failed to execute stock move: {e}")
            return False

    @classmethod
    def get_inventory_valuation(cls):
        """Computes total cost and retail value of stock currently on hand."""
        query = """
            SELECT 
                SUM(i.quantity_on_hand * p.cost_price) AS total_inventory_cost,
                SUM(i.quantity_on_hand * p.sale_price) AS total_inventory_retail,
                SUM(i.quantity_on_hand * (p.sale_price - p.cost_price)) AS potential_profit
            FROM inventory i
            JOIN products p ON i.product_id = p.product_id
        """
        results = DatabaseManager.execute_query(query)
        if results and results[0]["total_inventory_cost"] is not None:
            return results[0]
        return {"total_inventory_cost": 0.00, "total_inventory_retail": 0.00, "potential_profit": 0.00}

    @classmethod
    def search_products(cls, search_term):
        """Search products catalog by SKU, name, or category name."""
        query = """
            SELECT p.product_id, p.sku, p.product_name, c.category_name, p.sale_price, 
                   COALESCE(SUM(i.quantity_on_hand), 0) AS quantity_on_hand
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.category_id
            LEFT JOIN inventory i ON p.product_id = i.product_id
            WHERE p.product_name LIKE %s OR p.sku LIKE %s OR c.category_name LIKE %s
            GROUP BY p.product_id, p.sku, p.product_name, c.category_name, p.sale_price
        """
        like_term = f"%{search_term}%"
        return DatabaseManager.execute_query(query, (like_term, like_term, like_term))
