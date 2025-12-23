# Document Processing Pipeline

This solution contains two coordinated Azure resources that together provide automatic PDF ingestion and processing:

1. **Logic App Standard** (in `PDFHandsOn/PDFUpload`) – polls the `incoming` container for new PDFs, invokes the PDF processor function, and sends completion notifications.
2. **Azure Function App** (in `PDFProcessor`) – receives the blob context, runs OCR via Azure AI Document Intelligence, writes extracted text to the `processed` container, archives the original PDF to the `archive` container with the Cool tier, and returns metadata for the notification.

## Repository layout

| Path | Description |
| --- | --- |
| `PDFProcessor/` | Python Azure Function with the `pdf_processor` HTTP trigger. |
| `PDFHandsOn/PDFUpload/` | Logic App Standard workflow project; `PDF/workflow.json` holds the workflow definition. |

## Azure Function configuration

Environment settings required by `PDFProcessor/function_app.py`:

| Setting | Description |
| --- | --- |
| `AZURE_STORAGE_CONNECTION_STRING` | Connection string to the storage account hosting the `incoming`, `processed`, and `archive` containers. |
| `DOCUMENT_INTELLIGENCE_ENDPOINT` | Endpoint URL of the Azure AI Document Intelligence resource. |
| `DOCUMENT_INTELLIGENCE_KEY` | Key for the Document Intelligence resource. |
| `INCOMING_CONTAINER` | Optional override; defaults to `incoming`. |
| `PROCESSED_CONTAINER` | Optional override; defaults to `processed`. |
| `ARCHIVE_CONTAINER` | Optional override; defaults to `archive`. |

Dependencies are listed in `PDFProcessor/requirements.txt` and include `azure-ai-formrecognizer` and `azure-storage-blob`.

## Logic App workflow parameters

`PDFHandsOn/PDFUpload/PDF/workflow.json` defines parameters that must be populated after deployment:

| Parameter | Description |
| --- | --- |
| `$connections` | Logic App managed connections for Azure Blob Storage (`azureblob`) and Office 365 (`office365`). Configure via the portal or ARM template. |
| `incomingContainer` | Name of the watched container; defaults to `incoming`. |
| `pdfProcessorFunctionUrl` | HTTPS URL of the deployed `pdf_processor` function. |
| `pdfProcessorAudience` | App ID URI or resource URL used as the AAD audience (example: `https://<functionapp>.azurewebsites.net`). |
| `notificationEmail` | Email address that receives completion notifications. |

## Deployment flow

1. **Provision resources:** storage account with `incoming`, `processed`, `archive` containers; Azure AI Document Intelligence; Function App; Logic App Standard; Office 365 connection.
2. **Deploy Azure Function:** `func azure functionapp publish <app-name>` or CI/CD. Provide the configuration settings above.
3. **Enable managed identities + auth:** enable a system-assigned managed identity on the Logic App Standard, then enable Azure AD authentication on the Function App and require login. Grant the Logic App managed identity access to the Function App (App Role or Allowed callers).
4. **Deploy Logic App workflow:** `func azure functionapp publish` (for Workflow project) or use Azure portal/VS Code. Bind `$connections` to the storage and email connectors, then set the workflow parameters.
5. **Test end-to-end:** upload a sample `.pdf` into the `incoming` container. The Logic App should trigger, call the function, place OCR text in `processed/<file>.txt`, move the original to `archive/<file>.pdf` on the Cool tier, and send the notification email.

## Local testing tips

- Use the Storage Emulator/Azurite locally by pointing `AzureWebJobsStorage` and `AZURE_STORAGE_CONNECTION_STRING` to your emulator connection string.
- You can invoke the function locally with `func start` and send a request such as:

```bash
curl -X POST http://localhost:7071/api/pdf_processor \
  -H "Content-Type: application/json" \
  -d '{"blobName": "sample.pdf"}'
```

Ensure the referenced blob exists in the configured storage account and container before issuing the request.

## Security best practices

- Avoid function keys in query strings; use Azure AD auth with the Logic App managed identity.
- Store `pdfProcessorFunctionUrl` and `pdfProcessorAudience` in app settings or Key Vault references, not in workflow JSON.
- Prefer managed identities for Storage and Document Intelligence where possible; only keep secrets in app settings for local development.
