"""
Test script for Day 2-2 Dynamic SQL Query Function
Run: python test_function.py
"""

import requests
import json

# Base URL (change if deployed to Azure)
BASE_URL = "http://localhost:7071/api/products"

def test_get_request():
    """Test GET request with query parameters"""
    print("\n=== Test 1: GET Request ===")
    params = {
        "category": "Electronics",
        "maxPrice": 500,
        "minStock": 10
    }

    response = requests.get(BASE_URL, params=params)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

def test_post_request():
    """Test POST request with JSON body"""
    print("\n=== Test 2: POST Request ===")
    payload = {
        "category": "Electronics",
        "maxPrice": 100,
        "minStock": 50
    }

    response = requests.post(BASE_URL, json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

def test_missing_parameter():
    """Test error handling for missing required parameter"""
    print("\n=== Test 3: Missing Required Parameter ===")
    payload = {
        "maxPrice": 500
    }

    response = requests.post(BASE_URL, json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

def test_invalid_price():
    """Test error handling for invalid price"""
    print("\n=== Test 4: Invalid Price Value ===")
    payload = {
        "category": "Electronics",
        "maxPrice": "invalid"
    }

    response = requests.post(BASE_URL, json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

def test_no_results():
    """Test query that returns no results"""
    print("\n=== Test 5: No Results ===")
    payload = {
        "category": "NonExistentCategory",
        "maxPrice": 10
    }

    response = requests.post(BASE_URL, json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

def test_all_products_in_category():
    """Test getting all products in a category (no price limit)"""
    print("\n=== Test 6: All Products in Category ===")
    payload = {
        "category": "Clothing"
    }

    response = requests.post(BASE_URL, json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

if __name__ == "__main__":
    print("Starting Function Tests...")
    print("Make sure the function is running (func start)")

    try:
        test_get_request()
        test_post_request()
        test_missing_parameter()
        test_invalid_price()
        test_no_results()
        test_all_products_in_category()

        print("\n=== All Tests Completed ===")
    except requests.exceptions.ConnectionError:
        print("\nError: Could not connect to function.")
        print("Make sure the function is running: func start")
    except Exception as e:
        print(f"\nError during testing: {str(e)}")
