# Demo 4: Complete B2B Workflow - Receive X12 → Process → Send 997 → Forward JSON

## Overview
This is a production-ready end-to-end B2B integration workflow that combines all previous demos into a complete automated solution for processing X12 EDI messages.

## Files in This Demo

### Logic App Workflow
- **[LogicApp_Complete_B2B_Workflow.json](LogicApp_Complete_B2B_Workflow.json)** - Complete workflow definition

## Workflow Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     COMPLETE B2B WORKFLOW                        │
└─────────────────────────────────────────────────────────────────┘

1. Monitor Blob Storage (/incoming-x12)
          ↓
2. Get X12 File Content
          ↓
3. Decode X12 850 → JSON
          ↓
4. Transform to Internal Order Format
          ↓
5. Save Order JSON (/processed-orders)
          ↓
6. Generate 997 Acknowledgment
          ↓
7. Save 997 (/acknowledgments-997)
          ↓
8. Send 997 to Trading Partner (HTTP)
          ↓
9. Forward Order JSON to Internal API
          ↓
10. Create Processing Summary (/processing-logs)
          ↓
11. Archive Original File (/archive-x12)
          ↓
12. Delete Original from Incoming
```

## Required Setup

### 1. Azure Blob Storage Setup

Create the following folder structure in your storage account:

```
storage-account/
├── incoming-x12/          # Drop X12 files here (monitored by trigger)
├── processed-orders/      # Transformed JSON orders
├── acknowledgments-997/   # Generated 997 acknowledgments
├── processing-logs/       # Workflow execution summaries
└── archive-x12/          # Archived original X12 files
```

#### Creating Folders via Azure Portal:
1. Open Storage Account → Containers
2. Select your container
3. Click **+ Add Directory** for each folder above

### 2. Integration Account Setup

#### Upload Schemas:
1. `X12_00401_850.xsd` - For decoding 850 Purchase Orders
2. `X12_00401_997.xsd` - For encoding 997 Acknowledgments

#### Create X12 Agreements:
1. **Receive Agreement**: `ContosoRetail_To_FabrikamSupplies_X12`
   - For decoding incoming 850s

2. **Send Agreement**: `FabrikamSupplies_To_ContosoRetail_X12_997`
   - For encoding outbound 997s

### 3. Connection Configuration

#### Azure Blob Storage Connection
Update connection details in parameters:
```json
"azureblob": {
  "connectionId": "/subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.Web/connections/azureblob-1",
  "connectionName": "azureblob-1"
}
```

#### X12 Connection
Update X12 connector connection as in previous demos

### 4. API Endpoints Configuration

#### Trading Partner EDI Endpoint (for sending 997)
Update in `Send_997_via_HTTP` action:
```json
"uri": "https://partner-edi-endpoint.example.com/acknowledgments"
```

#### Internal Order Management API
Update in `Forward_JSON_to_API` action:
```json
"uri": "https://your-order-api.example.com/api/orders"
```

Add API key parameter:
```json
"orderApiKey": {
  "type": "String",
  "value": "your-actual-api-key"
}
```

## Testing the Demo

### Test Data Files
Located in `../Sample Data/`:
- **sample_x12_850_purchase_order.x12** - Full X12 850 with 3 line items
- **sample_x12_850_simple.x12** - Simple X12 850 for basic testing

### How to Test

#### Step 1: Deploy the Logic App
1. Import workflow JSON to Azure Logic Apps
2. Update all connection references
3. Configure API endpoints
4. Save and enable the Logic App

#### Step 2: Upload Test File
1. Navigate to Storage Account → Container
2. Go to `/incoming-x12` folder
3. Upload `sample_x12_850_purchase_order.x12`
4. Wait up to 3 minutes for trigger to fire

#### Step 3: Monitor Execution
1. Open Logic App in Azure Portal
2. View **Run History**
3. Click on the run to see detailed execution
4. Verify all actions succeeded

#### Step 4: Verify Outputs
Check the following folders in Blob Storage:

1. **/processed-orders/** - Should contain:
   ```
   ORDER_PO-2023-12345_20231223-143000_{guid}.json
   ```

2. **/acknowledgments-997/** - Should contain:
   ```
   997_ACK_000000001_20231223-143001.x12
   ```

3. **/processing-logs/** - Should contain:
   ```
   SUMMARY_{guid}_20231223-143002.json
   ```

4. **/archive-x12/** - Should contain original file

5. **/incoming-x12/** - Should be empty (file deleted)

## Workflow Actions Deep Dive

### Variables Initialized
```json
{
  "correlationId": "{guid}",      // Tracks request through entire workflow
  "processingStatus": "started"   // Workflow status tracking
}
```

### Step-by-Step Breakdown

| Step | Action | Description | Output |
|------|--------|-------------|--------|
| 1 | **Blob Trigger** | Monitors /incoming-x12 every 3 min | File metadata |
| 2 | **Get Blob Content** | Retrieves X12 file content | Raw X12 string |
| 3 | **Decode X12** | Parses EDI to JSON using agreement | Decoded JSON |
| 4 | **Extract Control Numbers** | Gets ISA13, GS06, ST02 for tracking | Control metadata |
| 5 | **Transform Order** | Maps to internal order format | Order JSON |
| 6 | **Save Order JSON** | Writes to /processed-orders | Blob path |
| 7 | **Build 997 XML** | Creates acknowledgment structure | 997 XML |
| 8 | **Encode 997** | Converts XML to X12 format | 997 X12 string |
| 9 | **Save 997** | Writes to /acknowledgments-997 | Blob path |
| 10 | **Send 997** | HTTP POST to trading partner | HTTP status |
| 11 | **Forward Order** | HTTP POST to internal API | API response |
| 12 | **Create Summary** | Builds execution log | Summary JSON |
| 13 | **Save Summary** | Writes to /processing-logs | Blob path |
| 14 | **Archive File** | Copies to /archive-x12 | Archive path |
| 15 | **Delete Original** | Removes from /incoming-x12 | Success |

### Processing Summary Structure

The workflow creates a comprehensive log:

```json
{
  "workflowStatus": "completed",
  "correlationId": "{guid}",
  "timestamp": "2023-12-23T14:30:00Z",
  "processedFile": "order_20231223.x12",
  "steps": {
    "1_received": {
      "status": "success",
      "description": "X12 message received from blob storage",
      "fileName": "order_20231223.x12"
    },
    "2_decoded": {
      "status": "success",
      "description": "X12 850 message decoded to JSON",
      "orderId": "PO-2023-12345"
    },
    // ... all 8 steps with status and details
  },
  "order": { /* complete order JSON */ }
}
```

## Monitoring & Observability

### Key Metrics to Track
1. **Processing Time** - End-to-end duration
2. **Success Rate** - % of files processed successfully
3. **997 Delivery Rate** - % of acknowledgments sent
4. **API Success Rate** - % of successful API posts
5. **Error Rate** - Failed workflows

### Application Insights Integration
Add diagnostic settings to track:
- Workflow runs
- Action durations
- Failures and exceptions
- Custom telemetry with correlation IDs

### Alerts to Configure
1. **Workflow Failures** - Alert on any run failure
2. **997 Send Failures** - Partner not receiving acknowledgments
3. **API Failures** - Orders not reaching internal system
4. **Long Processing Times** - Performance degradation
5. **No Files Processed** - Check if integration is down

## Error Handling Strategies

### 1. Decode Failures
```
If X12 decode fails:
  → Save error details to /processing-logs
  → Move file to /errors folder
  → Send alert to support team
  → Do NOT send 997 (invalid message)
