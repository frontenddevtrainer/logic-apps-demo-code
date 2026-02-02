import azure.functions as func
import logging
import json
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List
from models import (
    CustomerDTO,
    OrderDTO,
    ProductDTO,
    transform_customer_from_db,
    transform_order_from_db,
    transform_product_from_db
)

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

def get_db_connection():
    """Create and return a database connection."""
    try:
        conn = psycopg2.connect(
            host=os.environ.get('POSTGRES_HOST'),
            database=os.environ.get('POSTGRES_DATABASE'),
            user=os.environ.get('POSTGRES_USER'),
            password=os.environ.get('POSTGRES_PASSWORD'),
            port=os.environ.get('POSTGRES_PORT', '5432'),
            sslmode='require'
        )
        return conn
    except Exception as e:
        logging.error(f"Database connection failed: {str(e)}")
        raise

@app.route(route="customer/{customer_id}", methods=["GET"])
def get_customer(req: func.HttpRequest) -> func.HttpResponse:
    """
    Get customer information with transformed DTO

    Returns cleaned customer data with:
    - Hidden sensitive information
    - Calculated aggregates (total orders, total spent)
    - Formatted dates

    Example: GET /api/customer/CUST-0001
    """
    logging.info('Processing get_customer request')

    try:
        customer_id = req.route_params.get('customer_id')

        if not customer_id:
            return func.HttpResponse(
                json.dumps({"error": "customer_id is required"}),
                status_code=400,
                mimetype="application/json"
            )

        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Query with aggregated data
        query = """
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
            WHERE c.customer_id = %s
            GROUP BY c.customer_id, c.full_name, c.email, c.phone, c.created_at, c.is_active
        """

        cursor.execute(query, (customer_id,))
        db_row = cursor.fetchone()

        cursor.close()
        conn.close()

        if not db_row:
            return func.HttpResponse(
                json.dumps({"error": "Customer not found"}),
                status_code=404,
                mimetype="application/json"
            )

        # Transform DB row into DTO
        customer_dto = transform_customer_from_db(db_row)

        return func.HttpResponse(
            json.dumps({
                "status": "success",
                "data": customer_dto.model_dump()
            }, default=str),
            status_code=200,
            mimetype="application/json"
        )

    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return func.HttpResponse(
            json.dumps({"status": "error", "message": str(e)}),
            status_code=500,
            mimetype="application/json"
        )

@app.route(route="customer/{customer_id}/orders", methods=["GET"])
def get_customer_orders(req: func.HttpRequest) -> func.HttpResponse:
    """
    Get customer orders with transformation

    Returns:
    - Formatted order data
    - Parsed shipping addresses
    - Masked payment information
    - Human-readable order numbers

    Example: GET /api/customer/CUST-0001/orders
    """
    logging.info('Processing get_customer_orders request')

    try:
        customer_id = req.route_params.get('customer_id')

        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Query orders with customer info
        query = """
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
            WHERE o.customer_id = %s
            GROUP BY o.order_id, o.order_date, o.total_amount, o.status,
                     o.shipping_address, o.payment_method, c.full_name, c.email
            ORDER BY o.order_date DESC
        """

        cursor.execute(query, (customer_id,))
        db_rows = cursor.fetchall()

        cursor.close()
        conn.close()

        # Transform each order into DTO
        orders_dto = [transform_order_from_db(row) for row in db_rows]

        return func.HttpResponse(
            json.dumps({
                "status": "success",
                "count": len(orders_dto),
                "data": [order.model_dump() for order in orders_dto]
            }, default=str),
            status_code=200,
            mimetype="application/json"
        )

    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return func.HttpResponse(
            json.dumps({"status": "error", "message": str(e)}),
            status_code=500,
            mimetype="application/json"
        )

