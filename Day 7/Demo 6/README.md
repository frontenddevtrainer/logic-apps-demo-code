# Demo 6: Kafka Trigger (Event Hubs) → X12 Mapping Function

## Overview
This demo replaces the HTTP trigger from Demo 5 with a Kafka-based trigger backed by Azure Event Hubs (Kafka endpoint enabled). Messages published to the Kafka topic are picked up by a Logic App, passed to the `x12-map` Function, and the mapped JSON is emitted in the run history.

Architecture flow:
```
[Kafka Producer] → [Event Hubs (Kafka)] → [Logic App Trigger] → [x12-map Function] → [Compose Output]
```

## Azure Resources (Created)
- Resource group: `rg-logic-apps-demo-day7`
- Event Hubs namespace: `x12kafka1767794837` (Standard, 1 TU, Kafka enabled)
- Event Hub (Kafka topic): `x12-messages`
- Consumer group: `logicapp`

Fetch the Event Hubs connection string:
```bash
az eventhubs namespace authorization-rule keys list \
  -g rg-logic-apps-demo-day7 \
  --namespace-name x12kafka1767794837 \
  --name RootManageSharedAccessKey \
  --query primaryConnectionString -o tsv
```

Kafka bootstrap server:
```
x12kafka1767794837.servicebus.windows.net:9093
```

## Logic App
Definition file:
- `Day 7/Demo 6/LogicApp_X12_Map_from_Kafka.json`

What it does:
- Trigger: Event Hubs (polls for events).
- Decode: `ContentData` (base64) → JSON.
- Call Function: `https://x12-mapping.azurewebsites.net/api/x12-map`.
- Output: Compose action shows mapped JSON in run history.

### Configure the Logic App
1. Create a Consumption Logic App and import `Day 7/Demo 6/LogicApp_X12_Map_from_Kafka.json`.
2. Create an Event Hubs connection (connector name: `eventhubs`).
3. Set parameters:
   - `eventHubName`: `x12-messages`
   - `consumerGroup`: `logicapp`
   - `functionUrl`: your Function URL (include key if required)

Note: The trigger uses `@json(base64ToString(triggerBody()?['ContentData']))`. If your connector returns a different field, update `Parse_Kafka_Message` accordingly.

## Kafka Producer Example (kcat)
Install `kcat` and run:
```bash
BOOTSTRAP_SERVER="x12kafka1767794837.servicebus.windows.net:9093"
EVENTHUB_CONN_STRING="<event-hubs-connection-string>"
TOPIC="x12-messages"

kcat -b "$BOOTSTRAP_SERVER" \
  -X security.protocol=SASL_SSL \
  -X sasl.mechanism=PLAIN \
  -X sasl.username='$ConnectionString' \
  -X sasl.password="$EVENTHUB_CONN_STRING" \
  -t "$TOPIC" \
  -P
```
Paste this JSON message and press Enter:
```json
{
  "x12": "ISA*00*          *00*          *ZZ*CONTOSORETAIL  *ZZ*FABRIKAM       *210101*1253*U*00401*000000001*0*P*:~GS*PO*CONTOSORETAIL*FABRIKAM*20210101*1253*1*X*004010~ST*850*0001~BEG*00*SA*PO12345**20250115~N1*BY*CONTOSO RETAIL*92*12345~N1*ST*FABRIKAM SUPPLIES*92*67890~R4*5*LOC1*Seattle*WA*US~SE*6*0001~GE*1*1~IEA*1*000000001~",
  "client": "acme",
  "transactionSet": "850"
  }
```

## Scripted Demo Sender
Use the helper script to send a test message without installing Kafka tools:
```bash
./Day\ 7/Demo\ 6/run-demo-event.sh
```

Optional overrides:
```bash
RG=rg-logic-apps-demo-day7 \
NAMESPACE=x12kafka1767794837 \
EVENTHUB=x12-messages \
SEND_RULE=send-only \
./Day\ 7/Demo\ 6/run-demo-event.sh
```

Custom payload file:
```bash
./Day\ 7/Demo\ 6/run-demo-event.sh ./path/to/payload.json
```

## Kafka Producer Example (kafka-console-producer)
```bash
export BOOTSTRAP_SERVER="x12kafka1767794837.servicebus.windows.net:9093"
export EVENTHUB_CONN_STRING="<event-hubs-connection-string>"

kafka-console-producer \
  --broker-list "$BOOTSTRAP_SERVER" \
  --topic x12-messages \
  --producer-property security.protocol=SASL_SSL \
  --producer-property sasl.mechanism=PLAIN \
  --producer-property sasl.jaas.config='org.apache.kafka.common.security.plain.PlainLoginModule required username="$ConnectionString" password="$EVENTHUB_CONN_STRING";'
```

## Expected Output
The Logic App run history shows a `Compose_Mapped_Output` action containing the mapped JSON from the Function.
