"""
Test script for Day 2-5 Transform DB Data Function
Run: python test_function.py
"""

import requests
import json

# Base URL (change if deployed to Azure)
BASE_URL = "http://localhost:7071/api"

def test_get_customer():
    """Test get customer with aggregates"""
    print("\n=== Test 1: Get Customer ===")
    customer_id = "CUST-0001"
    url = f"{BASE_URL}/customer/{customer_id}"

    response = requests.get(url)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

def test_get_customer_orders():
    """Test get customer orders with transformation"""
    print("\n=== Test 2: Get Customer Orders ===")
    customer_id = "CUST-0001"
    url = f"{BASE_URL}/customer/{customer_id}/orders"

    response = requests.get(url)
    print(f"Status Code: {response.status_code}")
    data = response.json()
    print(f"Order Count: {data.get('count')}")

    if data.get('data') and len(data['data']) > 0:
        print(f"\nFirst Order:")
        print(json.dumps(data['data'][0], indent=2))

        # Verify transformations
        first_order = data['data'][0]
        print(f"\nTransformation Verification:")
        print(f"- Order Number Format: {first_order.get('order_number')}")
        print(f"- Shipping Address Parsed: {type(first_order.get('shipping_address')) == dict}")
        print(f"- Payment Info Masked: {first_order.get('payment_info', {}).get('last_four') == '****'}")

def test_get_product_catalog():
    """Test get product catalog with transformations"""
    print("\n=== Test 3: Get Product Catalog ===")
    url = f"{BASE_URL}/products/catalog"

    response = requests.get(url)
    print(f"Status Code: {response.status_code}")
    data = response.json()
    print(f"Total Products: {data.get('total_count')}")
    print(f"In Stock: {data.get('in_stock_count')}")
    print(f"Out of Stock: {data.get('out_of_stock_count')}")

    if data.get('data', {}).get('in_stock'):
        print(f"\nFirst In-Stock Product:")
        first_product = data['data']['in_stock'][0]
        print(json.dumps(first_product, indent=2))

        # Verify transformations
        print(f"\nTransformation Verification:")
        print(f"- SKU Generated: {first_product.get('sku')}")
        print(f"- Stock Level Categorized: {first_product.get('stock_level')}")
        print(f"- In Stock Boolean: {first_product.get('in_stock')}")

def test_filter_by_category():
    """Test product catalog filtering"""
    print("\n=== Test 4: Filter Products by Category ===")
    url = f"{BASE_URL}/products/catalog?category=Electronics"

    response = requests.get(url)
    print(f"Status Code: {response.status_code}")
    data = response.json()
    print(f"Electronics Products: {data.get('total_count')}")

def test_in_stock_only():
    """Test filtering for in-stock products only"""
    print("\n=== Test 5: In-Stock Products Only ===")
    url = f"{BASE_URL}/products/catalog?in_stock_only=true"

    response = requests.get(url)
    print(f"Status Code: {response.status_code}")
    data = response.json()
    print(f"In Stock Count: {data.get('in_stock_count')}")
    print(f"Out of Stock Count: {data.get('out_of_stock_count')}")

def test_get_order_details():
    """Test get order details with items"""
    print("\n=== Test 6: Get Order Details ===")
    order_id = 1
    url = f"{BASE_URL}/order/{order_id}"

    response = requests.get(url)
    print(f"Status Code: {response.status_code}")
    data = response.json()

    if data.get('status') == 'success':
        order = data['data']
        print(f"\nOrder Details:")
        print(f"- Order Number: {order.get('order_number')}")
        print(f"- Status: {order.get('status')}")
        print(f"- Total Amount: ${order.get('total_amount')}")
        print(f"- Items Count: {order.get('items_count')}")

        if order.get('items'):
            print(f"\nOrder Items:")
            for item in order['items']:
                print(f"  - {item['product_name']}: {item['quantity']} x ${item['unit_price']} = ${item['subtotal']}")

def test_customer_not_found():
    """Test error handling for non-existent customer"""
    print("\n=== Test 7: Customer Not Found ===")
    customer_id = "CUST-9999"
    url = f"{BASE_URL}/customer/{customer_id}"

    response = requests.get(url)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

def test_order_not_found():
    """Test error handling for non-existent order"""
    print("\n=== Test 8: Order Not Found ===")
    order_id = 99999
    url = f"{BASE_URL}/order/{order_id}"

    response = requests.get(url)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

def test_multiple_customers():
    """Test getting data for multiple customers"""
    print("\n=== Test 9: Multiple Customers ===")
    customer_ids = ["CUST-0001", "CUST-0002", "CUST-0003"]

    for customer_id in customer_ids:
        url = f"{BASE_URL}/customer/{customer_id}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()['data']
            print(f"{data['name']}: {data['total_orders']} orders, ${data['total_spent']:.2f} spent")

def compare_raw_vs_transformed():
    """Demonstrate the difference between raw DB data and transformed DTO"""
    print("\n=== Test 10: Raw vs Transformed Comparison ===")

    print("RAW DATABASE ROW (what you shouldn't return):")
    raw_example = {
        "customer_id": "CUST-0001",
        "full_name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "+1-555-123-4567",
        "created_at": "2024-01-15 10:30:00",
        "is_active": True,
        "order_count": 25,
        "total_spent": "5432.50"  # Decimal as string
    }
    print(json.dumps(raw_example, indent=2))

    print("\nTRANSFORMED DTO (clean API response):")
    url = f"{BASE_URL}/customer/CUST-0001"
    response = requests.get(url)
    if response.status_code == 200:
        print(json.dumps(response.json()['data'], indent=2))

if __name__ == "__main__":
    print("Starting Transformation Tests...")
    print("Make sure the function is running (func start)")

    try:
        test_get_customer()
        test_get_customer_orders()
        test_get_product_catalog()
        test_filter_by_category()
        test_in_stock_only()
        test_get_order_details()
        test_customer_not_found()
        test_order_not_found()
        test_multiple_customers()
        compare_raw_vs_transformed()

        print("\n=== All Tests Completed ===")
    except requests.exceptions.ConnectionError:
        print("\nError: Could not connect to function.")
        print("Make sure the function is running: func start")
    except Exception as e:
        print(f"\nError during testing: {str(e)}")
