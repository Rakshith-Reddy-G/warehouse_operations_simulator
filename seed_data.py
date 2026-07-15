# Database Seeder using Faker to generate realistic warehouse data
import random
import logging
from datetime import datetime, timedelta
from faker import Faker
from database import DatabaseManager
import config

# Setup logging
logging.basicConfig(level=logging.INFO, format=config.LOG_FORMAT)
logger = logging.getLogger("Seeder")

fake = Faker()
Faker.seed(42)
random.seed(42)

def clear_database():
    """Clears existing data from all tables in reverse dependency order."""
    logger.info("Clearing existing data from database tables...")
    tables = [
        "transactions", "returns", "shipments", "order_items", "orders",
        "inventory", "warehouse_locations", "employees", "customers",
        "products", "suppliers", "categories"
    ]
    
    conn = DatabaseManager.get_connection()
    cursor = conn.cursor()
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
    for table in tables:
        try:
            cursor.execute(f"TRUNCATE TABLE {table};")
            logger.info(f"Truncated table {table}")
        except Exception as e:
            logger.warning(f"Could not truncate {table}: {e}")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
    conn.commit()
    cursor.close()
    conn.close()
    logger.info("Database cleared.")

def seed_categories():
    logger.info("Seeding categories...")
    categories = [
        ("Electronics", "Gadgets, devices, and accessories"),
        ("Apparel", "Clothing, shoes, and wearable apparel"),
        ("Home & Kitchen", "Furniture, cookware, and home appliances"),
        ("Sports & Outdoors", "Fitness gear, camping equipment, and outdoor goods"),
        ("Books", "Physical books and printed media"),
        ("Beauty & Personal Care", "Cosmetics, skincare, and personal grooming"),
        ("Automotive", "Car parts, accessories, and maintenance tools"),
        ("Toys & Games", "Board games, children toys, and entertainment"),
        ("Industrial & Scientific", "Warehouse equipment, safety gear, and laboratory tools"),
        ("Office Products", "Stationery, office supplies, and writing instruments")
    ]
    
    query = "INSERT INTO categories (category_name, description) VALUES (%s, %s)"
    conn = DatabaseManager.get_connection()
    cursor = conn.cursor()
    cursor.executemany(query, categories)
    conn.commit()
    cursor.close()
    conn.close()
    logger.info(f"Seeded {len(categories)} categories.")

def seed_suppliers(count=100):
    logger.info(f"Seeding {count} suppliers...")
    suppliers = []
    for _ in range(count):
        suppliers.append((
            fake.company(),
            fake.name(),
            fake.unique.company_email(),
            fake.phone_number()[:20],
            fake.address(),
            round(random.uniform(3.0, 5.0), 2)
        ))
    
    query = """
        INSERT INTO suppliers (supplier_name, contact_name, email, phone, address, performance_rating) 
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    conn = DatabaseManager.get_connection()
    cursor = conn.cursor()
    cursor.executemany(query, suppliers)
    conn.commit()
    cursor.close()
    conn.close()
    logger.info(f"Seeded {count} suppliers.")

def seed_employees(count=20):
    logger.info(f"Seeding {count} employees...")
    employees = []
    roles = ['Receiver', 'Inspector', 'Picker', 'Packer', 'Manager']
    
    # Ensure at least 2 Managers, 4 Pickers, 4 Packers, 4 Receivers, 4 Inspectors
    predefined_roles = ['Manager', 'Manager', 'Picker', 'Picker', 'Picker', 'Picker', 
                        'Packer', 'Packer', 'Packer', 'Packer', 'Receiver', 'Receiver', 
                        'Receiver', 'Receiver', 'Inspector', 'Inspector', 'Inspector', 'Inspector']
    
    for i in range(count):
        role = predefined_roles[i] if i < len(predefined_roles) else random.choice(roles)
        hire_date = fake.date_between(start_date="-3y", end_date="-1m")
        employees.append((
            fake.first_name(),
            fake.last_name(),
            fake.unique.email(),
            role,
            "Active",
            hire_date
        ))
        
    query = """
        INSERT INTO employees (first_name, last_name, email, role, status, hire_date) 
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    conn = DatabaseManager.get_connection()
    cursor = conn.cursor()
    cursor.executemany(query, employees)
    conn.commit()
    cursor.close()
    conn.close()
    logger.info(f"Seeded {count} employees.")

