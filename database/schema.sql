-- Warehouse Operations Database Schema
-- DBMS: MySQL 8.0+

CREATE DATABASE IF NOT EXISTS warehouse_db;
USE warehouse_db;

-- 1. Categories Table
CREATE TABLE IF NOT EXISTS categories (
    category_id INT AUTO_INCREMENT PRIMARY KEY,
    category_name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT
) ENGINE=InnoDB;

-- 2. Suppliers Table
CREATE TABLE IF NOT EXISTS suppliers (
    supplier_id INT AUTO_INCREMENT PRIMARY KEY,
    supplier_name VARCHAR(150) NOT NULL,
    contact_name VARCHAR(100),
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20),
    address TEXT,
    performance_rating DECIMAL(3,2) DEFAULT 5.00 CHECK (performance_rating >= 0.00 AND performance_rating <= 5.00)
) ENGINE=InnoDB;

-- 3. Products Table
CREATE TABLE IF NOT EXISTS products (
    product_id INT AUTO_INCREMENT PRIMARY KEY,
    sku VARCHAR(50) UNIQUE NOT NULL,
    product_name VARCHAR(150) NOT NULL,
    category_id INT,
    supplier_id INT,
    cost_price DECIMAL(10,2) NOT NULL CHECK (cost_price >= 0.00),
    sale_price DECIMAL(10,2) NOT NULL CHECK (sale_price >= 0.00),
    reorder_level INT DEFAULT 10 CHECK (reorder_level >= 0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories(category_id) ON DELETE SET NULL,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- 4. Customers Table
CREATE TABLE IF NOT EXISTS customers (
    customer_id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20),
    address TEXT,
    membership_tier ENUM('Standard', 'Silver', 'Gold', 'Platinum') DEFAULT 'Standard',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 5. Employees Table
CREATE TABLE IF NOT EXISTS employees (
    employee_id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    role ENUM('Receiver', 'Inspector', 'Picker', 'Packer', 'Manager') NOT NULL,
    status ENUM('Active', 'Inactive') DEFAULT 'Active',
    hire_date DATE NOT NULL
) ENGINE=InnoDB;

-- 6. Warehouse Locations Table
CREATE TABLE IF NOT EXISTS warehouse_locations (
    location_id INT AUTO_INCREMENT PRIMARY KEY,
    zone VARCHAR(10) NOT NULL,
    aisle INT NOT NULL,
    shelf INT NOT NULL,
    bin INT NOT NULL,
    max_capacity INT NOT NULL CHECK (max_capacity > 0),
    current_capacity INT DEFAULT 0 CHECK (current_capacity >= 0),
    CONSTRAINT uq_location UNIQUE (zone, aisle, shelf, bin)
) ENGINE=InnoDB;

-- 7. Inventory Table
CREATE TABLE IF NOT EXISTS inventory (
    inventory_id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    location_id INT NOT NULL,
    quantity_on_hand INT NOT NULL DEFAULT 0 CHECK (quantity_on_hand >= 0),
    quantity_reserved INT NOT NULL DEFAULT 0 CHECK (quantity_reserved >= 0),
    quantity_allocated INT NOT NULL DEFAULT 0 CHECK (quantity_allocated >= 0),
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT uq_product_location UNIQUE (product_id, location_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE,
    FOREIGN KEY (location_id) REFERENCES warehouse_locations(location_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 8. Orders Table
CREATE TABLE IF NOT EXISTS orders (
    order_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT,
    status ENUM('Pending', 'Picking', 'Packed', 'Shipped', 'Delivered', 'Cancelled', 'Returned') DEFAULT 'Pending',
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_amount DECIMAL(10,2) NOT NULL DEFAULT 0.00 CHECK (total_amount >= 0.00),
    picking_employee_id INT,
    packing_employee_id INT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE SET NULL,
    FOREIGN KEY (picking_employee_id) REFERENCES employees(employee_id) ON DELETE SET NULL,
    FOREIGN KEY (packing_employee_id) REFERENCES employees(employee_id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- 9. Order Items Table
CREATE TABLE IF NOT EXISTS order_items (
    order_item_id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL CHECK (quantity > 0),
    unit_price DECIMAL(10,2) NOT NULL CHECK (unit_price >= 0.00),
    item_status ENUM('Pending', 'Reserved', 'Picked', 'Packed', 'Shipped', 'Cancelled') DEFAULT 'Pending',
    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE RESTRICT
) ENGINE=InnoDB;

-- 10. Shipments Table
CREATE TABLE IF NOT EXISTS shipments (
    shipment_id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT UNIQUE NOT NULL,
    tracking_number VARCHAR(100) UNIQUE NOT NULL,
    carrier VARCHAR(50) NOT NULL,
    shipping_cost DECIMAL(10,2) NOT NULL CHECK (shipping_cost >= 0.00),
    ship_date TIMESTAMP NULL,
    delivery_date TIMESTAMP NULL,
    status ENUM('In Transit', 'Delivered', 'Failed') DEFAULT 'In Transit',
    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 11. Returns Table
CREATE TABLE IF NOT EXISTS returns (
    return_id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL CHECK (quantity > 0),
    return_reason VARCHAR(255) NOT NULL,
    return_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    refund_amount DECIMAL(10,2) NOT NULL CHECK (refund_amount >= 0.00),
    status ENUM('Pending', 'Approved', 'Rejected') DEFAULT 'Pending',
    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE RESTRICT
) ENGINE=InnoDB;

-- 12. Transactions Table (Auditing Log)
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    transaction_type ENUM('RECEIVING', 'QUALITY_FAIL', 'PUT_AWAY', 'RESERVATION', 'PICKING', 'PACKING', 'SHIPPING', 'DELIVERY', 'RETURN_INSPECTED', 'STOCK_ADJUSTMENT') NOT NULL,
    product_id INT,
    location_id INT,
    quantity INT NOT NULL,
    employee_id INT,
    reference_id VARCHAR(50),
    transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE SET NULL,
    FOREIGN KEY (location_id) REFERENCES warehouse_locations(location_id) ON DELETE SET NULL,
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id) ON DELETE SET NULL
) ENGINE=InnoDB;
