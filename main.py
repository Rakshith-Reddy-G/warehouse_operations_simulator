# Main CLI orchestrator and interactive simulation runner
import os
import sys
import random
import logging
from pathlib import Path
from datetime import datetime

from database import DatabaseManager
import config
import seed_data
from simulator import (
    ReceivingManager,
    InventoryManager,
    PickingManager,
    PackingManager,
    ShippingManager,
    ReturnsManager,
    get_low_stock_products
)
from simulator.analytics import WarehouseAnalytics

# Configure logging
logging.basicConfig(level=logging.INFO, format=config.LOG_FORMAT, handlers=[
    logging.FileHandler(config.LOG_FILE),
    logging.StreamHandler(sys.stdout)
])
logger = logging.getLogger("CLIOrchestrator")

def execute_sql_file(filepath):
    """Parses and executes a SQL script file, handling DELIMITER commands."""
    logger.info(f"Applying database script: {filepath.name}")
    if not filepath.exists():
        logger.error(f"SQL file not found: {filepath}")
        return False
        
    conn = DatabaseManager.get_connection()
    cursor = conn.cursor()
    
    with open(filepath, 'r') as f:
        content = f.read()
        
    statements = []
    current_statement = []
    delimiter = ';'
    
    lines = content.split('\n')
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith('--'):
            continue
            
        # Handle delimiter switches
        if stripped.lower().startswith('delimiter'):
            delimiter = stripped.split()[1]
            continue
            
        current_statement.append(line)
        if stripped.endswith(delimiter):
            stmt = '\n'.join(current_statement)
            if delimiter != ';':
                stmt = stmt.rstrip().rstrip(delimiter)
            statements.append(stmt)
            current_statement = []
            
    for stmt in statements:
        stmt_stripped = stmt.strip()
        if stmt_stripped:
            try:
                cursor.execute(stmt_stripped)
            except Exception as e:
                logger.error(f"Failed to execute SQL statement:\n{stmt_stripped}\nError: {e}")
                conn.rollback()
                cursor.close()
                conn.close()
                return False
                
    conn.commit()
    cursor.close()
    conn.close()
    logger.info(f"Successfully applied {filepath.name}")
    return True

def initialize_database():
    """Initializes schema, procedures, triggers, indexes, and views."""
    db_dir = config.BASE_DIR / "database"
    sql_files = [
        db_dir / "schema.sql",
        db_dir / "triggers.sql",
        db_dir / "stored_procedures.sql",
        db_dir / "indexes.sql",
        db_dir / "views.sql"
    ]
    
    logger.info("Initializing database objects...")
    for sql_file in sql_files:
        if not execute_sql_file(sql_file):
            logger.error("Database initialization aborted due to statement errors.")
            return False
            
    logger.info("Database initialized successfully with all schemas and structures.")
    return True