def seed_customers(count=500):
    logger.info(f"Seeding {count} customers...")
    customers = []
    tiers = ['Standard', 'Silver', 'Gold', 'Platinum']
    weights = [0.70, 0.18, 0.09, 0.03] # Standard is most common
    
    for _ in range(count):
        customers.append((
            fake.first_name(),
            fake.last_name(),
            fake.unique.email(),
            fake.phone_number()[:20],
            fake.address(),
            random.choices(tiers, weights=weights)[0],
            fake.date_between(start_date="-2y", end_date="-10d")
        ))
        
    query = """
        INSERT INTO customers (first_name, last_name, email, phone, address, membership_tier, created_at) 
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    conn = DatabaseManager.get_connection()
    cursor = conn.cursor()
    cursor.executemany(query, customers)
    conn.commit()
    cursor.close()
    conn.close()
    logger.info(f"Seeded {count} customers.")

def seed_locations(count=100):
    logger.info(f"Seeding {count} warehouse locations...")
    locations = []
    zones = ['Zone A', 'Zone B', 'Zone C', 'Zone D', 'Zone E'] # A: Electronics, B: Apparel, C: Home, D: Sports, E: General
    
    # 5 zones x 4 aisles x 5 shelves x 1 bin = 100 locations
    loc_count = 0
    for zone in zones:
        for aisle in range(1, 5):
            for shelf in range(1, 6):
                for bin in range(1, 2):
                    if loc_count >= count:
                        break
                    # capacity randomizer
                    capacity = random.choice([50, 100, 200, 500])
                    locations.append((zone, aisle, shelf, bin, capacity, 0))
                    loc_count += 1
            if loc_count >= count:
                break
                
    query = """
        INSERT INTO warehouse_locations (zone, aisle, shelf, bin, max_capacity, current_capacity) 
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    conn = DatabaseManager.get_connection()
    cursor = conn.cursor()
    cursor.executemany(query, locations)
    conn.commit()
    cursor.close()
    conn.close()
    logger.info(f"Seeded {len(locations)} locations.")

