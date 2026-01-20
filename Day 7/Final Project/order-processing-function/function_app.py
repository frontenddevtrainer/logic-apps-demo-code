"""
Order Processing Azure Function
Final Project - Order Processing System

This function:
1. Receives X12 850 Purchase Order messages
2. Parses and maps X12 to JSON using configurable mappings
3. Validates the mapped order data
4. Stores valid orders in PostgreSQL database
5. Saves order documents to Blob Storage
6. Returns order confirmation with ID
"""

import json
import logging
import os
import posixpath
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import azure.functions as func
import psycopg2
from azure.core.exceptions import ResourceNotFoundError
from azure.storage.blob import BlobServiceClient, ContentSettings

from mapping_logic.mapper import map_segments, merge_mappings

DEFAULT_ELEMENT_SEPARATOR = "*"
DEFAULT_SEGMENT_SEPARATOR = "~"
DEFAULT_COMPONENT_SEPARATOR = ":"

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


def detect_delimiters(x12_text: str) -> Tuple[str, str, str]:
    candidate = x12_text.lstrip()
    if candidate.startswith("ISA") and len(candidate) >= 106:
        element_sep = candidate[3]
        component_sep = candidate[104]
        segment_sep = candidate[105]
        return element_sep, segment_sep, component_sep
    return DEFAULT_ELEMENT_SEPARATOR, DEFAULT_SEGMENT_SEPARATOR, DEFAULT_COMPONENT_SEPARATOR


def parse_x12(
    text: str,
    element_sep: str = DEFAULT_ELEMENT_SEPARATOR,
    segment_sep: str = DEFAULT_SEGMENT_SEPARATOR,
    component_sep: str = DEFAULT_COMPONENT_SEPARATOR,
) -> list[dict[str, Any]]:
    segments = []
    for raw_segment in text.split(segment_sep):
        raw_segment = raw_segment.strip()
        if not raw_segment:
            continue
        parts = raw_segment.split(element_sep)
        segment_id = parts[0]
        elements = []
        for element in parts[1:]:
            if component_sep and component_sep in element:
                elements.append(element.split(component_sep))
            else:
                elements.append(element)
        segments.append({"id": segment_id, "elements": elements})
    return segments


class BlobMappingStore:
    def __init__(self, service: BlobServiceClient, container: str) -> None:
        self._service = service
        self._container = container

    def download_json(self, blob_path: str) -> Dict[str, Any]:
        blob_client = self._service.get_blob_client(
            container=self._container, blob=blob_path
        )
        data = blob_client.download_blob().readall()
        return json.loads(data)


def _build_service_from_connection_string() -> BlobServiceClient:
    connection_string = os.environ.get("MAPPING_STORAGE_CONNECTION") or os.environ.get(
        "AzureWebJobsStorage"
    )
    if not connection_string:
        raise RuntimeError(
            "MAPPING_STORAGE_CONNECTION or AzureWebJobsStorage must be configured."
        )
    return BlobServiceClient.from_connection_string(connection_string)


def _parse_blob_url(blob_url: str) -> Tuple[str, str, str, Optional[str]]:
    parsed = urlparse(blob_url)
    path = parsed.path.lstrip("/")
    if not path:
        raise ValueError("mappingBlobUrl must include a container and blob path.")

    container, _, blob_path = path.partition("/")
    if not container or not blob_path:
        raise ValueError("mappingBlobUrl must include a container and blob path.")

    sas_token = parsed.query or None
    account_url = f"{parsed.scheme}://{parsed.netloc}"
    return account_url, container, blob_path, sas_token


def _build_store_from_blob_url(blob_url: str) -> Tuple[BlobMappingStore, str]:
    account_url, container, blob_path, sas_token = _parse_blob_url(blob_url)
    if sas_token:
        service = BlobServiceClient(account_url=account_url, credential=sas_token)
    else:
        service = _build_service_from_connection_string()
    return BlobMappingStore(service, container), blob_path


def _build_store_from_env(container: str) -> BlobMappingStore:
    service = _build_service_from_connection_string()
    return BlobMappingStore(service, container)


