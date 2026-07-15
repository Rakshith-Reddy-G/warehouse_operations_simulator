# Utility methods for the simulator
import random
import logging
from database import DatabaseManager

logger = logging.getLogger("SimulatorUtils")

def get_random_employee_by_role(role):
    """Retrieves a random active employee with a specific role."""
    query = "SELECT employee_id, first_name, last_name FROM employees WHERE role = %s AND status = 'Active'"
    employees = DatabaseManager.execute_query(query, (role,))
    if not employees:
        return None
    return random.choice(employees)

def get_low_stock_products(threshold=15):
    """Gets products whose total available stock is below the threshold."""
    query = """
        SELECT p.product_id, p.sku, p.product_name, COALESCE(SUM(i.quantity_on_hand - i.quantity_reserved), 0) AS qty_available
        FROM products p
        LEFT JOIN inventory i ON p.product_id = i.product_id
        GROUP BY p.product_id, p.sku, p.product_name
        HAVING qty_available <= %s
    """
    return DatabaseManager.execute_query(query, (threshold,))

def generate_random_tracking_number():
    """Generates a pseudo-random tracking number."""
    return f"TRK{random.randint(1000000000, 9999999999)}"
