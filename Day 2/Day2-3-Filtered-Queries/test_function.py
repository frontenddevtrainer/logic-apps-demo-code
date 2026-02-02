"""
Test script for Day 2-3 Filtered Queries with Pagination
Run: python test_function.py
"""

import requests
import json

# Base URL (change if deployed to Azure)
BASE_URL = "http://localhost:7071/api/orders"

def test_first_page():
    """Test first page of completed orders"""
    print("\n=== Test 1: First Page (1-100) ===")
    payload = {
        "status": "COMPLETED",
        "page": 1,
        "pageSize": 100
    }

    response = requests.post(BASE_URL, json=payload)
    print(f"Status Code: {response.status_code}")
    data = response.json()
    print(f"Total Records: {data['pagination']['totalRecords']}")
    print(f"Total Pages: {data['pagination']['totalPages']}")
    print(f"Current Page: {data['pagination']['page']}")
    print(f"Records Returned: {len(data['data'])}")
    print(f"Has Next Page: {data['pagination']['hasNextPage']}")

def test_second_page():
    """Test second page of completed orders"""
    print("\n=== Test 2: Second Page (101-200) ===")
    payload = {
        "status": "COMPLETED",
        "page": 2,
        "pageSize": 100
    }

    response = requests.post(BASE_URL, json=payload)
    print(f"Status Code: {response.status_code}")
    data = response.json()
    print(f"Current Page: {data['pagination']['page']}")
    print(f"Records Returned: {len(data['data'])}")
    print(f"Has Previous Page: {data['pagination']['hasPreviousPage']}")
    print(f"Has Next Page: {data['pagination']['hasNextPage']}")

def test_custom_page_size():
    """Test with smaller page size"""
    print("\n=== Test 3: Custom Page Size (50 records) ===")
    payload = {
        "status": "PENDING",
        "page": 1,
        "pageSize": 50
    }

    response = requests.post(BASE_URL, json=payload)
    print(f"Status Code: {response.status_code}")
    data = response.json()
    print(f"Page Size: {data['pagination']['pageSize']}")
    print(f"Records Returned: {len(data['data'])}")
    print(f"Total Pages: {data['pagination']['totalPages']}")

def test_date_range():
    """Test with custom date range"""
    print("\n=== Test 4: Custom Date Range ===")
    payload = {
        "status": "COMPLETED",
        "startDate": "2024-01-01",
        "endDate": "2024-12-31",
        "page": 1,
        "pageSize": 25
    }

    response = requests.post(BASE_URL, json=payload)
    print(f"Status Code: {response.status_code}")
    data = response.json()
    print(f"Filters: {json.dumps(data['filters'], indent=2)}")
    print(f"Total Records in Range: {data['pagination']['totalRecords']}")
    print(f"Records Returned: {len(data['data'])}")

def test_all_statuses():
    """Test different order statuses"""
    print("\n=== Test 5: All Status Types ===")
    statuses = ['PENDING', 'PROCESSING', 'COMPLETED', 'CANCELLED']

    for status in statuses:
        payload = {
            "status": status,
            "page": 1,
            "pageSize": 10
        }
        response = requests.post(BASE_URL, json=payload)
        data = response.json()
        print(f"{status}: {data['pagination']['totalRecords']} orders")

def test_missing_required_param():
    """Test error handling for missing status"""
    print("\n=== Test 6: Missing Required Parameter ===")
    payload = {
        "page": 1,
        "pageSize": 100
    }

    response = requests.post(BASE_URL, json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

def test_invalid_status():
    """Test error handling for invalid status"""
    print("\n=== Test 7: Invalid Status Value ===")
    payload = {
        "status": "INVALID_STATUS",
        "page": 1
    }

    response = requests.post(BASE_URL, json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

def test_headers():
    """Test pagination headers"""
    print("\n=== Test 8: Check Response Headers ===")
    payload = {
        "status": "COMPLETED",
        "page": 1,
        "pageSize": 100
    }

    response = requests.post(BASE_URL, json=payload)
    print(f"X-Total-Count: {response.headers.get('X-Total-Count')}")
    print(f"X-Page: {response.headers.get('X-Page')}")
    print(f"X-Page-Size: {response.headers.get('X-Page-Size')}")
    print(f"X-Total-Pages: {response.headers.get('X-Total-Pages')}")

def test_last_page():
    """Test navigating to last page"""
    print("\n=== Test 9: Navigate to Last Page ===")

    # First get total pages
    payload = {
        "status": "COMPLETED",
        "page": 1,
        "pageSize": 50
    }
    response = requests.post(BASE_URL, json=payload)
    data = response.json()
    total_pages = data['pagination']['totalPages']

    # Then request last page
    payload['page'] = total_pages
    response = requests.post(BASE_URL, json=payload)
    data = response.json()

    print(f"Last Page Number: {data['pagination']['page']}")
    print(f"Records on Last Page: {len(data['data'])}")
    print(f"Has Next Page: {data['pagination']['hasNextPage']}")
    print(f"Has Previous Page: {data['pagination']['hasPreviousPage']}")

if __name__ == "__main__":
    print("Starting Pagination Tests...")
    print("Make sure the function is running (func start)")

    try:
        test_first_page()
        test_second_page()
        test_custom_page_size()
        test_date_range()
        test_all_statuses()
        test_missing_required_param()
        test_invalid_status()
        test_headers()
        test_last_page()

        print("\n=== All Tests Completed ===")
    except requests.exceptions.ConnectionError:
        print("\nError: Could not connect to function.")
        print("Make sure the function is running: func start")
    except Exception as e:
        print(f"\nError during testing: {str(e)}")
