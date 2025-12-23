# Processing Large Files with Block Blobs

This Azure Function exposes a single HTTP endpoint (`/api/block-blob-uploader`) that helps Logic Apps (or any HTTP client) upload files larger than 100 MB to Azure Storage by using the block blob pattern. It provides a thin orchestration layer over the Azure Storage SDK so callers can stage chunks, commit them, and manage metadata without handling authentication or SDK plumbing on their own.

## What Has Been Implemented
- HTTP-triggered function registered at `block-blob-uploader` with function-level auth.
- Three actions (`start`, `stage`, and `commit`) that mirror the workflow required for large block blob uploads.
- Automatic container creation, optional overwrite support, and metadata/content-type handling.
- Server-side validation for chunk size (≤ 100 MB) and block counts (≤ 50,000).
- Helpful responses with the blob URL plus recommended block size settings for the caller.

## Prerequisites
1. Python 3.10+ and the Azure Functions Core Tools.
2. An Azure Storage account connection string configured via either:
   - `LargeFileStorageConnection`, or
   - `AzureWebJobsStorage` (fallback if the first is not provided).
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running Locally
1. Update `local.settings.json` with the storage connection string.
2. Start the Functions host:
   ```bash
   func start
   ```
3. Send HTTP POST requests to `http://localhost:7071/api/block-blob-uploader` with the JSON payloads described below.

## Request Workflow
The client typically issues three requests in sequence:

### 1. Start (optional but recommended)
Use this to create the container if needed and, optionally, delete an existing blob.

```json
{
  "action": "start",
  "containerName": "large-files",
  "blobName": "sample.dat",
  "overwrite": true
}
```

Response highlights include the blob URL, `recommendedBlockSize` (4 MB), `maxBlockSize`, and `maxBlocks`.

### 2. Stage Blocks
Send each chunk as a base64 string. You must provide either `blockId` (already base64) or `blockNumber` (integer/string that will be converted).

```json
{
  "action": "stage",
  "containerName": "large-files",
  "blobName": "sample.dat",
  "blockNumber": 1,
  "chunkData": "<base64-encoded bytes>"
}
```

Each chunk must be ≤ 100 MB. The response echoes the server-generated block ID and the byte length staged.

### 3. Commit Block List
After the final chunk, commit the ordered block list. Accepts either `blockList` (array of objects) or `blockIds` (array of strings).

```json
{
  "action": "commit",
  "containerName": "large-files",
  "blobName": "sample.dat",
  "contentType": "application/octet-stream",
  "metadata": {
    "source": "logic-app"
  },
  "blockList": [
    { "blockNumber": 1 },
    { "blockNumber": 2 }
  ]
}
```

The response confirms the commit and returns the blob URL.

## Error Handling
- Malformed JSON or missing required fields return HTTP 400 with an error description.
- Chunk sizes exceeding 100 MB or too many blocks (> 50,000) also return HTTP 400.
- Unexpected issues (e.g., storage outages) return HTTP 500 with a generic message and logged details.

With this helper endpoint, Logic Apps can reliably upload very large files without needing to manually call the Azure Storage REST API for each block.
