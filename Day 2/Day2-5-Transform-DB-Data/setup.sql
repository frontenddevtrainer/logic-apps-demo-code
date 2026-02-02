-- Setup script for Day 2-5 Demo: Transform DB Data
-- Run this in your PostgreSQL database

-- Create customers table
CREATE TABLE IF NOT EXISTS customers (
    customer_id VARCHAR(50) PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    phone VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create orders table
CREATE TABLE IF NOT EXISTS orders (
    order_id SERIAL PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL REFERENCES customers(customer_id),
    order_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    total_amount NUMERIC(10, 2) NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('PENDING', 'PROCESSING', 'COMPLETED', 'CANCELLED')),
    shipping_address TEXT,
    payment_method VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create products table (if not exists from previous demos)
CREATE TABLE IF NOT EXISTS products (
    product_id SERIAL PRIMARY KEY,
    product_name VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    price NUMERIC(10, 2) NOT NULL,
    stock_quantity INTEGER NOT NULL DEFAULT 0,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create order_items table
CREATE TABLE IF NOT EXISTS order_items (
    order_item_id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES products(product_id),
    quantity INTEGER NOT NULL,
    unit_price NUMERIC(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_customers_email ON customers(email);
CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items(order_id);

-- Insert sample customers
INSERT INTO customers (customer_id, full_name, email, phone, is_active) VALUES
('CUST-0001', 'John Doe', 'john.doe@example.com', '+1-555-123-4567', TRUE),
('CUST-0002', 'Jane Smith', 'jane.smith@example.com', '+1-555-234-5678', TRUE),
('CUST-0003', 'Bob Johnson', 'bob.johnson@example.com', '+1-555-345-6789', TRUE),
('CUST-0004', 'Alice Williams', 'alice.williams@example.com', NULL, TRUE),
('CUST-0005', 'Charlie Brown', 'charlie.brown@example.com', '+1-555-456-7890', FALSE)
ON CONFLICT (customer_id) DO NOTHING;

-- Insert sample products (if needed)
INSERT INTO products (product_name, category, price, stock_quantity, description) VALUES
('Laptop Pro 15', 'Electronics', 1299.99, 25, 'High-performance laptop'),
('Wireless Mouse', 'Electronics', 29.99, 150, 'Ergonomic wireless mouse'),
('USB-C Cable', 'Electronics', 12.99, 500, '6ft USB-C charging cable'),
('Office Chair', 'Home', 249.99, 30, 'Ergonomic office chair'),
('Desk Lamp', 'Home', 39.99, 100, 'LED desk lamp')
ON CONFLICT DO NOTHING;

-- Insert sample orders
INSERT INTO orders (customer_id, order_date, total_amount, status, shipping_address, payment_method) VALUES
('CUST-0001', '2024-12-15 10:30:00', 1329.98, 'COMPLETED', '123 Main St, Springfield, IL 62701', 'Credit Card'),
('CUST-0001', '2024-12-10 14:20:00', 42.98, 'COMPLETED', '123 Main St, Springfield, IL 62701', 'PayPal'),
('CUST-0002', '2024-12-14 09:15:00', 249.99, 'PROCESSING', '456 Oak Ave, Portland, OR 97201', 'Credit Card'),
('CUST-0003', '2024-12-13 16:45:00', 12.99, 'COMPLETED', '789 Pine Rd, Austin, TX 78701', 'Debit Card'),
('CUST-0001', '2024-12-12 11:30:00', 39.99, 'PENDING', '123 Main St, Springfield, IL 62701', 'Credit Card'),
('CUST-0002', '2024-12-11 13:00:00', 1299.99, 'CANCELLED', '456 Oak Ave, Portland, OR 97201', 'Credit Card'),
('CUST-0004', '2024-12-09 10:00:00', 29.99, 'COMPLETED', '321 Elm St, Seattle, WA 98101', 'PayPal');

-- Insert sample order items
-- Order 1: Laptop + Mouse
INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES
(1, 1, 1, 1299.99),
(1, 2, 1, 29.99);

-- Order 2: USB-C Cables
INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES
(2, 3, 2, 12.99);

-- Order 3: Office Chair
INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES
(3, 4, 1, 249.99);

-- Order 4: USB-C Cable
INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES
(4, 3, 1, 12.99);

-- Order 5: Desk Lamp
INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES
(5, 5, 1, 39.99);

-- Order 6: Laptop (cancelled)
INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES
(6, 1, 1, 1299.99);

-- Order 7: Mouse
INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES
(7, 2, 1, 29.99);

-- Verify data
SELECT 'Customers' as table_name, COUNT(*) as count FROM customers
UNION ALL
SELECT 'Orders', COUNT(*) FROM orders
UNION ALL
SELECT 'Products', COUNT(*) FROM products
UNION ALL
SELECT 'Order Items', COUNT(*) FROM order_items;

-- Test customer with aggregates query
SELECT
    c.customer_id,
    c.full_name,
    c.email,
    c.phone,
    c.created_at,
    c.is_active,
    COUNT(o.order_id) as order_count,
    COALESCE(SUM(o.total_amount), 0) as total_spent
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
WHERE c.customer_id = 'CUST-0001'
GROUP BY c.customer_id, c.full_name, c.email, c.phone, c.created_at, c.is_active;

-- Test orders with customer info query
SELECT
    o.order_id,
    o.order_date,
    o.total_amount,
    o.status,
    o.shipping_address,
    o.payment_method,
    c.full_name as customer_name,
    c.email as customer_email,
    COUNT(oi.order_item_id) as items_count
FROM orders o
INNER JOIN customers c ON o.customer_id = c.customer_id
LEFT JOIN order_items oi ON o.order_id = oi.order_id
WHERE o.customer_id = 'CUST-0001'
GROUP BY o.order_id, o.order_date, o.total_amount, o.status,
         o.shipping_address, o.payment_method, c.full_name, c.email
ORDER BY o.order_date DESC;
