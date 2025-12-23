import csv
import io
import logging
import os
from typing import Optional
from urllib.parse import parse_qs, urlparse

import azure.functions as func
from azure.storage.blob import BlobClient

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


def _build_blob_client(blob_url: str) -> BlobClient:
    """Return a BlobClient based on the provided URL and available credentials."""
    parsed = urlparse(blob_url)
    query_params = parse_qs(parsed.query)

    if "sig" in query_params:
        # SAS already supplies authentication, so no extra credential needed.
        return BlobClient.from_blob_url(blob_url)

    credential: Optional[str] = os.environ.get("AzureWebJobsStorage")
    if not credential:
        raise RuntimeError(
            "AzureWebJobsStorage setting must be configured when blobUrl has no SAS token."
        )

    return BlobClient.from_blob_url(blob_url, credential=credential)


@app.function_name(name="csv-processor")
@app.route(route="csv-processor", methods=["POST"])
def csv_processor(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("CSV processing function triggered")

    try:
        body = req.get_json()
    except ValueError:
        logging.warning("Invalid JSON payload supplied.")
        return func.HttpResponse("Request body must be valid JSON.", status_code=400)

    if not isinstance(body, dict):
        logging.warning("JSON payload is not an object.")
        return func.HttpResponse(
            "JSON payload must be an object that contains blobUrl.", status_code=400
        )

    blob_url = body.get("blobUrl")
    if not blob_url:
        logging.warning("Missing blobUrl in request payload.")
        return func.HttpResponse("blobUrl is required", status_code=400)

    try:
        blob_client = _build_blob_client(blob_url)
        stream = blob_client.download_blob().chunks()

        text_stream = io.TextIOWrapper(
            io.BufferedReader(io.BytesIO(b"".join(stream))),
            encoding="utf-8",
        )

        reader = csv.DictReader(text_stream)

        row_count = 0
        for row_count, row in enumerate(reader, start=1):
            logging.info("Row %s: %s", row_count, row)

        return func.HttpResponse(
            f"CSV processed successfully. Rows: {row_count}",
            status_code=200,
        )

    except Exception as exc:  # pragma: no cover - Azure Functions runtime handles logging
        logging.error("Failed to process CSV blob: %s", exc)
        return func.HttpResponse(str(exc), status_code=500)
