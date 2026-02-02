import azure.functions as func
import logging
import json
import os
import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
import math

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

@app.route(route="orders", methods=["GET", "POST"])
def get_orders(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP trigger function to get orders with filtering and pagination.

    Query parameters (GET) or Body (POST):
    - status: Order status filter (required) - PENDING, PROCESSING, COMPLETED, CANCELLED
    - startDate: Filter orders from this date (optional, default: 30 days ago)
    - endDate: Filter orders until this date (optional, default: today)
    - page: Page number, 1-based (optional, default: 1)
    - pageSize: Number of records per page (optional, default: 100, max: 500)

    Example Request:
    POST /api/orders
    {
        "status": "COMPLETED",
        "startDate": "2024-01-01",
        "endDate": "2024-12-31",
        "page": 1,
        "pageSize": 100
    }
    """
    logging.info('Processing get_orders request')

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

            status = req_body.get('status')
            start_date = req_body.get('startDate')
            end_date = req_body.get('endDate')
            page = req_body.get('page', 1)
            page_size = req_body.get('pageSize', 100)
        else:
            status = req.params.get('status')
            start_date = req.params.get('startDate')
            end_date = req.params.get('endDate')
            page = int(req.params.get('page', 1))
            page_size = int(req.params.get('pageSize', 100))

        # Validate required parameter
        if not status:
            return func.HttpResponse(
                json.dumps({"error": "Parameter 'status' is required"}),
                status_code=400,
                mimetype="application/json"
            )

        # Validate status value
        valid_statuses = ['PENDING', 'PROCESSING', 'COMPLETED', 'CANCELLED']
        if status not in valid_statuses:
            return func.HttpResponse(
                json.dumps({
                    "error": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
                }),
                status_code=400,
                mimetype="application/json"
            )

        # Set default dates
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')

        # Validate and set pagination parameters
        try:
            page = int(page)
            page_size = int(page_size)

            if page < 1:
                page = 1
            if page_size < 1:
                page_size = 100
            if page_size > 500:
                page_size = 500

        except ValueError:
            return func.HttpResponse(
                json.dumps({"error": "Invalid page or pageSize value"}),
                status_code=400,
                mimetype="application/json"
            )

        # Calculate offset
        offset = (page - 1) * page_size

        # Connect to database
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Get total count first
        count_query = """
            SELECT COUNT(*) as total_count
            FROM orders
            WHERE status = %s
              AND order_date >= %s
              AND order_date <= %s
        """
        cursor.execute(count_query, (status, start_date, end_date))
        total_count = cursor.fetchone()['total_count']

        # Calculate total pages
        total_pages = math.ceil(total_count / page_size) if total_count > 0 else 0

        # Get paginated results (BEST PRACTICE: filter at database level)
        query = """
            SELECT
                order_id,
                customer_id,
                order_date,
                total_amount,
                status,
                shipping_address,
                payment_method
            FROM orders
            WHERE status = %s
              AND order_date >= %s
              AND order_date <= %s
            ORDER BY order_date DESC
            LIMIT %s OFFSET %s
        """

        cursor.execute(query, (status, start_date, end_date, page_size, offset))
        orders = cursor.fetchall()

        # Close connections
        cursor.close()
        conn.close()

        # Prepare response with pagination metadata
        response_data = {
            "status": "success",
            "pagination": {
                "page": page,
                "pageSize": page_size,
                "totalRecords": total_count,
                "totalPages": total_pages,
                "hasNextPage": page < total_pages,
                "hasPreviousPage": page > 1
            },
            "filters": {
                "status": status,
                "startDate": start_date,
                "endDate": end_date
            },
            "data": orders
        }

        logging.info(f"Found {len(orders)} orders (page {page}/{total_pages}) for status '{status}'")

        return func.HttpResponse(
            json.dumps(response_data, default=str),
            status_code=200,
            headers={
                "Content-Type": "application/json",
                "X-Total-Count": str(total_count),
                "X-Page": str(page),
                "X-Page-Size": str(page_size),
                "X-Total-Pages": str(total_pages)
            },
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