def seed_products(count=1000):
    logger.info(f"Seeding {count} products...")
    
    # Retrieve categories and suppliers
    categories = DatabaseManager.execute_query("SELECT category_id FROM categories")
    suppliers = DatabaseManager.execute_query("SELECT supplier_id FROM suppliers")
    
    category_ids = [c["category_id"] for c in categories]
    supplier_ids = [s["supplier_id"] for s in suppliers]
    
    products = []
    for i in range(1, count + 1):
        sku = f"PROD-{random.choice(category_ids):02d}-{i:04d}"
        prod_name = f"{fake.word().capitalize()} {fake.word()} {random.choice(['XL', 'Pro', 'Lite', 'Classic', 'v2', 'Max'])}"
        category_id = random.choice(category_ids)
        supplier_id = random.choice(supplier_ids)
        cost_price = round(random.uniform(5.00, 250.00), 2)
        sale_price = round(cost_price * random.uniform(1.25, 2.0), 2)
        reorder_level = random.choice([10, 15, 20, 30])
        created_at = fake.date_between(start_date="-1y", end_date="-6m")
        
        products.append((
            sku, prod_name, category_id, supplier_id, cost_price, sale_price, reorder_level, created_at
        ))
        
    query = """
        INSERT INTO products (sku, product_name, category_id, supplier_id, cost_price, sale_price, reorder_level, created_at) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    conn = DatabaseManager.get_connection()
    cursor = conn.cursor()
    cursor.executemany(query, products)
    conn.commit()
    cursor.close()
    conn.close()
    logger.info(f"Seeded {count} products.")

def seed_inventory_and_receiving(target_records=5000):
    """Seed initial inventory, receiving events, and put-aways."""
    logger.info("Seeding initial inventory, receiving logs, and put-away transactions...")
    
    products = DatabaseManager.execute_query("SELECT product_id, supplier_id FROM products")
    locations = DatabaseManager.execute_query("SELECT location_id, max_capacity FROM warehouse_locations")
    receivers = DatabaseManager.execute_query("SELECT employee_id FROM employees WHERE role = 'Receiver'")
    inspectors = DatabaseManager.execute_query("SELECT employee_id FROM employees WHERE role = 'Inspector'")
    
    receiver_ids = [r["employee_id"] for r in receivers]
    inspector_ids = [ins["employee_id"] for ins in inspectors]
    
    inventory_inserts = []
    transaction_inserts = []
    
    # We will distribute products across locations
    loc_capacities = {loc["location_id"]: loc["max_capacity"] for loc in locations}
    loc_current = {loc["location_id"]: 0 for loc in locations}
    
    used_pairs = set()
    
    for _ in range(target_records):
        prod = random.choice(products)
        prod_id = prod["product_id"]
        supp_id = prod["supplier_id"]
        
        # Select location with capacity
        loc_candidates = [l_id for l_id, cap in loc_capacities.items() if loc_current[l_id] < cap]
        if not loc_candidates:
            logger.warning("All warehouse locations are at full capacity during seeding!")
            break
            
        loc_id = random.choice(loc_candidates)
        
        # Avoid duplicate (prod, loc) pairs
        if (prod_id, loc_id) in used_pairs:
            continue
        used_pairs.add((prod_id, loc_id))
        
        # Calculate quantity to place
        max_cap = loc_capacities[loc_id]
        curr_cap = loc_current[loc_id]
        qty = random.randint(10, min(50, max_cap - curr_cap))
        
        if qty <= 0:
            continue
            
        loc_current[loc_id] += qty
        
        # Create inventory row
        inventory_inserts.append((prod_id, loc_id, qty, 0, 0))
        
        # Create receiving audit log
        recv_emp = random.choice(receiver_ids)
        insp_emp = random.choice(inspector_ids)
        ref_id = f"RECV-SUPP-{supp_id}-{random.randint(1000,9999)}"
        recv_date = fake.date_time_between(start_date="-180d", end_date="-150d")
        
        # Transaction 1: Receiving at Dock
        transaction_inserts.append((
            'RECEIVING', prod_id, None, qty, recv_emp, ref_id, recv_date, 'Supplier shipment checked in at dock'
        ))
        
        # Transaction 2: Put Away in location
        transaction_inserts.append((
            'PUT_AWAY', prod_id, loc_id, qty, recv_emp, ref_id, recv_date + timedelta(hours=random.randint(1, 4)), 'Completed put-away task'
        ))
        
    # Bulk insert inventory
    query_inv = """
        INSERT INTO inventory (product_id, location_id, quantity_on_hand, quantity_reserved, quantity_allocated) 
        VALUES (%s, %s, %s, %s, %s)
    """
    conn = DatabaseManager.get_connection()
    cursor = conn.cursor()
    cursor.executemany(query_inv, inventory_inserts)
    conn.commit()
    cursor.close()
    conn.close()
    logger.info(f"Seeded {len(inventory_inserts)} inventory rows.")
    
    # Bulk insert transactions
    query_tx = """
        INSERT INTO transactions (transaction_type, product_id, location_id, quantity, employee_id, reference_id, transaction_date, notes) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    conn = DatabaseManager.get_connection()
    cursor = conn.cursor()
    
    # Split transaction inserts to avoid packet size issues
    batch_size = 5000
    for i in range(0, len(transaction_inserts), batch_size):
        cursor.executemany(query_tx, transaction_inserts[i:i+batch_size])
        conn.commit()
    cursor.close()
    conn.close()
    logger.info(f"Seeded {len(transaction_inserts)} initial receiving/put-away transactions.")

