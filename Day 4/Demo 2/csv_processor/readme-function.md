# CSV Processor Azure Function

This function exposes an anonymous HTTP endpoint that downloads a CSV file from Azure Blob Storage, logs each row, and returns the number of processed rows.

## Prerequisites
- Python 3.10+
- [Azure Functions Core Tools](https://learn.microsoft.com/azure/azure-functions/functions-run-local)
- Azure Storage account connection string with access to the CSV blob
- `AzureWebJobsStorage` environment variable set to that connection string

## Install Dependencies
```bash
cd "Day 4/Demo 2/csv_processor"
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
```

## Run Locally
```bash
func start
```
The function host listens on `http://localhost:7071`. The CSV processor endpoint is `POST http://localhost:7071/api/csv-processor`.

## Testing with Postman
1. Open Postman and create a new `POST` request to `http://localhost:7071/api/csv-processor`.
2. Set the `Content-Type` header to `application/json`.
3. In the **Body** tab, choose **raw** and provide JSON such as:
   ```json
   {
     "blobUrl": "https://<storage-account>.blob.core.windows.net/<container>/<file>.csv?sv=...&sig=..."
   }
   ```
4. Send the request. A successful response returns status `200` with the row count, e.g. `CSV processed successfully. Rows: 42`.
5. Inspect the Azure Functions host console for log output of each CSV row.

## Notes
- **Authentication options**
  - **SAS URL**: Add a SAS token (with at least `sp=r`) directly to `blobUrl`. The function detects the `sig` parameter and uses the SAS for authentication.
  - **Shared key**: Omit the SAS from `blobUrl` and ensure `AzureWebJobsStorage` is configured with the storage account connection string. The function will sign requests using this account key.
  - If neither a SAS nor `AzureWebJobsStorage` credential is present, the request fails with HTTP `500`.
- Keep SAS tokens URL-encoded and unexpired (`st`/`se` times). Any copy/paste changes usually result in `InvalidAuthenticationInfo`.
- Errors (missing `blobUrl`, invalid JSON, download failures) are surfaced via HTTP `400`/`500` and logged in the Functions console.