def run_active_simulation_cycle(cycles=1):
    """Simulates a full cycle of active warehouse operations."""
    logger.info(f"--- Starting Active Warehouse Operations Simulation ({cycles} Cycle) ---")
    
    # 1. Simulate inbound receiving
    logger.info("\n[STEP 1] Simulating Inbound Supplier Shipments...")
    products = DatabaseManager.execute_query("SELECT product_id, supplier_id FROM products LIMIT 5")
    if products:
        for _ in range(2):
            prod = random.choice(products)
            qty = random.randint(10, 50)
            ref_id = f"RECV-SIM-{random.randint(1000, 9999)}"
            ReceivingManager.receive_shipment(
                supplier_id=prod["supplier_id"],
                product_id=prod["product_id"],
                quantity=qty,
                reference_id=ref_id
            )
            
    # 2. Simulate customer order creation
    logger.info("\n[STEP 2] Simulating New Customer Order Creation...")
    customers = DatabaseManager.execute_query("SELECT customer_id FROM customers LIMIT 10")
    instock_prods = DatabaseManager.execute_query(
        "SELECT DISTINCT product_id, sale_price FROM inventory WHERE quantity_on_hand > 5 LIMIT 10"
    )
    
    if not customers or not instock_prods:
        logger.warning("No customers or instock products available. Seed database first.")
        return
        
    new_order_ids = []
    for _ in range(3):
        cust = random.choice(customers)
        cust_id = cust["customer_id"]
        
        # Create order in Pending state
        ins_order_query = "INSERT INTO orders (customer_id, status, total_amount) VALUES (%s, 'Pending', 0.00)"
        order_id = DatabaseManager.execute_update(ins_order_query, (cust_id,))
        new_order_ids.append(order_id)
        
        # Add 1-3 random items to the order
        num_items = random.randint(1, 3)
        selected_prods = random.sample(instock_prods, min(num_items, len(instock_prods)))
        
        total_order_amt = 0.0
        for prod in selected_prods:
            qty = random.randint(1, 2)
            price = float(prod["sale_price"])
            total_order_amt += (qty * price)
            
            ins_item_query = "INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES (%s, %s, %s, %s)"
            DatabaseManager.execute_update(ins_item_query, (order_id, prod["product_id"], qty, price))
            
        # Update order total
        DatabaseManager.execute_update("UPDATE orders SET total_amount = %s WHERE order_id = %s", (total_order_amt, order_id))
        logger.info(f"ORDER CREATED: Order {order_id} placed by Customer {cust_id} for ${total_order_amt:.2f}")

    # 3. Simulate picking reservation & processing
    logger.info("\n[STEP 3] Reserving Stock & Picking Orders...")
    for o_id in new_order_ids:
        # Reserve stock
        reserved = PickingManager.reserve_order_stock(o_id)
        if reserved:
            # Complete picking path
            PickingManager.complete_picking(o_id)
            
    # 4. Simulate packing
    logger.info("\n[STEP 4] Simulating Packing Stations...")
    picking_orders = DatabaseManager.execute_query("SELECT order_id FROM orders WHERE status = 'Picking'")
    for ord in picking_orders:
        PackingManager.pack_order(ord["order_id"])
        
    # 5. Simulate shipping & carrier handover
    logger.info("\n[STEP 5] Shipping Packaged Orders to Carrier...")
    packed_orders = DatabaseManager.execute_query("SELECT order_id FROM orders WHERE status = 'Packed'")
    shipped_order_ids = []
    for ord in packed_orders:
        o_id = ord["order_id"]
        if ShippingManager.ship_order(o_id):
            shipped_order_ids.append(o_id)
            
    # 6. Simulate delivery transit
    logger.info("\n[STEP 6] Simulating Customer Deliveries...")
    for o_id in shipped_order_ids:
        ShippingManager.simulate_delivery(o_id)
        
    # 7. Simulate returns
    logger.info("\n[STEP 7] Simulating Returns Intake...")
    delivered_orders = DatabaseManager.execute_query(
        "SELECT o.order_id, oi.product_id, oi.quantity FROM orders o "
        "JOIN order_items oi ON o.order_id = oi.order_id "
        "WHERE o.status = 'Delivered' LIMIT 2"
    )
    for ord in delivered_orders:
        # 30% return chance in simulation run
        if random.random() < 0.30:
            ReturnsManager.process_return(
                order_id=ord["order_id"],
                product_id=ord["product_id"],
                quantity=ord["quantity"]
            )
            
    # Check low stock alerts
    logger.info("\n[ALERTS] Checking Warehouse Inventory Thresholds...")
    low_stock = get_low_stock_products(config.LOW_STOCK_THRESHOLD)
    if low_stock:
        logger.warning(f"ALERT: {len(low_stock)} products are below safety reorder levels! Check low stock reports.")
        for item in low_stock[:3]:
            logger.warning(f" -> SKU {item['sku']} ({item['product_name']}): Available Qty = {item['qty_available']}")
    else:
        logger.info("All products have sufficient safety levels.")
        
    logger.info("\n--- Simulation Cycle Completed! ---")