def seed_orders_and_lifecycle(order_count=5000):
    """Seed historical customer orders and run them through lifecycles."""
    logger.info(f"Seeding {order_count} historical orders and executing operations lifecycle...")
    
    customers = DatabaseManager.execute_query("SELECT customer_id FROM customers")
    products = DatabaseManager.execute_query("SELECT product_id, sale_price, cost_price FROM products")
    employees_pick = DatabaseManager.execute_query("SELECT employee_id FROM employees WHERE role = 'Picker'")
    employees_pack = DatabaseManager.execute_query("SELECT employee_id FROM employees WHERE role = 'Packer'")
    
    customer_ids = [c["customer_id"] for c in customers]
    picker_ids = [e["employee_id"] for e in employees_pick]
    packer_ids = [e["employee_id"] for e in employees_pack]
    
    prod_map = {p["product_id"]: p for p in products}
    prod_ids = list(prod_map.keys())
    
    statuses = ['Pending', 'Picking', 'Packed', 'Shipped', 'Delivered', 'Cancelled', 'Returned']
    status_weights = [0.08, 0.05, 0.05, 0.22, 0.50, 0.04, 0.06] # Real-world distribution
    
    orders = []
    order_items = []
    shipments = []
    returns = []
    transactions = []
    
    # Get current inventory on hand to deduct as we ship/deliver
    inventory_rows = DatabaseManager.execute_query("SELECT inventory_id, product_id, location_id, quantity_on_hand FROM inventory")
    # map product to list of inventory locations: {prod_id: [{inv_id, loc_id, qty}]}
    stock_map = {}
    for inv in inventory_rows:
        pid = inv["product_id"]
        if pid not in stock_map:
            stock_map[pid] = []
        stock_map[pid].append(inv)
        
    logger.info("Generating order histories in memory...")
    
    for order_id in range(1, order_count + 1):
        cust_id = random.choice(customer_ids)
        status = random.choices(statuses, weights=status_weights)[0]
        order_date = fake.date_time_between(start_date="-150d", end_date="now")
        
        picker_emp = random.choice(picker_ids) if status not in ['Pending'] else None
        packer_emp = random.choice(packer_ids) if status not in ['Pending', 'Picking'] else None
        
        # Decide how many items (1 to 4)
        num_items = random.randint(1, 4)
        selected_prods = random.sample(prod_ids, num_items)
        
        order_total = 0.0
        items_temp = []
        
        stock_available_for_order = True
        
        # Check stock availability
        for pid in selected_prods:
            qty = random.randint(1, 3)
            price = prod_map[pid]["sale_price"]
            order_total += (qty * price)
            
            # check if we have enough simulated stock
            total_stock = sum(s["quantity_on_hand"] for s in stock_map.get(pid, []))
            if total_stock < qty:
                stock_available_for_order = False
            
            items_temp.append((order_id, pid, qty, price))
            
        # If stock is insufficient, status is set to Pending (simulates stockouts)
        if not stock_available_for_order and status not in ['Cancelled']:
            status = 'Pending'
            picker_emp = None
            packer_emp = None
            
        orders.append((
            order_id, cust_id, status, order_date, order_total, picker_emp, packer_emp, order_date
        ))
        
        # Process inventory deductions and logs based on status
        ref_id = f"ORDER-{order_id}"
        
        for o_id, pid, qty, price in items_temp:
            item_status = 'Pending'
            if status == 'Picking':
                item_status = 'Reserved'
            elif status == 'Packed':
                item_status = 'Packed'
            elif status in ['Shipped', 'Delivered', 'Returned']:
                item_status = 'Shipped'
            elif status == 'Cancelled':
                item_status = 'Cancelled'
                
            order_items.append((o_id, pid, qty, price, item_status))
            
            # Simulate physical warehouse movement & transactions
            if status in ['Picking', 'Packed', 'Shipped', 'Delivered', 'Returned'] and stock_available_for_order:
                # 1. Reservation transaction
                res_date = order_date + timedelta(minutes=random.randint(15, 60))
                # Distribute reservation across physical locations in stock_map
                remaining_res = qty
                for s_item in stock_map.get(pid, []):
                    if remaining_res <= 0:
                        break
                    if s_item["quantity_on_hand"] <= 0:
                        continue
                    reserved_amt = min(remaining_res, s_item["quantity_on_hand"])
                    
                    transactions.append((
                        'RESERVATION', pid, s_item["location_id"], reserved_amt, picker_emp, ref_id, res_date, 'Reserved for picking'
                    ))
                    
                    # 2. Picking transaction
                    pick_date = res_date + timedelta(minutes=random.randint(10, 45))
                    transactions.append((
                        'PICKING', pid, s_item["location_id"], reserved_amt, picker_emp, ref_id, pick_date, 'Picked from shelf'
                    ))
                    
                    # Deduct from simulated in-memory stock for shipped states
                    if status in ['Shipped', 'Delivered', 'Returned']:
                        s_item["quantity_on_hand"] -= reserved_amt
                        
                    remaining_res -= reserved_amt
                    
                # 3. Packing transaction
                pack_date = order_date + timedelta(hours=random.randint(1, 3))
                if packer_emp:
                    transactions.append((
                        'PACKING', pid, None, qty, packer_emp, ref_id, pack_date, 'Order items packed'
                    ))
                    
                # 4. Shipping transaction
                if status in ['Shipped', 'Delivered', 'Returned']:
                    ship_date = pack_date + timedelta(hours=random.randint(2, 12))
                    transactions.append((
                        'SHIPPING', pid, None, qty, packer_emp, ref_id, ship_date, 'Dispatched to carrier'
                    ))
                    
                    # 5. Delivery transaction
                    if status in ['Delivered', 'Returned']:
                        deliv_date = ship_date + timedelta(days=random.randint(1, 5))
                        transactions.append((
                            'DELIVERY', pid, None, qty, None, ref_id, deliv_date, 'Delivered to customer'
                        ))
        
        # Create Shipment records
        if status in ['Shipped', 'Delivered', 'Returned']:
            carrier = random.choice(['FedEx', 'UPS', 'DHL', 'USPS'])
            tracking = f"TRK{random.randint(10000000, 99999999)}"
            ship_cost = round(random.uniform(5.00, 45.00), 2)
            
            ship_date = order_date + timedelta(hours=random.randint(3, 15))
            deliv_date = ship_date + timedelta(days=random.randint(1, 5)) if status in ['Delivered', 'Returned'] else None
            ship_status = 'Delivered' if status in ['Delivered', 'Returned'] else 'In Transit'
            
            shipments.append((
                order_id, tracking, carrier, ship_cost, ship_date, deliv_date, ship_status
            ))
            
        # Create Return record if Returned
        if status == 'Returned':
            # Select random item from order
            ret_item = random.choice(items_temp)
            ret_pid = ret_item[1]
            ret_qty = ret_item[2]
            ret_price = ret_item[3]
            
            reasons = ['Damaged', 'Defective', 'Incorrect Item', 'Not as Described', 'Buyer Remorse']
            reason = random.choices(reasons, weights=[0.15, 0.20, 0.15, 0.20, 0.30])[0]
            
            ret_date = order_date + timedelta(days=random.randint(6, 15))
            refund = round(ret_qty * ret_price, 2)
            
            returns.append((
                order_id, ret_pid, ret_qty, reason, ret_date, refund, 'Approved'
            ))
            
            # Log return transaction
            transactions.append((
                'RETURN_INSPECTED', ret_pid, None, ret_qty, None, ref_id, ret_date, f"Return processed. Reason: {reason}"
            ))
            
            # If restockable, put back
            if reason not in ['Damaged', 'Defective']:
                # Find product location to put back in-memory
                if ret_pid in stock_map and stock_map[ret_pid]:
                    dest_s = stock_map[ret_pid][0]
                    dest_s["quantity_on_hand"] += ret_qty
                    transactions.append((
                        'STOCK_ADJUSTMENT', ret_pid, dest_s["location_id"], ret_qty, None, ref_id, ret_date + timedelta(hours=1), 'Returned stock re-shelved'
                    ))

    # Bulk insert orders (without triggers firing on order table)
    logger.info("Executing database bulk inserts...")
    
    query_order = """
        INSERT INTO orders (order_id, customer_id, status, order_date, total_amount, picking_employee_id, packing_employee_id, updated_at) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    conn = DatabaseManager.get_connection()
    cursor = conn.cursor()
    
    for i in range(0, len(orders), batch_size):
        cursor.executemany(query_order, orders[i:i+batch_size])
        conn.commit()
    logger.info(f"Seeded {len(orders)} orders.")
    
    # Bulk insert order items
    query_item = """
        INSERT INTO order_items (order_id, product_id, quantity, unit_price, item_status) 
        VALUES (%s, %s, %s, %s, %s)
    """
    for i in range(0, len(order_items), batch_size):
        cursor.executemany(query_item, order_items[i:i+batch_size])
        conn.commit()
    logger.info(f"Seeded {len(order_items)} order items.")
    
    # Bulk insert shipments
    query_ship = """
        INSERT INTO shipments (order_id, tracking_number, carrier, shipping_cost, ship_date, delivery_date, status) 
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    for i in range(0, len(shipments), batch_size):
        cursor.executemany(query_ship, shipments[i:i+batch_size])
        conn.commit()
    logger.info(f"Seeded {len(shipments)} shipments.")
    
    # Bulk insert returns
    query_ret = """
        INSERT INTO returns (order_id, product_id, quantity, return_reason, return_date, refund_amount, status) 
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    for i in range(0, len(returns), batch_size):
        cursor.executemany(query_ret, returns[i:i+batch_size])
        conn.commit()
    logger.info(f"Seeded {len(returns)} returns.")
    
    # Bulk insert transactions
    query_tx = """
        INSERT INTO transactions (transaction_type, product_id, location_id, quantity, employee_id, reference_id, transaction_date, notes) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    for i in range(0, len(transactions), batch_size):
        cursor.executemany(query_tx, transactions[i:i+batch_size])
        conn.commit()
    logger.info(f"Seeded {len(transactions)} lifecycle transactions.")
    
    # Sync database physical inventory levels to match actual on-hand stock left
    logger.info("Synchronizing final physical inventory states into MySQL...")
    sync_queries = []
    for pid, s_list in stock_map.items():
        for s_item in s_list:
            sync_queries.append((
                "UPDATE inventory SET quantity_on_hand = %s WHERE inventory_id = %s",
                (s_item["quantity_on_hand"], s_item["inventory_id"])
            ))
            
    # Executing syncs in transaction
    DatabaseManager.execute_transaction(sync_queries)
    logger.info("Physical inventory synchronization completed.")
    
    cursor.close()
    conn.close()

def main():
    logger.info("Starting Warehouse Database Seeder...")
    clear_database()
    seed_categories()
    seed_suppliers()
    seed_employees()
    seed_customers()
    seed_locations()
    seed_products()
    seed_inventory_and_receiving()
    seed_orders_and_lifecycle()
    logger.info("Seeding completed successfully!")

if __name__ == "__main__":
    main()
