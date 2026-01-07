import json
import logging
import os
import posixpath
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlparse

import azure.functions as func
from azure.core.exceptions import ResourceNotFoundError
from azure.storage.blob import BlobServiceClient

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