```

### 2. 997 Send Failures
```
If 997 HTTP POST fails:
  → Retry with exponential backoff (3 attempts)
  → Save 997 to /acknowledgments-997 anyway
  → Log failure for manual retry
  → Continue with order processing
```

### 3. API Failures
```
If internal API fails:
  → Retry with exponential backoff
  → Save order to /failed-api-posts
  → Send alert for manual intervention
  → 997 already sent, so acknowledge issue to partner
```

## Production Considerations

### Security
1. **Store secrets in Azure Key Vault**
   - API keys
   - Connection strings
   - Partner credentials

2. **Use Managed Identity**
   - For blob storage access
   - For Key Vault access
   - For API authentication

3. **Enable HTTPS only**
   - All HTTP actions
   - Blob storage
   - API endpoints

### Performance
1. **Trigger Optimization**
   - Adjust polling interval based on volume
   - Use `maxFileCount` to control batch size
   - Consider Event Grid trigger for large volumes

2. **Parallel Processing**
   - `splitOn` enabled for batch processing
   - Each file processed in separate run

3. **Throttling**
   - Configure retry policies
   - Handle 429 responses
   - Implement exponential backoff

### Compliance & Audit
1. **Retention Policies**
   - Keep original X12 for 7 years (typical EDI requirement)
   - Archive 997s for audit
   - Maintain processing logs

2. **Audit Trail**
   - Correlation IDs link all related records
   - Timestamps on all operations
   - Control numbers track EDI compliance

## Testing Checklist

### Before Go-Live
- [ ] All blob storage folders created
- [ ] Integration Account configured with schemas and agreements
- [ ] Connections tested and working
- [ ] API endpoints configured and accessible
- [ ] Trading partner endpoint accepts 997s
- [ ] Test files processed successfully
- [ ] Monitoring and alerts configured
- [ ] Error handling tested with invalid files
- [ ] Performance tested with expected volume
- [ ] Security review completed
- [ ] Documentation updated
- [ ] Runbook created for support team

## Troubleshooting

### Workflow Not Triggering
1. Check blob trigger is enabled
2. Verify polling interval is appropriate
3. Ensure files are in correct folder: `/incoming-x12`
4. Check blob connection is valid
5. Review run history for trigger failures

### Files Stuck in Processing
1. Check for long-running actions
2. Review timeout settings
3. Look for connection timeouts
4. Check API response times
5. Verify no infinite loops

### 997 Not Sent
1. Verify 997 encoding succeeded
2. Check HTTP endpoint is reachable
3. Review HTTP action logs
4. Validate 997 content
5. Check partner firewall/IP allowlist

### Orders Not in API
1. Check API endpoint configuration
2. Verify API key is valid
3. Review API action status
4. Check API logs for errors
5. Validate JSON structure

## File Naming Conventions

### Processed Orders
```
ORDER_{orderId}_{timestamp}_{correlationId}.json
Example: ORDER_PO-2023-12345_20231223-143000_a1b2c3d4.json
```

### 997 Acknowledgments
```
997_ACK_{interchangeControlNumber}_{timestamp}.x12
Example: 997_ACK_000000001_20231223-143001.x12
```

### Processing Summaries
```
SUMMARY_{correlationId}_{timestamp}.json
Example: SUMMARY_a1b2c3d4_20231223-143002.json
```

### Archived Files
```
{original-filename}
Preserves original name for traceability
```

## Integration Patterns

This workflow demonstrates:
1. **Event-Driven Architecture** - Blob trigger initiates processing
2. **ETL Pattern** - Extract (decode), Transform (map), Load (API)
3. **Audit Logging** - Complete tracking of all operations
4. **Error Handling** - Graceful degradation and retry logic
5. **Idempotency** - Correlation IDs prevent duplicate processing
6. **Archive Pattern** - Original data preserved for compliance

## Next Steps

### Enhancements to Consider
1. **Add validation rules** - Business logic validation before API
2. **Implement dead letter queue** - For permanently failed messages
3. **Add duplicate detection** - Check if order already processed
4. **Enable batching** - Process multiple files in single run
5. **Add notifications** - Email/Teams alerts on errors
6. **Integrate with Service Bus** - For reliable messaging
7. **Add partner-specific routing** - Different endpoints per partner
8. **Implement 999** - Implementation Acknowledgment for HIPAA

## Additional Resources

- [Logic Apps Best Practices](https://learn.microsoft.com/en-us/azure/logic-apps/logic-apps-best-practices)
- [B2B Enterprise Integration](https://learn.microsoft.com/en-us/azure/logic-apps/logic-apps-enterprise-integration-overview)
- [EDI Standards and Compliance](https://www.edibasics.com/)
