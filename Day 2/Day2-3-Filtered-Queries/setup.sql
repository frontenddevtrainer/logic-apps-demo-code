-- Setup script for Day 2-3 Demo
-- Run this in your PostgreSQL database

-- Create orders table
CREATE TABLE IF NOT EXISTS orders (
    order_id SERIAL PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL,
    order_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    total_amount NUMERIC(10, 2) NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('PENDING', 'PROCESSING', 'COMPLETED', 'CANCELLED')),
    shipping_address TEXT,
    payment_method VARCHAR(50),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_date ON orders(order_date DESC);
CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_composite ON orders(status, order_date DESC);

-- Function to generate random customer ID
CREATE OR REPLACE FUNCTION random_customer_id() RETURNS VARCHAR AS $$
BEGIN
    RETURN 'CUST-' || LPAD((FLOOR(RANDOM() * 1000) + 1)::TEXT, 4, '0');
END;
$$ LANGUAGE plpgsql;

-- Insert sample data (300+ orders for testing pagination)
INSERT INTO orders (customer_id, order_date, total_amount, status, shipping_address, payment_method)
SELECT
    random_customer_id(),
    CURRENT_DATE - (random() * 180)::int * INTERVAL '1 day',
    ROUND((RANDOM() * 900 + 100)::NUMERIC, 2),
    CASE
        WHEN RANDOM() < 0.6 THEN 'COMPLETED'
        WHEN RANDOM() < 0.8 THEN 'PROCESSING'
        WHEN RANDOM() < 0.95 THEN 'PENDING'
        ELSE 'CANCELLED'
    END,
    (ARRAY['123 Main St, City, State 12345',
           '456 Oak Ave, Town, State 67890',
           '789 Pine Rd, Village, State 11111',
           '321 Elm St, City, State 22222',
           '654 Maple Dr, Town, State 33333'])[FLOOR(RANDOM() * 5 + 1)],
    (ARRAY['Credit Card', 'PayPal', 'Debit Card', 'Bank Transfer'])[FLOOR(RANDOM() * 4 + 1)]
FROM generate_series(1, 300);

-- Insert some specific test data
INSERT INTO orders (customer_id, order_date, total_amount, status, shipping_address, payment_method) VALUES
('CUST-0001', '2024-12-15 10:30:00', 299.99, 'COMPLETED', '123 Main St, City, State 12345', 'Credit Card'),
('CUST-0002', '2024-12-14 14:20:00', 149.50, 'COMPLETED', '456 Oak Ave, Town, State 67890', 'PayPal'),
('CUST-0003', '2024-12-13 09:15:00', 499.99, 'PROCESSING', '789 Pine Rd, Village, State 11111', 'Credit Card'),
('CUST-0001', '2024-12-12 16:45:00', 89.99, 'PENDING', '123 Main St, City, State 12345', 'Debit Card'),
('CUST-0004', '2024-12-11 11:30:00', 199.99, 'CANCELLED', '321 Elm St, City, State 22222', 'Credit Card');

-- Verify data distribution
SELECT
    status,
    COUNT(*) as order_count,
    ROUND(AVG(total_amount), 2) as avg_amount,
    ROUND(SUM(total_amount), 2) as total_revenue
FROM orders
GROUP BY status
ORDER BY order_count DESC;

-- Check date range
SELECT
    MIN(order_date) as earliest_order,
    MAX(order_date) as latest_order,
    COUNT(*) as total_orders
FROM orders;

-- Test pagination queries
-- Example 1: Get first 100 completed orders
SELECT
    order_id,
    customer_id,
    order_date,
    total_amount,
    status
FROM orders
WHERE status = 'COMPLETED'
  AND order_date >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY order_date DESC
LIMIT 100 OFFSET 0;

-- Example 2: Get total count for pagination
SELECT COUNT(*) as total_count
FROM orders
WHERE status = 'COMPLETED'
  AND order_date >= CURRENT_DATE - INTERVAL '30 days';

-- Example 3: Test OFFSET for page 2
SELECT
    order_id,
    customer_id,
    order_date,
    total_amount,
    status
FROM orders
WHERE status = 'COMPLETED'
ORDER BY order_date DESC
LIMIT 100 OFFSET 100;

-- Performance analysis
EXPLAIN ANALYZE
SELECT
    order_id,
    customer_id,
    order_date,
    total_amount,
    status
FROM orders
WHERE status = 'COMPLETED'
  AND order_date >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY order_date DESC
LIMIT 100 OFFSET 0;
