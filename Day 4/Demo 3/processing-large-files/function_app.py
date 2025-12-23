import base64
import binascii
import json
import logging
import os
from typing import List, Optional

import azure.functions as func
from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError
from azure.storage.blob import BlobBlock, BlobServiceClient, ContentSettings

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

_blob_service_client: Optional[BlobServiceClient] = None
RECOMMENDED_BLOCK_SIZE = 4 * 1024 * 1024  # 4 MB keeps Logic Apps stable.
MAX_BLOCK_SIZE = 100 * 1024 * 1024  # REST API limit for Put Block.
MAX_BLOCKS_PER_BLOB = 50_000


def _get_storage_connection_string() -> str:
    """Pick the first available storage connection string."""
    for key in ("LargeFileStorageConnection", "AzureWebJobsStorage"):
        value = os.environ.get(key)
        if value:
            return value
    raise RuntimeError("No storage connection string configured.")


def _get_blob_client(container_name: str, blob_name: str):
    global _blob_service_client
    if _blob_service_client is None:
        _blob_service_client = BlobServiceClient.from_connection_string(
            _get_storage_connection_string()
        )

    container_client = _blob_service_client.get_container_client(container_name)
    try:
        container_client.create_container()
    except ResourceExistsError:
        pass

    return container_client.get_blob_client(blob_name)


def _decode_chunk(encoded_chunk: str) -> bytes:
    if not encoded_chunk:
        raise ValueError("chunkData must contain a base64 string.")
    try:
        return base64.b64decode(encoded_chunk)
    except binascii.Error as exc:
        raise ValueError("chunkData is not valid base64 content.") from exc


def _normalise_block_id(value) -> str:
    """
    Convert the provided block identifier to a base64 encoded string.

    Azure expects block identifiers to be base64 strings, so we accept either
    raw numbers/strings or pre-encoded identifiers to keep the Logic App simple.
    """
    if value is None:
        raise ValueError("Either blockId or blockNumber is required.")

    if isinstance(value, int):
        formatted = f"{value:07d}"
        return base64.b64encode(formatted.encode()).decode()

    value_str = str(value)
    try:
        base64.b64decode(value_str, validate=True)
        return value_str
    except (ValueError, binascii.Error):
        formatted = value_str if not value_str.isdigit() else value_str.zfill(7)
        return base64.b64encode(formatted.encode()).decode()


def _get_block_id_from_payload(payload: dict) -> str:
    if "blockId" in payload and payload["blockId"]:
        return _normalise_block_id(payload["blockId"])
    if "blockNumber" in payload:
        return _normalise_block_id(payload["blockNumber"])
    raise ValueError("Provide blockId or blockNumber for staging blocks.")


def _normalise_block_list(blocks) -> List[BlobBlock]:
    if not isinstance(blocks, list) or not blocks:
        raise ValueError("blockList must be a non-empty list.")

    normalised: List[BlobBlock] = []
    for block in blocks:
        block_id = block
        if isinstance(block, dict):
            block_id = block.get("blockId") or block.get("id") or block.get("blockNumber")
        normalised.append(BlobBlock(block_id=_normalise_block_id(block_id)))
    return normalised


def _content_settings_from_payload(payload: dict) -> Optional[ContentSettings]:
    content_type = payload.get("contentType")
    if not content_type:
        return None
    return ContentSettings(content_type=content_type)


@app.route(route="block-blob-uploader", methods=["POST"])
def block_blob_uploader(req: func.HttpRequest) -> func.HttpResponse:
    try:
        body = req.get_json()
    except ValueError:
        return func.HttpResponse(
            json.dumps({"error": "The request body must be valid JSON."}),
            status_code=400,
            mimetype="application/json",
        )

    action = (body.get("action") or "stage").lower()
    container_name = body.get("containerName")
    blob_name = body.get("blobName")

    if not container_name or not blob_name:
        return func.HttpResponse(
            json.dumps({"error": "containerName and blobName are required."}),
            status_code=400,
            mimetype="application/json",
        )

    try:
        blob_client = _get_blob_client(container_name, blob_name)
        logging.info(
            "Processing '%s' action for blob '%s/%s'.", action, container_name, blob_name
        )
        if action == "start":
            overwrite = bool(body.get("overwrite", False))
            if overwrite:
                try:
                    blob_client.delete_blob(delete_snapshots="include")
                except ResourceNotFoundError:
                    pass
            response_body = {
                "status": "ready",
                "blobUrl": blob_client.url,
                "recommendedBlockSize": RECOMMENDED_BLOCK_SIZE,
                "maxBlockSize": MAX_BLOCK_SIZE,
                "maxBlocks": MAX_BLOCKS_PER_BLOB,
            }
        elif action == "stage":
            chunk_bytes = _decode_chunk(body.get("chunkData") or body.get("data"))
            if len(chunk_bytes) > MAX_BLOCK_SIZE:
                raise ValueError(
                    f"Each block must be <= {MAX_BLOCK_SIZE} bytes; received {len(chunk_bytes)} bytes."
                )
            block_id = _get_block_id_from_payload(body)
            blob_client.stage_block(block_id=block_id, data=chunk_bytes)
            response_body = {
                "status": "staged",
                "blockId": block_id,
                "size": len(chunk_bytes),
            }
        elif action == "commit":
            block_list = _normalise_block_list(body.get("blockList") or body.get("blockIds"))
            if len(block_list) > MAX_BLOCKS_PER_BLOB:
                raise ValueError(
                    f"Too many blocks provided ({len(block_list)}). "
                    f"Maximum supported blocks is {MAX_BLOCKS_PER_BLOB}."
                )
            blob_client.commit_block_list(
                block_list,
                content_settings=_content_settings_from_payload(body),
                metadata=body.get("metadata"),
            )
            response_body = {"status": "committed", "blobUrl": blob_client.url}
        else:
            return func.HttpResponse(
                json.dumps({"error": f"Unsupported action '{action}'."}),
                status_code=400,
                mimetype="application/json",
            )

        return func.HttpResponse(
            json.dumps(response_body),
            status_code=200,
            mimetype="application/json",
        )
    except ValueError as exc:
        return func.HttpResponse(
            json.dumps({"error": str(exc)}),
            status_code=400,
            mimetype="application/json",
        )
    except Exception as exc:  # noqa: BLE001
        logging.exception("Large file upload failed.")
        return func.HttpResponse(
            json.dumps({"error": "Upload failed.", "details": str(exc)}),
            status_code=500,
            mimetype="application/json",
        )
