"""
Data Transfer Objects (DTOs) for API responses
These models define the structure of data returned to clients
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

class CustomerDTO(BaseModel):
    """Customer information DTO - cleaned for API response"""
    customer_id: str = Field(..., description="Unique customer identifier")
    name: str = Field(..., description="Customer full name")
    email: str = Field(..., description="Customer email")
    phone: Optional[str] = Field(None, description="Phone number")
    member_since: datetime = Field(..., description="Registration date")
    total_orders: int = Field(0, description="Total number of orders")
    total_spent: float = Field(0.0, description="Total amount spent")
    status: str = Field("active", description="Customer status")

    class Config:
        json_schema_extra = {
            "example": {
                "customer_id": "CUST-0001",
                "name": "John Doe",
                "email": "john.doe@example.com",
                "phone": "+1-555-123-4567",
                "member_since": "2024-01-15T10:30:00",
                "total_orders": 25,
                "total_spent": 5432.50,
                "status": "active"
            }
        }

class OrderItemDTO(BaseModel):
    """Order item DTO"""
    product_id: int
    product_name: str
    quantity: int
    unit_price: float
    subtotal: float

class OrderDTO(BaseModel):
    """Order information DTO - cleaned for API response"""
    order_id: int = Field(..., description="Unique order identifier")
    order_number: str = Field(..., description="Human-readable order number")
    customer_name: str = Field(..., description="Customer name")
    customer_email: str = Field(..., description="Customer email")
    order_date: datetime = Field(..., description="Order date")
    status: str = Field(..., description="Order status")
    total_amount: float = Field(..., description="Total order amount")
    items_count: int = Field(..., description="Number of items")
    shipping_address: dict = Field(..., description="Parsed shipping address")
    payment_info: dict = Field(..., description="Payment information")

    class Config:
        json_schema_extra = {
            "example": {
                "order_id": 1001,
                "order_number": "ORD-2024-001001",
                "customer_name": "John Doe",
                "customer_email": "john.doe@example.com",
                "order_date": "2024-12-15T10:30:00",
                "status": "COMPLETED",
                "total_amount": 299.99,
                "items_count": 3,
                "shipping_address": {
                    "street": "123 Main St",
                    "city": "City",
                    "state": "State",
                    "zip": "12345"
                },
                "payment_info": {
                    "method": "Credit Card",
                    "last_four": "****"
                }
            }
        }

class ProductDTO(BaseModel):
    """Product information DTO - cleaned for API response"""
    product_id: int
    sku: str
    name: str
    category: str
    price: float
    discount_price: Optional[float] = None
    in_stock: bool
    stock_level: str  # "high", "medium", "low", "out_of_stock"
    image_url: Optional[str] = None

def transform_customer_from_db(db_row: dict) -> CustomerDTO:
    """
    Transform raw database row into CustomerDTO

    Example transformation:
    - Hide sensitive information
    - Format data for frontend consumption
    - Calculate derived fields
    - Apply business logic
    """
    return CustomerDTO(
        customer_id=db_row['customer_id'],
        name=db_row['full_name'],
        email=db_row['email'],
        phone=db_row.get('phone'),
        member_since=db_row['created_at'],
        total_orders=db_row.get('order_count', 0),
        total_spent=float(db_row.get('total_spent', 0)),
        status="active" if db_row.get('is_active', True) else "inactive"
    )

def transform_order_from_db(db_row: dict) -> OrderDTO:
    """
    Transform raw database order row into OrderDTO

    Transformations applied:
    - Format order number
    - Parse shipping address string
    - Mask sensitive payment info
    - Convert decimals to floats
    """

    # Parse shipping address (assuming format: "street, city, state zip")
    address_parts = db_row.get('shipping_address', '').split(',')
    shipping_address = {
        "street": address_parts[0].strip() if len(address_parts) > 0 else "",
        "city": address_parts[1].strip() if len(address_parts) > 1 else "",
        "state_zip": address_parts[2].strip() if len(address_parts) > 2 else ""
    }

    # Extract state and zip from "State ZIP"
    if shipping_address["state_zip"]:
        state_zip_parts = shipping_address["state_zip"].rsplit(' ', 1)
        shipping_address["state"] = state_zip_parts[0] if len(state_zip_parts) > 0 else ""
        shipping_address["zip"] = state_zip_parts[1] if len(state_zip_parts) > 1 else ""
        del shipping_address["state_zip"]

    # Mask payment information
    payment_info = {
        "method": db_row.get('payment_method', 'N/A'),
        "last_four": "****"  # Never expose full payment details
    }

    return OrderDTO(
        order_id=db_row['order_id'],
        order_number=f"ORD-{datetime.now().year}-{str(db_row['order_id']).zfill(6)}",
        customer_name=db_row.get('customer_name', 'N/A'),
        customer_email=db_row.get('customer_email', 'N/A'),
        order_date=db_row['order_date'],
        status=db_row['status'],
        total_amount=float(db_row['total_amount']),
        items_count=db_row.get('items_count', 0),
        shipping_address=shipping_address,
        payment_info=payment_info
    )

def transform_product_from_db(db_row: dict) -> ProductDTO:
    """
    Transform raw database product row into ProductDTO

    Transformations:
    - Calculate stock level category
    - Format pricing
    - Generate SKU if missing
    """
    stock_quantity = db_row.get('stock_quantity', 0)

    # Determine stock level
    if stock_quantity == 0:
        stock_level = "out_of_stock"
        in_stock = False
    elif stock_quantity < 10:
        stock_level = "low"
        in_stock = True
    elif stock_quantity < 50:
        stock_level = "medium"
        in_stock = True
    else:
        stock_level = "high"
        in_stock = True

    return ProductDTO(
        product_id=db_row['product_id'],
        sku=db_row.get('sku', f"SKU-{db_row['product_id']:06d}"),
        name=db_row['product_name'],
        category=db_row['category'],
        price=float(db_row['price']),
        discount_price=None,  # Could calculate from promotions table
        in_stock=in_stock,
        stock_level=stock_level,
        image_url=None  # Could generate from product_id
    )
