#!/usr/bin/env bash
set -euo pipefail

RG="${RG:-rg-logic-apps-demo-day7}"
NAMESPACE="${NAMESPACE:-x12kafka1767794837}"
EVENTHUB="${EVENTHUB:-x12-messages}"
SEND_RULE="${SEND_RULE:-send-only}"
PAYLOAD_FILE="${PAYLOAD_FILE:-${1:-}}"

if ! command -v az >/dev/null 2>&1; then
  echo "az CLI is required." >&2
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required." >&2
  exit 1
fi

if ! az account show >/dev/null 2>&1; then
  echo "az CLI is not logged in. Run: az login" >&2
  exit 1
fi

if ! az eventhubs eventhub authorization-rule show \
  -g "$RG" --namespace-name "$NAMESPACE" --eventhub-name "$EVENTHUB" --name "$SEND_RULE" \
  >/dev/null 2>&1; then
  az eventhubs eventhub authorization-rule create \
    -g "$RG" --namespace-name "$NAMESPACE" --eventhub-name "$EVENTHUB" --name "$SEND_RULE" \
    --rights Send >/dev/null
fi

CONN=$(az eventhubs eventhub authorization-rule keys list \
  -g "$RG" --namespace-name "$NAMESPACE" --eventhub-name "$EVENTHUB" --name "$SEND_RULE" \
  --query primaryConnectionString -o tsv)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${VENV_DIR:-$SCRIPT_DIR/.venv}"

if [[ ! -d "$VENV_DIR" ]]; then
  python3 -m venv "$VENV_DIR"
  "$VENV_DIR/bin/pip" install -q azure-eventhub
fi

if [[ -n "$PAYLOAD_FILE" ]]; then
  if [[ ! -f "$PAYLOAD_FILE" ]]; then
    echo "Payload file not found: $PAYLOAD_FILE" >&2
    exit 1
  fi
  PAYLOAD="$(cat "$PAYLOAD_FILE")"
else
  PAYLOAD='{"x12":"ISA*00*          *00*          *ZZ*CONTOSORETAIL  *ZZ*FABRIKAM       *210101*1253*U*00401*000000001*0*P*:~GS*PO*CONTOSORETAIL*FABRIKAM*20210101*1253*1*X*004010~ST*850*0001~BEG*00*SA*PO12345**20250115~N1*BY*CONTOSO RETAIL*92*12345~N1*ST*FABRIKAM SUPPLIES*92*67890~R4*5*LOC1*Seattle*WA*US~SE*6*0001~GE*1*1~IEA*1*000000001~","client":"acme","transactionSet":"850"}'
fi

SEND_CONN="$CONN" PAYLOAD="$PAYLOAD" "$VENV_DIR/bin/python" - <<'PY'
import os
from azure.eventhub import EventHubProducerClient, EventData

conn = os.environ["SEND_CONN"]
payload = os.environ["PAYLOAD"]

producer = EventHubProducerClient.from_connection_string(conn)
with producer:
    batch = producer.create_batch()
    batch.add(EventData(payload))
    producer.send_batch(batch)
print("Event Hub send status: 201")
PY

echo "Sent message to $EVENTHUB in $NAMESPACE."
