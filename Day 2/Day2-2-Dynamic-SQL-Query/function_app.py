import azure.functions as func
import logging
import json
import os
import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor

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

@app.route(route="products", methods=["GET", "POST"])
def get_products(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP trigger function to get products with dynamic filtering.

    Query parameters (GET) or Body (POST):
    - category: Product category to filter by (required)
    - maxPrice: Maximum price filter (optional, default: no limit)
    - minStock: Minimum stock quantity (optional, default: 0)

    Example Request:
    POST /api/products
    {
        "category": "Electronics",
        "maxPrice": 500,
        "minStock": 10
    }
    """
    logging.info('Processing get_products request')

    try:
        # Get parameters from query string or request body
        if req.method == "POST":
            try:
                req_body = req.get_json()
            except ValueError:
                return func.HttpResponse(
                    json.dumps({"error": "Invalid JSON in request body"}),
                    status_code=400,
                    mimetype="application/json"
                )

            category = req_body.get('category')
            max_price = req_body.get('maxPrice')
            min_stock = req_body.get('minStock', 0)
        else:
            category = req.params.get('category')
            max_price = req.params.get('maxPrice')
            min_stock = req.params.get('minStock', 0)

        # Validate required parameter
        if not category:
            return func.HttpResponse(
                json.dumps({"error": "Parameter 'category' is required"}),
                status_code=400,
                mimetype="application/json"
            )

        # Set defaults
        if max_price:
            try:
                max_price = float(max_price)
            except ValueError:
                return func.HttpResponse(
                    json.dumps({"error": "Invalid maxPrice value"}),
                    status_code=400,
                    mimetype="application/json"
                )
        else:
            max_price = 1000000  # No limit

        try:
            min_stock = int(min_stock)
        except ValueError:
            return func.HttpResponse(
                json.dumps({"error": "Invalid minStock value"}),
                status_code=400,
                mimetype="application/json"
            )

        # Connect to database
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Execute parameterized query (prevents SQL injection)
        query = """
            SELECT
                product_id,
                product_name,
                category,
                price,
                stock_quantity,
                description,
                created_at
            FROM products
            WHERE category = %s
              AND price <= %s
              AND stock_quantity >= %s
            ORDER BY product_name ASC
        """

        cursor.execute(query, (category, max_price, min_stock))
        products = cursor.fetchall()

        # Close connections
        cursor.close()
        conn.close()

        # Prepare response
        response_data = {
            "status": "success",
            "count": len(products),
            "filters": {
                "category": category,
                "maxPrice": max_price,
                "minStock": min_stock
            },
            "data": products
        }

        logging.info(f"Found {len(products)} products for category '{category}'")

        return func.HttpResponse(
            json.dumps(response_data, default=str),
            status_code=200,
            mimetype="application/json"
        )

    except psycopg2.Error as db_error:
        logging.error(f"Database error: {str(db_error)}")
        return func.HttpResponse(
            json.dumps({
                "status": "error",
                "message": "Database error occurred",
                "error": str(db_error)
            }),
            status_code=500,
            mimetype="application/json"
        )

    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        return func.HttpResponse(
            json.dumps({
                "status": "error",
                "message": "An unexpected error occurred",
                "error": str(e)
            }),
            status_code=500,
            mimetype="application/json"
        )
