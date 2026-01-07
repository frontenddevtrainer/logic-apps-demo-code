# cURL Examples: X12 Mapping

Replace the placeholders before running:
- `LOGIC_APP_URL`: your Logic App HTTP trigger URL
- `FUNCTION_URL`: your Function endpoint (e.g. `https://<app>.azurewebsites.net/api/x12-map`)

## 1) Logic App: standard mapping (client + transaction set)
```bash
LOGIC_APP_URL="<logic-app-url>"

curl -X POST "$LOGIC_APP_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "x12": "ISA*00*          *00*          *ZZ*CONTOSORETAIL  *ZZ*FABRIKAM       *210101*1253*U*00401*000000001*0*P*:~GS*PO*CONTOSORETAIL*FABRIKAM*20210101*1253*1*X*004010~ST*850*0001~BEG*00*SA*PO12345**20250115~N1*BY*CONTOSO RETAIL*92*12345~N1*ST*FABRIKAM SUPPLIES*92*67890~SE*5*0001~GE*1*1~IEA*1*000000001~",
    "client": "acme",
    "transactionSet": "850"
  }'
```

## 2) Logic App: non-standard mapping (custom R4 rule)
```bash
LOGIC_APP_URL="<logic-app-url>"

curl -X POST "$LOGIC_APP_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "x12": "ISA*00*          *00*          *ZZ*CONTOSORETAIL  *ZZ*FABRIKAM       *210101*1253*U*00401*000000001*0*P*:~GS*PO*CONTOSORETAIL*FABRIKAM*20210101*1253*1*X*004010~ST*850*0001~BEG*00*SA*PO12345**20250115~N1*BY*CONTOSO RETAIL*92*12345~N1*ST*FABRIKAM SUPPLIES*92*67890~R4*5*LOC1*Seattle*WA*US~SE*6*0001~GE*1*1~IEA*1*000000001~",
    "client": "acme",
    "transactionSet": "850"
  }'
```

## 3) Function: includeMeta response
```bash
FUNCTION_URL="<function-url>"

curl -X POST "$FUNCTION_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "x12": "ISA*00*          *00*          *ZZ*SENDER*ZZ*RECEIVER*210101*1253*U*00401*000000001*0*P*:~GS*PO*SENDER*RECEIVER*20210101*1253*1*X*004010~ST*850*0001~BEG*00*SA*PO12345**20250115~SE*3*0001~GE*1*1~IEA*1*000000001~",
    "mappingPath": "mapping/standards/850.json",
    "includeMeta": true
  }'
```

## 4) Function: mappingPath override
```bash
FUNCTION_URL="<function-url>"

curl -X POST "$FUNCTION_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "x12": "ISA*00*          *00*          *ZZ*SENDER*ZZ*RECEIVER*210101*1253*U*00401*000000001*0*P*:~GS*PO*SENDER*RECEIVER*20210101*1253*1*X*004010~ST*850*0001~BEG*00*SA*PO12345**20250115~SE*3*0001~GE*1*1~IEA*1*000000001~",
    "mappingPath": "mapping/standards/850.json"
  }'
```

## 5) Function: mappingBlobUrl (SAS)
```bash
FUNCTION_URL="<function-url>"
MAPPING_BLOB_URL="https://<account>.blob.core.windows.net/x12-mappings/mapping/clients/acme/850.json?<sas>"

curl -X POST "$FUNCTION_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "x12": "<x12 text>",
    "mappingBlobUrl": "'"$MAPPING_BLOB_URL"'"
  }'
```
