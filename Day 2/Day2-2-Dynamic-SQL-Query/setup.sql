-- Setup script for Day 2-2 Demo
-- Run this in your PostgreSQL database

-- Create products table
CREATE TABLE IF NOT EXISTS products (
    product_id SERIAL PRIMARY KEY,
    product_name VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    price NUMERIC(10, 2) NOT NULL,
    stock_quantity INTEGER NOT NULL DEFAULT 0,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_products_price ON products(price);
CREATE INDEX IF NOT EXISTS idx_products_stock ON products(stock_quantity);

-- Insert sample data
INSERT INTO products (product_name, category, price, stock_quantity, description) VALUES
('Laptop Pro 15', 'Electronics', 1299.99, 25, 'High-performance laptop with 16GB RAM'),
('Wireless Mouse', 'Electronics', 29.99, 150, 'Ergonomic wireless mouse'),
('USB-C Cable', 'Electronics', 12.99, 500, '6ft USB-C charging cable'),
('Mechanical Keyboard', 'Electronics', 89.99, 75, 'RGB mechanical gaming keyboard'),
('27" Monitor', 'Electronics', 349.99, 40, '4K UHD monitor'),
('Webcam HD', 'Electronics', 79.99, 100, '1080p HD webcam'),
('Cotton T-Shirt', 'Clothing', 19.99, 200, 'Comfortable cotton t-shirt'),
('Jeans', 'Clothing', 49.99, 75, 'Classic fit jeans'),
('Hoodie', 'Clothing', 39.99, 120, 'Warm pullover hoodie'),
('Running Shoes', 'Footwear', 89.99, 50, 'Lightweight running shoes'),
('Sneakers', 'Footwear', 69.99, 80, 'Casual sneakers'),
('Desk Lamp', 'Home', 39.99, 100, 'LED desk lamp with adjustable brightness'),
('Office Chair', 'Home', 249.99, 30, 'Ergonomic office chair'),
('Bookshelf', 'Home', 149.99, 20, '5-tier wooden bookshelf'),
('Water Bottle', 'Sports', 24.99, 300, 'Insulated stainless steel water bottle'),
('Yoga Mat', 'Sports', 34.99, 150, 'Non-slip yoga mat');

-- Verify data
SELECT category, COUNT(*) as product_count, AVG(price) as avg_price
FROM products
GROUP BY category
ORDER BY category;

-- Test query examples
-- Example 1: Get Electronics under $500
SELECT product_name, price, stock_quantity
FROM products
WHERE category = 'Electronics'
  AND price <= 500
  AND stock_quantity >= 10;

-- Example 2: Get all Clothing items
SELECT product_name, price, stock_quantity
FROM products
WHERE category = 'Clothing';