def _apply_mapping_root(mapping_path: str, mapping_root: str) -> str:
    if not mapping_root:
        return mapping_path
    mapping_root = mapping_root.strip("/")
    if not mapping_root:
        return mapping_path
    if mapping_path.startswith(f"{mapping_root}/") or mapping_path == mapping_root:
        return mapping_path
    return posixpath.join(mapping_root, mapping_path)


def _resolve_mapping_path(current_path: str, extends_path: str) -> str:
    if extends_path.startswith("/"):
        return extends_path.lstrip("/")
    current_dir = posixpath.dirname(current_path)
    return posixpath.normpath(posixpath.join(current_dir, extends_path))


def load_mapping_from_store(
    store: BlobMappingStore,
    mapping_path: str,
    cache: Optional[Dict[str, Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    if cache is None:
        cache = {}
    if mapping_path in cache:
        return cache[mapping_path]

    mapping = store.download_json(mapping_path)
    extends_path = mapping.get("extends")
    if extends_path:
        base_path = _resolve_mapping_path(mapping_path, extends_path)
        base_mapping = load_mapping_from_store(store, base_path, cache)
        mapping = merge_mappings(base_mapping, mapping)

    cache[mapping_path] = mapping
    return mapping


def _build_default_mapping_path(
    mapping_root: str, client: Optional[str], transaction_set: str
) -> str:
    if client:
        return posixpath.join(mapping_root, "clients", client, f"{transaction_set}.json")
    return posixpath.join(mapping_root, "standards", f"{transaction_set}.json")


@app.function_name(name="x12-map")
@app.route(route="x12-map", methods=["POST"])
def x12_map(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("X12 mapping request received")

    try:
        payload = req.get_json()
    except ValueError:
        return func.HttpResponse("Request body must be valid JSON.", status_code=400)

    if not isinstance(payload, dict):
        return func.HttpResponse("JSON payload must be an object.", status_code=400)

    segments = payload.get("segments")
    if segments is not None:
        if not isinstance(segments, list):
            return func.HttpResponse("segments must be an array.", status_code=400)
        if not all(isinstance(segment, dict) for segment in segments):
            return func.HttpResponse(
                "segments must be an array of objects.", status_code=400
            )
    else:
        x12_text = payload.get("x12") or payload.get("x12Text")
        if not x12_text:
            return func.HttpResponse("x12 or segments is required.", status_code=400)
        if not isinstance(x12_text, str):
            return func.HttpResponse("x12 must be a string.", status_code=400)
        detected_element, detected_segment, detected_component = detect_delimiters(
            x12_text
        )
        element_sep = payload.get("elementSeparator", detected_element)
        segment_sep = payload.get("segmentSeparator", detected_segment)
        component_sep = payload.get("componentSeparator", detected_component)
        segments = parse_x12(x12_text, element_sep, segment_sep, component_sep)

    mapping_blob_url = payload.get("mappingBlobUrl")
    mapping_root = payload.get("mappingRoot") or os.environ.get(
        "MAPPING_ROOT", "mapping"
    )

    try:
        if mapping_blob_url:
            store, mapping_path = _build_store_from_blob_url(mapping_blob_url)
        else:
            mapping_path = payload.get("mappingPath")
            if not mapping_path:
                transaction_set = payload.get("transactionSet")
                if not transaction_set:
                    return func.HttpResponse(
                        "transactionSet or mappingPath is required.", status_code=400
                    )
                client = payload.get("client")
                mapping_path = _build_default_mapping_path(
                    mapping_root, client, transaction_set
                )
            else:
                mapping_path = mapping_path.lstrip("/")
                mapping_path = _apply_mapping_root(mapping_path, mapping_root)

            mapping_container = payload.get("mappingContainer") or os.environ.get(
                "MAPPING_CONTAINER", "x12-mappings"
            )
            store = _build_store_from_env(mapping_container)

        mapping = load_mapping_from_store(store, mapping_path)
        output = map_segments(segments, mapping)
    except ResourceNotFoundError:
        return func.HttpResponse(
            "Mapping file not found in Blob Storage.", status_code=404
        )
    except Exception as exc:
        logging.exception("Mapping failed")
        return func.HttpResponse(str(exc), status_code=500)

    if payload.get("includeMeta"):
        response_body: Dict[str, Any] = {
            "mappingPath": mapping_path,
            "segmentCount": len(segments),
            "output": output,
        }
    else:
        response_body = output

    return func.HttpResponse(
        json.dumps(response_body, indent=2),
        status_code=200,
        mimetype="application/json",
    )


# =============================================================================
# ORDER VALIDATION FUNCTIONS
# =============================================================================

def normalize_items(order: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Normalize items from mapped order - handles both array and single object formats.
    The mapper outputs 'items[]' as an object (last item wins) when array syntax is used.
    """
    # Check for items[] (object from mapper's literal interpretation)
    items_obj = order.get("items[]")
    if items_obj and isinstance(items_obj, dict):
        # Convert string numbers to actual numbers
        item = {}
        for k, v in items_obj.items():
            if k in ("quantity", "unitPrice") and isinstance(v, str):
                try:
                    item[k] = float(v)
                except ValueError:
                    item[k] = v
            else:
                item[k] = v
        return [item]

    # Check for items array
    items = order.get("items", [])
    if isinstance(items, list):
        return items

    # Check for single item object
    if isinstance(items, dict):
        return [items]

    return []


def validate_mapped_order(order: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate mapped order data from X12 850.

    Expected fields from X12 850 mapping:
    - purchaseOrderNumber: from BEG03
    - purchaseOrderDate: from BEG05
    - buyer: object with id and name from N1 (BY)
    - seller: object with id and name from N1 (SE)
    - items: array from PO1 segments
    """
    errors = []
    warnings = []

    # Validate purchase order number
    if not order.get("purchaseOrderNumber"):
        errors.append("purchaseOrderNumber is required (BEG03)")

    # Validate purchase order date
    if not order.get("purchaseOrderDate"):
        warnings.append("purchaseOrderDate is recommended (BEG05)")

    # Validate buyer information
    buyer = order.get("buyer", {})
    if not buyer.get("name"):
        warnings.append("buyer.name is recommended (N1-BY)")

    # Normalize and validate items
    items = normalize_items(order)
    if not items:
        errors.append("At least one line item is required (PO1)")
    else:
        total_amount = 0
        for i, item in enumerate(items):
            item_prefix = f"items[{i}]"

            if not item.get("productId"):
                errors.append(f"{item_prefix}.productId is required (PO1-07)")

            quantity = item.get("quantity")
            # Handle string quantities from mapping
            if isinstance(quantity, str):
                try:
                    quantity = float(quantity)
                except ValueError:
                    pass

            if quantity is None:
                errors.append(f"{item_prefix}.quantity is required (PO1-02)")
            elif not isinstance(quantity, (int, float)) or quantity <= 0:
                errors.append(f"{item_prefix}.quantity must be positive")

            unit_price = item.get("unitPrice")
            # Handle string prices from mapping
            if isinstance(unit_price, str):
                try:
                    unit_price = float(unit_price)
                except ValueError:
                    pass

            if unit_price is None:
                warnings.append(f"{item_prefix}.unitPrice is recommended (PO1-04)")
            elif isinstance(unit_price, (int, float)) and unit_price >= 0:
                if isinstance(quantity, (int, float)) and quantity > 0:
                    total_amount += quantity * unit_price

    is_valid = len(errors) == 0

    result = {
        "isValid": is_valid,
        "errors": errors,
        "warnings": warnings,
        "validatedAt": datetime.utcnow().isoformat() + "Z"
    }

    if is_valid and items:
        calculated_total = 0
        for item in items:
            qty = item.get("quantity", 0)
            price = item.get("unitPrice", 0)
            if isinstance(qty, str):
                try:
                    qty = float(qty)
                except ValueError:
                    qty = 0
            if isinstance(price, str):
                try:
                    price = float(price)
                except ValueError:
                    price = 0
            if isinstance(qty, (int, float)) and isinstance(price, (int, float)):
                calculated_total += qty * price
        result["calculatedTotal"] = round(calculated_total, 2)
        result["itemCount"] = len(items)
        # Store normalized items back to order for database storage
        order["_normalized_items"] = items

    return result


# =============================================================================
# POSTGRESQL STORAGE FUNCTIONS
# =============================================================================

def get_postgres_connection():
    """Create PostgreSQL connection from environment variables."""
    return psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST"),
        database=os.environ.get("POSTGRES_DB", "order_processing"),
        user=os.environ.get("POSTGRES_USER"),
        password=os.environ.get("POSTGRES_PASSWORD"),
        port=os.environ.get("POSTGRES_PORT", "5432"),
        sslmode=os.environ.get("POSTGRES_SSLMODE", "require")
    )


def store_order_in_postgres(order_id: str, order: Dict[str, Any], validation: Dict[str, Any]) -> None:
    """Store order and items in PostgreSQL database."""
    conn = get_postgres_connection()
    try:
        with conn.cursor() as cur:
            # Insert main order record
            cur.execute("""
                INSERT INTO orders (
                    order_id, customer_id, customer_name, customer_email,
                    total_amount, item_count, status, order_date,
                    shipping_address, notes
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                order_id,
                order.get("buyer", {}).get("id", ""),
                order.get("buyer", {}).get("name", ""),
                order.get("buyer", {}).get("email", ""),
                validation.get("calculatedTotal", 0),
                validation.get("itemCount", 0),
                "pending",
                order.get("purchaseOrderDate", datetime.utcnow().isoformat()),
                json.dumps(order.get("shipTo", {})),
                order.get("notes", "")
            ))

            # Insert order items (use normalized items if available)
            items = order.get("_normalized_items") or normalize_items(order)
            for item in items:
                qty = item.get("quantity", 0)
                price = item.get("unitPrice", 0)
                if isinstance(qty, str):
                    try:
                        qty = float(qty)
                    except ValueError:
                        qty = 0
                if isinstance(price, str):
                    try:
                        price = float(price)
                    except ValueError:
                        price = 0
                cur.execute("""
                    INSERT INTO order_items (
                        order_id, product_id, product_name, quantity,
                        unit_price, line_total
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    order_id,
                    item.get("productId", ""),
                    item.get("description", ""),
                    qty,
                    price,
                    qty * price
                ))

            conn.commit()
    finally:
        conn.close()


# =============================================================================
# BLOB STORAGE FUNCTIONS
# =============================================================================

def save_order_to_blob(order_id: str, order_document: Dict[str, Any]) -> str:
    """Save order document to Blob Storage and return the blob path."""
    connection_string = os.environ.get("ORDER_STORAGE_CONNECTION") or os.environ.get("AzureWebJobsStorage")
    container_name = os.environ.get("ORDER_CONTAINER", "order-documents")

    service = BlobServiceClient.from_connection_string(connection_string)

    # Create date-based path: order-documents/2024/01/15/ORD-xxx.json
    now = datetime.utcnow()
    blob_path = f"{now.strftime('%Y/%m/%d')}/{order_id}.json"

    blob_client = service.get_blob_client(container=container_name, blob=blob_path)

    blob_client.upload_blob(
        json.dumps(order_document, indent=2),
        content_settings=ContentSettings(content_type="application/json"),
        overwrite=True
    )

    return f"{container_name}/{blob_path}"


# =============================================================================
# MAIN ORDER PROCESSING ENDPOINT
# =============================================================================

@app.function_name(name="process-order")
@app.route(route="process-order", methods=["POST"])
def process_order(req: func.HttpRequest) -> func.HttpResponse:
    """
    Complete order processing endpoint:
    1. Receive X12 850 Purchase Order
    2. Parse and map to JSON
    3. Validate the order
    4. Store in PostgreSQL
    5. Save document to Blob Storage
    6. Return confirmation with Order ID
    """
    logging.info("Order processing request received")

    try:
        payload = req.get_json()
    except ValueError:
        return func.HttpResponse(
            json.dumps({"success": False, "error": "Request body must be valid JSON."}),
            status_code=400,
            mimetype="application/json"
        )

    if not isinstance(payload, dict):
        return func.HttpResponse(
            json.dumps({"success": False, "error": "JSON payload must be an object."}),
            status_code=400,
            mimetype="application/json"
        )

    # Generate order ID
    order_id = f"ORD-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
    order_timestamp = datetime.utcnow().isoformat() + "Z"

    # Step 1: Parse X12 message
    segments = payload.get("segments")
    if segments is None:
        x12_text = payload.get("x12") or payload.get("x12Text")
        if not x12_text:
            return func.HttpResponse(
                json.dumps({"success": False, "error": "x12 or segments is required."}),
                status_code=400,
                mimetype="application/json"
            )
        detected_element, detected_segment, detected_component = detect_delimiters(x12_text)
        element_sep = payload.get("elementSeparator", detected_element)
        segment_sep = payload.get("segmentSeparator", detected_segment)
        component_sep = payload.get("componentSeparator", detected_component)
        segments = parse_x12(x12_text, element_sep, segment_sep, component_sep)

    # Step 2: Load mapping and transform to JSON
    mapping_root = payload.get("mappingRoot") or os.environ.get("MAPPING_ROOT", "mapping")

    try:
        mapping_blob_url = payload.get("mappingBlobUrl")
        if mapping_blob_url:
            store, mapping_path = _build_store_from_blob_url(mapping_blob_url)
        else:
            mapping_path = payload.get("mappingPath")
            if not mapping_path:
                transaction_set = payload.get("transactionSet", "850")
                client = payload.get("client")
                mapping_path = _build_default_mapping_path(mapping_root, client, transaction_set)
            else:
                mapping_path = mapping_path.lstrip("/")
                mapping_path = _apply_mapping_root(mapping_path, mapping_root)

            mapping_container = payload.get("mappingContainer") or os.environ.get("MAPPING_CONTAINER", "x12-mappings")
            store = _build_store_from_env(mapping_container)

        mapping = load_mapping_from_store(store, mapping_path)
        mapped_order = map_segments(segments, mapping)
    except ResourceNotFoundError:
        return func.HttpResponse(
            json.dumps({"success": False, "error": "Mapping file not found in Blob Storage."}),
            status_code=404,
            mimetype="application/json"
        )
    except Exception as exc:
        logging.exception("Mapping failed")
        return func.HttpResponse(
            json.dumps({"success": False, "error": f"Mapping failed: {str(exc)}"}),
            status_code=500,
            mimetype="application/json"
        )

    # Step 3: Validate the mapped order
    validation_result = validate_mapped_order(mapped_order)

    if not validation_result["isValid"]:
        return func.HttpResponse(
            json.dumps({
                "success": False,
                "orderId": order_id,
                "message": "Order validation failed",
                "errors": validation_result["errors"],
                "warnings": validation_result["warnings"],
                "validatedAt": validation_result["validatedAt"]
            }),
            status_code=400,
            mimetype="application/json"
        )

    # Step 4: Store in PostgreSQL
    try:
        store_order_in_postgres(order_id, mapped_order, validation_result)
        db_status = "Order saved to PostgreSQL"
    except Exception as exc:
        logging.exception("PostgreSQL storage failed")
        db_status = f"PostgreSQL storage failed: {str(exc)}"

    # Step 5: Save to Blob Storage
    order_document = {
        "orderId": order_id,
        "orderDate": order_timestamp,
        "status": "pending",
        "originalX12": payload.get("x12", ""),
        "mappedOrder": mapped_order,
        "validation": validation_result,
        "metadata": {
            "createdAt": order_timestamp,
            "source": "X12-850-OrderProcessing",
            "version": "1.0"
        }
    }

    try:
        blob_path = save_order_to_blob(order_id, order_document)
        blob_status = f"Document saved to {blob_path}"
    except Exception as exc:
        logging.exception("Blob storage failed")
        blob_path = None
        blob_status = f"Blob storage failed: {str(exc)}"

    # Step 6: Return confirmation
    response = {
        "success": True,
        "message": "Order processed successfully",
        "orderId": order_id,
        "orderDate": order_timestamp,
        "status": "pending",
        "summary": {
            "purchaseOrderNumber": mapped_order.get("purchaseOrderNumber"),
            "buyer": mapped_order.get("buyer", {}).get("name"),
            "itemCount": validation_result.get("itemCount"),
            "totalAmount": validation_result.get("calculatedTotal")
        },
        "storage": {
            "database": db_status,
            "blobPath": blob_path
        },
        "warnings": validation_result.get("warnings", [])
    }

    logging.info(f"Order {order_id} processed successfully")

    return func.HttpResponse(
        json.dumps(response, indent=2),
        status_code=201,
        mimetype="application/json"
    )