@app.route(route="products/catalog", methods=["GET"])
def get_product_catalog(req: func.HttpRequest) -> func.HttpResponse:
    """
    Get product catalog with transformation

    Returns:
    - Stock level indicators
    - Formatted pricing
    - Generated SKUs
    - Availability status

    Query Parameters:
    - category: Filter by category (optional)
    - in_stock_only: true/false (optional, default: false)

    Example: GET /api/products/catalog?category=Electronics&in_stock_only=true
    """
    logging.info('Processing get_product_catalog request')

    try:
        category = req.params.get('category')
        in_stock_only = req.params.get('in_stock_only', 'false').lower() == 'true'

        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Build dynamic query
        query = """
            SELECT
                product_id,
                product_name,
                category,
                price,
                stock_quantity,
                description
            FROM products
            WHERE 1=1
        """
        params = []

        if category:
            query += " AND category = %s"
            params.append(category)

        if in_stock_only:
            query += " AND stock_quantity > 0"

        query += " ORDER BY product_name"

        cursor.execute(query, params)
        db_rows = cursor.fetchall()

        cursor.close()
        conn.close()

        # Transform each product into DTO
        products_dto = [transform_product_from_db(row) for row in db_rows]

        # Group by stock level for frontend
        grouped_response = {
            "in_stock": [p.model_dump() for p in products_dto if p.in_stock],
            "out_of_stock": [p.model_dump() for p in products_dto if not p.in_stock]
        }

        return func.HttpResponse(
            json.dumps({
                "status": "success",
                "total_count": len(products_dto),
                "in_stock_count": len(grouped_response["in_stock"]),
                "out_of_stock_count": len(grouped_response["out_of_stock"]),
                "data": grouped_response
            }, default=str),
            status_code=200,
            mimetype="application/json"
        )

    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return func.HttpResponse(
            json.dumps({"status": "error", "message": str(e)}),
            status_code=500,
            mimetype="application/json"
        )

@app.route(route="order/{order_id}", methods=["GET"])
def get_order_details(req: func.HttpRequest) -> func.HttpResponse:
    """
    Get detailed order information with transformation

    Returns complete order details including:
    - Transformed order data
    - Parsed addresses
    - Masked payment info
    - Order items with product details

    Example: GET /api/order/1001
    """
    logging.info('Processing get_order_details request')

    try:
        order_id = req.route_params.get('order_id')

        if not order_id:
            return func.HttpResponse(
                json.dumps({"error": "order_id is required"}),
                status_code=400,
                mimetype="application/json"
            )

        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Get order details
        order_query = """
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
            WHERE o.order_id = %s
            GROUP BY o.order_id, o.order_date, o.total_amount, o.status,
                     o.shipping_address, o.payment_method, c.full_name, c.email
        """

        cursor.execute(order_query, (order_id,))
        order_row = cursor.fetchone()

        if not order_row:
            cursor.close()
            conn.close()
            return func.HttpResponse(
                json.dumps({"error": "Order not found"}),
                status_code=404,
                mimetype="application/json"
            )

        # Get order items
        items_query = """
            SELECT
                oi.quantity,
                oi.unit_price,
                p.product_name,
                p.product_id
            FROM order_items oi
            INNER JOIN products p ON oi.product_id = p.product_id
            WHERE oi.order_id = %s
        """

        cursor.execute(items_query, (order_id,))
        items_rows = cursor.fetchall()

        cursor.close()
        conn.close()

        # Transform order
        order_dto = transform_order_from_db(order_row)

        # Transform items
        items = [
            {
                "product_id": item['product_id'],
                "product_name": item['product_name'],
                "quantity": item['quantity'],
                "unit_price": float(item['unit_price']),
                "subtotal": float(item['quantity'] * item['unit_price'])
            }
            for item in items_rows
        ]

        response = order_dto.model_dump()
        response['items'] = items

        return func.HttpResponse(
            json.dumps({
                "status": "success",
                "data": response
            }, default=str),
            status_code=200,
            mimetype="application/json"
        )

    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return func.HttpResponse(
            json.dumps({"status": "error", "message": str(e)}),
            status_code=500,
            mimetype="application/json"
        )
