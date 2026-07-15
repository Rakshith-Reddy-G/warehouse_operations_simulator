# Warehouse Operations Simulator & SQL Reporting

A production-quality Python and MySQL simulation system that models the complete lifecycle of a high-throughput distribution center (comparable to Amazon, Flipkart, or Walmart logistics hubs). It generates transaction-consistent historical records, manages physical rack space, applies stored procedures and triggers for inventory integrity, runs Pandas-based business analytics, and outputs dashboard-ready analytical CSVs for Power BI.

---

## 1. Project Features
*   **Decoupled Architecture**: Strictly follows **SOLID** principles, dividing operational business concerns from database layers and domain entities.
*   **Operations Lifecycles**: Models Supplier Receiving, Quality Assurance (QA) Inspection, Storage Slot Location Allocation, Customer Order Creation, optimized Path Picking, Packing, Shipping Carriers Handover, Transit Delivery, and Reverse Returns.
*   **Procedural Integrity**: Offloads complex computations (e.g. stock allocation, reservation blocks) to database-level MySQL stored procedures and automated capacity management triggers.
*   **Faker Seeding Engine**: Generates over 50,000 transaction-consistent events over a 6-month historical timeline.
*   **Business Intelligence Export**: Implements Pandas KPIs (AOV, inventory turnover, delivery time delays, returns metrics) and exports structured dimension/fact sheets.

---

## 2. Technologies Used
*   **Backend & Logic**: Python 3.12+, Object-Oriented Programming (OOP)
*   **Database**: MySQL Server 8.0+, `mysql-connector-python` (with pool management)
*   **Data Analysis**: Pandas, NumPy
*   **Data Generation**: Faker
*   **Configuration**: Dotenv (`python-dotenv`), Logging
*   **Visualization**: Power BI Desktop (for dashboard modeling)

---

## 3. Installation Guide

### Prerequisites
1.  Python 3.12 or higher installed.
2.  MySQL Server installed and running locally.
3.  Git (optional).

### Step 1: Clone and Set Up Workspace
Ensure the codebase files are located in your workspace:
```bash
cd warehouse_operations_simulator/
```

### Step 2: Configure Environment Variables
Create a `.env` file in the root directory:
```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=warehouse_db

# Simulation settings
SIMULATION_SPEED_SECONDS=1.0
LOW_STOCK_THRESHOLD=15
QA_FAIL_PROBABILITY=0.05
RETURN_PROBABILITY=0.10
```

### Step 3: Install Dependencies
Install requirements via `pip`:
```bash
pip install -r requirements.txt
```

---

## 4. Usage Guidelines
Run the CLI orchestrator to control the simulator:
```bash
python main.py
```

### CLI Menu Options:
1.  **Initialize / Reset Database Schema**: Recreates all base tables, performance indexes, auditing triggers, views, and stored procedures in your MySQL server.
2.  **Seed Historical Data (Faker Engine)**: Wipes old logs and seeds master customer/supplier catalogs and 5,000 orders, automatically executing 50,000 ledger transactions.
3.  **Run Active Operations Simulation Cycle**: Executes a live operation cycle (receiving inbound shipments, processing new orders, picking, packing, shipping, and simulating customer deliveries).
4.  **Calculate and Export Pandas KPI Reports (CSV)**: Computes business-critical analytics and writes CSVs into `sample_data/`.
5.  **Search Product/Order Engine**: Interactively query SKU catalogs or trace specific order lifecycle event timelines.

---

## 5. Directory Mapping
*   `main.py`: Main CLI execution loop.
*   `config.py`: Configuration and environment parser.
*   `database.py`: Thread-safe database pooling connector.
*   `seed_data.py`: Multi-threaded historical Faker seeder.
*   `database/`: Base SQL schemas, views, stored procedures, indexes, and triggers.
*   `simulator/`: Modules for receiving, inventory, picking, packing, shipping, returns, and Pandas analytics.
*   `models/`: Domain OOP data models.
*   `reports/`: Pre-compiled SQL business reporting queries.
*   `dashboard/`: Power BI guide and visualization specifications.
*   `docs/`: Visual workflow, architecture, and ER system diagrams.
*   `requirements.txt`: Python package requirements list.

---

## 6. Future Enhancements
1.  **Multi-Warehouse Simulation**: Add multiple fulfillment centers with inter-warehouse stock transfer rules.
2.  **LPN (License Plate Number) Tracking**: Track item pallets rather than individual product counts for large-pallet shipping logistics.
3.  **Worker Scheduling**: Dynamic shifts for Pickers/Packers, adding employee hourly wages to calculate operational labor costs.
4.  **Web Interface**: Re-platform CLI console to a web dashboard using Next.js/FastAPI to monitor operations visually.