def search_console():
    """Allows interactive searching of the product and order records."""
    while True:
        print("\n=== INTERACTIVE SEARCH ENGINE ===")
        print("1. Search Product Catalog (SKU, Name, Category)")
        print("2. Search Customer Orders by ID")
        print("3. Return to Main Menu")
        choice = input("Enter search option: ").strip()
        
        if choice == '1':
            term = input("Enter search keyword: ").strip()
            results = InventoryManager.search_products(term)
            if not results:
                print("No matching products found.")
            else:
                print(f"\nFound {len(results)} matching products:")
                print(f"{'SKU':<15} | {'Product Name':<35} | {'Category':<20} | {'Price':<8} | {'Stock':<5}")
                print("-" * 90)
                for p in results[:15]:
                    print(f"{p['sku']:<15} | {p['product_name'][:33]:<35} | {p['category_name']:<20} | ${p['sale_price']:<7} | {p['quantity_on_hand']:<5}")
        elif choice == '2':
            order_id = input("Enter Order ID: ").strip()
            if not order_id.isdigit():
                print("Invalid ID format.")
                continue
            
            order = DatabaseManager.execute_query(
                "SELECT o.order_id, c.first_name, c.last_name, o.status, o.total_amount, o.order_date "
                "FROM orders o JOIN customers c ON o.customer_id = c.customer_id WHERE o.order_id = %s",
                (int(order_id),)
            )
            if not order:
                print(f"Order ID {order_id} not found.")
            else:
                o = order[0]
                print(f"\nOrder Details:")
                print(f"ID: {o['order_id']} | Date: {o['order_date']}")
                print(f"Customer: {o['first_name']} {o['last_name']} | Status: {o['status']}")
                print(f"Total Amount: ${o['total_amount']:.2f}")
                
                # Retrieve items
                items = DatabaseManager.execute_query(
                    "SELECT p.sku, p.product_name, oi.quantity, oi.unit_price, oi.item_status "
                    "FROM order_items oi JOIN products p ON oi.product_id = p.product_id "
                    "WHERE oi.order_id = %s", (int(order_id),)
                )
                print(f"\nOrder Line Items:")
                for item in items:
                    print(f" -> SKU {item['sku']} | {item['product_name'][:30]:<30} | Qty: {item['quantity']} | Unit Price: ${item['unit_price']} | Status: {item['item_status']}")
        elif choice == '3':
            break
        else:
            print("Invalid input.")

def display_menu():
    print("\n" + "=" * 50)
    print("  WAREHOUSE OPERATIONS SIMULATOR & ANALYTICS")
    print("=" * 50)
    print("1. Initialize / Reset Database Schema")
    print("2. Seed Historical Data (Faker Engine)")
    print("3. Run Active Operations Simulation Cycle")
    print("4. Calculate and Export Pandas KPI Reports (CSV)")
    print("5. Search Product/Order Engine")
    print("6. Exit")
    print("=" * 50)

def main():
    while True:
        display_menu()
        choice = input("Select an option (1-6): ").strip()
        
        if choice == '1':
            confirm = input("This will clear and recreate all tables. Continue? (y/n): ").strip().lower()
            if confirm == 'y':
                initialize_database()
        elif choice == '2':
            confirm = input("Seed historical data (may take a few seconds)? (y/n): ").strip().lower()
            if confirm == 'y':
                try:
                    seed_data.main()
                except Exception as e:
                    logger.error(f"Error seeding data: {e}")
        elif choice == '3':
            run_active_simulation_cycle()
        elif choice == '4':
            try:
                success = WarehouseAnalytics.generate_all_kpi_reports()
                if success:
                    print(f"\nKPI reports exported successfully to: {config.EXPORT_DIR}")
            except Exception as e:
                logger.error(f"Analytics execution failed: {e}")
        elif choice == '5':
            search_console()
        elif choice == '6':
            print("Shutting down simulator. Goodbye!")
            sys.exit(0)
        else:
            print("Invalid selection. Please choose between 1 and 6.")

if __name__ == "__main__":
    main()
