-- =====================================================
-- Order Processing System - PostgreSQL Database Schema
-- Final Project - Day 7
-- =====================================================

-- Create database (run this separately if needed)
-- CREATE DATABASE order_processing;

-- Connect to the database
-- \c order_processing

-- =====================================================
-- TABLES
-- =====================================================

-- Orders table - stores main order information
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    order_id VARCHAR(100) UNIQUE NOT NULL,
    customer_id VARCHAR(100) NOT NULL,
    customer_name VARCHAR(255),
    customer_email VARCHAR(255) NOT NULL,
    customer_phone VARCHAR(50),
    total_amount DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
    item_count INTEGER NOT NULL DEFAULT 0,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    order_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    shipping_address TEXT,
    billing_address TEXT,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Order items table - stores individual line items
CREATE TABLE IF NOT EXISTS order_items (
    id SERIAL PRIMARY KEY,
    order_id VARCHAR(100) NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
    product_id VARCHAR(100) NOT NULL,
    product_name VARCHAR(255) NOT NULL,
    quantity DECIMAL(10, 2) NOT NULL,
    unit_price DECIMAL(12, 2) NOT NULL,
    line_total DECIMAL(12, 2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Order status history - tracks status changes
CREATE TABLE IF NOT EXISTS order_status_history (
    id SERIAL PRIMARY KEY,
    order_id VARCHAR(100) NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
    previous_status VARCHAR(50),
    new_status VARCHAR(50) NOT NULL,
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    changed_by VARCHAR(100) DEFAULT 'system',
    notes TEXT
);

-- =====================================================
-- INDEXES
-- =====================================================

-- Index on order_id for fast lookups
CREATE INDEX IF NOT EXISTS idx_orders_order_id ON orders(order_id);

-- Index on customer_id for customer order queries
CREATE INDEX IF NOT EXISTS idx_orders_customer_id ON orders(customer_id);

-- Index on customer_email for email lookups
CREATE INDEX IF NOT EXISTS idx_orders_customer_email ON orders(customer_email);

-- Index on status for filtering by status
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);

-- Index on order_date for date-based queries
CREATE INDEX IF NOT EXISTS idx_orders_order_date ON orders(order_date);

-- Index on order_items order_id for joining
CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id);

-- Index on order_items product_id for product queries
CREATE INDEX IF NOT EXISTS idx_order_items_product_id ON order_items(product_id);

-- Index on status history order_id
CREATE INDEX IF NOT EXISTS idx_order_status_history_order_id ON order_status_history(order_id);

-- =====================================================
-- FUNCTIONS
-- =====================================================

-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Function to track status changes
CREATE OR REPLACE FUNCTION track_order_status_change()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.status IS DISTINCT FROM NEW.status THEN
        INSERT INTO order_status_history (order_id, previous_status, new_status, notes)
        VALUES (NEW.order_id, OLD.status, NEW.status, 'Status updated');
    END IF;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- =====================================================
-- TRIGGERS
-- =====================================================

-- Trigger to auto-update updated_at on orders
DROP TRIGGER IF EXISTS update_orders_updated_at ON orders;
CREATE TRIGGER update_orders_updated_at
    BEFORE UPDATE ON orders
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger to track order status changes
DROP TRIGGER IF EXISTS track_order_status ON orders;
CREATE TRIGGER track_order_status
    AFTER UPDATE ON orders
    FOR EACH ROW
    EXECUTE FUNCTION track_order_status_change();

-- =====================================================
-- VIEWS
-- =====================================================

-- View for order summary with item details
CREATE OR REPLACE VIEW order_summary AS
SELECT
    o.order_id,
    o.customer_id,
    o.customer_name,
    o.customer_email,
    o.total_amount,
    o.item_count,
    o.status,
    o.order_date,
    o.created_at,
    json_agg(
        json_build_object(
            'productId', oi.product_id,
            'productName', oi.product_name,
            'quantity', oi.quantity,
            'unitPrice', oi.unit_price,
            'lineTotal', oi.line_total
        )
    ) AS items
FROM orders o
LEFT JOIN order_items oi ON o.order_id = oi.order_id
GROUP BY o.id, o.order_id, o.customer_id, o.customer_name, o.customer_email,
         o.total_amount, o.item_count, o.status, o.order_date, o.created_at;

-- View for daily order statistics
CREATE OR REPLACE VIEW daily_order_stats AS
SELECT
    DATE(order_date) AS order_date,
    COUNT(*) AS total_orders,
    SUM(total_amount) AS total_revenue,
    AVG(total_amount) AS avg_order_value,
    SUM(item_count) AS total_items
FROM orders
GROUP BY DATE(order_date)
ORDER BY order_date DESC;

-- View for order status distribution
CREATE OR REPLACE VIEW order_status_distribution AS
SELECT
    status,
    COUNT(*) AS order_count,
    SUM(total_amount) AS total_value,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) AS percentage
FROM orders
GROUP BY status
ORDER BY order_count DESC;

-- =====================================================
-- SAMPLE QUERIES
-- =====================================================

-- Get all orders for a customer
-- SELECT * FROM orders WHERE customer_id = 'CUST-001';

-- Get order with items
-- SELECT * FROM order_summary WHERE order_id = 'ORD-20240115-xxx';

-- Get pending orders
-- SELECT * FROM orders WHERE status = 'pending' ORDER BY order_date DESC;

-- Get orders in date range
-- SELECT * FROM orders
-- WHERE order_date BETWEEN '2024-01-01' AND '2024-01-31'
-- ORDER BY order_date DESC;

-- Get top products by quantity sold
-- SELECT product_id, product_name, SUM(quantity) as total_sold, SUM(line_total) as total_revenue
-- FROM order_items
-- GROUP BY product_id, product_name
-- ORDER BY total_sold DESC
-- LIMIT 10;

-- =====================================================
-- GRANTS (adjust as needed for your environment)
-- =====================================================

-- Grant usage on schema
-- GRANT USAGE ON SCHEMA public TO your_app_user;

-- Grant permissions on tables
-- GRANT SELECT, INSERT, UPDATE ON orders TO your_app_user;
-- GRANT SELECT, INSERT ON order_items TO your_app_user;
-- GRANT SELECT, INSERT ON order_status_history TO your_app_user;

-- Grant permissions on sequences
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO your_app_user;

-- =====================================================
-- END OF SCHEMA
-- =====================================================
