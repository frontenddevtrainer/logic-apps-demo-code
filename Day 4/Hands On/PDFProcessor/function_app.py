import json
import logging
import os
from io import BytesIO
from typing import Optional

import azure.functions as func
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from azure.storage.blob import BlobServiceClient, StandardBlobTier
from azure.core.exceptions import ResourceNotFoundError

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

_blob_service_client: Optional[BlobServiceClient] = None
_document_client: Optional[DocumentAnalysisClient] = None

INCOMING_CONTAINER = os.getenv("INCOMING_CONTAINER", "incoming")
PROCESSED_CONTAINER = os.getenv("PROCESSED_CONTAINER", "processed")
ARCHIVE_CONTAINER = os.getenv("ARCHIVE_CONTAINER", "archive")


def _get_required_setting(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise EnvironmentError(f"Required app setting '{name}' is missing.")
    return value


def _get_blob_service_client() -> BlobServiceClient:
    global _blob_service_client
    if _blob_service_client is None:
        connection_string = _get_required_setting("AZURE_STORAGE_CONNECTION_STRING")
        _blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    return _blob_service_client


def _get_document_client() -> DocumentAnalysisClient:
    global _document_client
    if _document_client is None:
        endpoint = _get_required_setting("DOCUMENT_INTELLIGENCE_ENDPOINT")
        key = _get_required_setting("DOCUMENT_INTELLIGENCE_KEY")
        _document_client = DocumentAnalysisClient(endpoint=endpoint, credential=AzureKeyCredential(key))
    return _document_client


def _extract_text_from_pdf(pdf_data: bytes) -> str:
    client = _get_document_client()
    poller = client.begin_analyze_document("prebuilt-read", pdf_data)
    result = poller.result()
    return result.content.strip()


def _upload_processed_text(blob_service: BlobServiceClient, blob_name: str, text: str) -> str:
    base_name = os.path.splitext(blob_name)[0]
    processed_blob_name = f"{base_name}.txt"
    processed_client = blob_service.get_blob_client(container=PROCESSED_CONTAINER, blob=processed_blob_name)
    processed_client.upload_blob(text.encode("utf-8"), overwrite=True)
    return processed_blob_name


def _archive_original(blob_service: BlobServiceClient, blob_name: str, pdf_data: bytes) -> None:
    archive_client = blob_service.get_blob_client(container=ARCHIVE_CONTAINER, blob=blob_name)
    archive_client.upload_blob(BytesIO(pdf_data), overwrite=True)
    archive_client.set_standard_blob_tier(StandardBlobTier.Cool)
    incoming_client = blob_service.get_blob_client(container=INCOMING_CONTAINER, blob=blob_name)
    incoming_client.delete_blob(delete_snapshots="include")


@app.route(route="pdf_processor", methods=["POST"])
def pdf_processor(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Starting PDF processing pipeline invocation.")
    try:
        payload = req.get_json()
    except ValueError:
        return func.HttpResponse("Request body must be valid JSON.", status_code=400)

    blob_name = payload.get("blobName") or payload.get("name")
    correlation_id = payload.get("correlationId")

    if not blob_name:
        return func.HttpResponse("The request body must include a 'blobName'.", status_code=400)

    blob_service = _get_blob_service_client()
    incoming_client = blob_service.get_blob_client(container=INCOMING_CONTAINER, blob=blob_name)

    try:
        pdf_data = incoming_client.download_blob().readall()
    except ResourceNotFoundError:
        return func.HttpResponse(f"Blob '{blob_name}' was not found in container '{INCOMING_CONTAINER}'.", status_code=404)

    try:
        extracted_text = _extract_text_from_pdf(pdf_data)
        processed_blob_name = _upload_processed_text(blob_service, blob_name, extracted_text or " ")
        _archive_original(blob_service, blob_name, pdf_data)
    except Exception as exc:  # pylint: disable=broad-except
        logging.exception("Failed to process blob %s", blob_name)
        return func.HttpResponse(f"Failed to process PDF: {exc}", status_code=500)

    response = {
        "blobName": blob_name,
        "processedBlob": processed_blob_name,
        "archiveContainer": ARCHIVE_CONTAINER,
        "processedContainer": PROCESSED_CONTAINER,
        "textLength": len(extracted_text),
        "correlationId": correlation_id,
    }

    logging.info("Successfully processed %s", blob_name)
    return func.HttpResponse(
        json.dumps(response),
        status_code=200,
        mimetype="application/json",
    )
