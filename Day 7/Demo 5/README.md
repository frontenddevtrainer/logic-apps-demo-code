# Demo 5: X12 to JSON Mapping with Azure Functions and Blob Config

## Overview
This demo adds a flexible X12 to JSON mapping endpoint backed by Azure Functions. Mapping files live in Azure Blob Storage so you can update client-specific rules without redeploying the function.

The function:
- Accepts raw X12 text or pre-parsed segments.
- Locates a mapping file by client + transaction set, explicit blob path, or a SAS URL.
- Loads the mapping (including extends/overrides) from Blob Storage.
- Applies the mapping logic from the Mapping Logic folder to produce JSON output.

## Folder Layout
- `Day 7/Demo 5/x12-mapping-function`: Azure Functions app
- `Day 7/Demo 5/x12-mapping-function/mapping_logic/mapper.py`: copy of `Mapping Logic/src/mapper.py`
- `Day 7/Demo 5/LogicApp_X12_Map_to_PostgreSQL.json`: Logic App workflow (HTTP trigger → Function → HTTP response)
- `Day 7/Demo 5/curl-examples.md`: ready-to-run cURL requests for the Logic App and Function

## Prerequisites
- Python 3.10+
- Azure Functions Core Tools
- Azure Storage account
- Mapping files from `Mapping Logic/mapping`

## Setup
1. Create a container for mappings (example: `x12-mappings`).
2. Upload the mapping folder structure to Blob Storage.
   - Upload `Mapping Logic/mapping` so the container has paths like:
     - `mapping/standards/850.json`
     - `mapping/clients/acme/850.json`
3. Configure local settings for the Function app:
   - `Day 7/Demo 5/x12-mapping-function/local.settings.json`
   - Update `AzureWebJobsStorage`, `MAPPING_CONTAINER`, and `MAPPING_ROOT` as needed.

Optional upload command:
```bash
az storage blob upload-batch \
  --account-name <storage-account> \
  --destination x12-mappings \
  --source "Mapping Logic/mapping" \
  --destination-path mapping
```

## Running Locally
```bash
cd "Day 7/Demo 5/x12-mapping-function"
pip install -r requirements.txt
func start
```

## Logic App Orchestration (Optional)
The Logic App in `Day 7/Demo 5/LogicApp_X12_Map_to_PostgreSQL.json` implements:
```
[HTTP Request] → [Call x12-map Function] → [HTTP Response]
```

### Configure the Logic App
1. Create a Consumption Logic App and import `Day 7/Demo 5/LogicApp_X12_Map_to_PostgreSQL.json`.
2. Set the `functionUrl` parameter to your Function endpoint (include the function key if required).
3. No managed connections are required for this pass-through workflow.

See `Day 7/Demo 5/curl-examples.md` for ready-to-run Logic App and Function requests.

## Request Payload Options
Required (choose one):
- `x12`: raw X12 text
- `segments`: pre-parsed segments array

Mapping selection (choose one):
- `client` + `transactionSet`
- `mappingPath` (relative blob path)
- `mappingBlobUrl` (full SAS URL to mapping JSON)

Optional:
- `mappingContainer`: overrides `MAPPING_CONTAINER`
- `mappingRoot`: overrides `MAPPING_ROOT`
- `elementSeparator`, `segmentSeparator`, `componentSeparator`: override delimiters
- `includeMeta`: return mapping path and segment count

Delimiter detection:
- If delimiters are not supplied, the function tries to detect them from the ISA segment.

## Example: Client + Transaction Set
```bash
curl -X POST "http://localhost:7071/api/x12-map" \
  -H "Content-Type: application/json" \
  --data "$(jq -n --rawfile x12 ../../Mapping\ Logic/samples/850_acme.edi '{x12: $x12, client: "acme", transactionSet: "850"}')"
```

## Example: Explicit Mapping Path
```json
{
  "x12": "ISA*00* *00* *ZZ*SENDER*ZZ*RECEIVER*210101*1253*U*00401*000000001*0*P*:~GS*PO*SENDER*RECEIVER*20210101*1253*1*X*004010~ST*850*0001~BEG*00*SA*PO12345**20250115~SE*3*0001~GE*1*1~IEA*1*000000001~",
  "mappingPath": "mapping/standards/850.json"
}
```

## Example: SAS URL to Mapping
```json
{
  "x12": "<x12 text>",
  "mappingBlobUrl": "https://<account>.blob.core.windows.net/x12-mappings/mapping/clients/acme/850.json?<sas>",
  "includeMeta": true
}
```

## Response
Default response is the mapped JSON output. If `includeMeta` is true, the response is:
```json
{
  "mappingPath": "mapping/clients/acme/850.json",
  "segmentCount": 18,
  "output": { "purchaseOrder": { "number": "PO12345" } }
}
```

## Notes
- Mapping extends/overrides resolve relative to the mapping file path in Blob Storage.
- Update the mapping files in Blob Storage to change behavior without redeploying the function.
