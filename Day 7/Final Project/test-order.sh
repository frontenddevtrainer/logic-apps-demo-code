#!/usr/bin/env bash
#
# Test script for Final Project: X12 850 Order Processing System
#
# Sends test X12 850 orders to the deployed Function App or Logic App
#
# Usage:
#   ./test-order.sh                           # Send default test order
#   ./test-order.sh ./custom-payload.json     # Send custom payload
#   ./test-order.sh --logic-app               # Send to Logic App instead of Function
#   ./test-order.sh --mapping-only            # Test X12 mapping only (no storage)
#
set -euo pipefail

# =============================================================================
# Configuration
# =============================================================================
FUNCTION_APP="${FUNCTION_APP:-}"
FUNCTION_URL="${FUNCTION_URL:-}"
LOGIC_APP_URL="${LOGIC_APP_URL:-}"
PAYLOAD_FILE=""
USE_LOGIC_APP=false
MAPPING_ONLY=false

# =============================================================================
# Sample X12 850 Messages
# =============================================================================
DEFAULT_PAYLOAD='{
  "x12": "ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       *240115*1030*U*00401*000000001*0*P*:~GS*PO*SENDER*RECEIVER*20240115*1030*1*X*004010~ST*850*0001~BEG*00*SA*PO-2024-001**20240115~CUR*BY*USD~N1*BY*Acme Corporation*92*ACME-001~N3*100 Main Street*Suite 500~N4*Seattle*WA*98101*US~N1*ST*Acme Warehouse*92*WH-001~N3*200 Distribution Way~N4*Portland*OR*97201*US~PO1*001*10*EA*29.99*PE*VP*MOUSE-W100~PID*F****Wireless Mouse - Black~PO1*002*5*EA*49.99*PE*VP*KB-USB200~PID*F****USB Keyboard - Full Size~PO1*003*2*EA*199.99*PE*VP*MON-24HD~PID*F****24-inch HD Monitor~CTT*3*17~AMT*TT*849.83~SE*18*0001~GE*1*1~IEA*1*000000001~",
  "transactionSet": "850"
}'

MINIMAL_PAYLOAD='{
  "x12": "ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       *240115*1030*U*00401*000000001*0*P*:~GS*PO*SENDER*RECEIVER*20240115*1030*1*X*004010~ST*850*0001~BEG*00*NE*PO-MIN-001**20240115~N1*BY*Quick Buyer Inc*92*QB-001~PO1*001*25*EA*15.00**VP*WIDGET-001~CTT*1*25~SE*6*0001~GE*1*1~IEA*1*000000001~",
  "transactionSet": "850"
}'

BULK_PAYLOAD='{
  "x12": "ISA*00*          *00*          *ZZ*BIGORDER       *ZZ*SUPPLIER       *240115*1400*U*00401*000000002*0*P*:~GS*PO*BIGORDER*SUPPLIER*20240115*1400*2*X*004010~ST*850*0002~BEG*00*SA*PO-BULK-2024-001**20240115~CUR*BY*USD~N1*BY*Enterprise Corp*92*ENT-001~N3*500 Corporate Blvd~N4*Chicago*IL*60601*US~PO1*001*100*EA*5.99*PE*VP*CABLE-HDMI-6FT~PID*F****HDMI Cable 6 Foot~PO1*002*200*EA*3.49*PE*VP*CABLE-USB-C-3FT~PID*F****USB-C Cable 3 Foot~PO1*003*50*EA*12.99*PE*VP*ADAPTER-USBC-HDMI~PID*F****USB-C to HDMI Adapter~CTT*3*350~AMT*TT*1946.50~SE*14*0002~GE*1*2~IEA*1*000000002~",
  "transactionSet": "850"
}'

# =============================================================================
# Helper Functions
# =============================================================================
log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

error() {
  echo "[ERROR] $*" >&2
  exit 1
}

usage() {
  cat <<EOF
Usage: $0 [OPTIONS] [PAYLOAD_FILE]

Options:
  --function-app NAME    Function App name (or set FUNCTION_APP env var)
  --function-url URL     Direct Function URL (or set FUNCTION_URL env var)
  --logic-app-url URL    Logic App URL (or set LOGIC_APP_URL env var)
  --logic-app            Send to Logic App instead of Function
  --mapping-only         Test X12 mapping only (no storage)
  --minimal              Use minimal test payload
  --bulk                 Use bulk order test payload
  -h, --help             Show this help

Examples:
  # Test with deployed Function App
  FUNCTION_APP=order-processing-func-12345 ./test-order.sh

  # Test with direct URL
  ./test-order.sh --function-url http://localhost:7071/api/process-order

  # Test mapping only (no PostgreSQL/Blob storage)
  ./test-order.sh --mapping-only --function-url http://localhost:7071/api/x12-map

  # Send custom payload
  ./test-order.sh ./my-order.json
EOF
  exit 0
}

get_function_url() {
  if [[ -n "$FUNCTION_URL" ]]; then
    echo "$FUNCTION_URL"
    return
  fi

  if [[ -n "$FUNCTION_APP" ]]; then
    if [[ "$MAPPING_ONLY" == "true" ]]; then
      echo "https://$FUNCTION_APP.azurewebsites.net/api/x12-map"
    else
      echo "https://$FUNCTION_APP.azurewebsites.net/api/process-order"
    fi
    return
  fi

  error "No Function URL specified. Set FUNCTION_APP or FUNCTION_URL, or use --function-url"
}

# =============================================================================
# Parse Arguments
# =============================================================================
PAYLOAD="$DEFAULT_PAYLOAD"

while [[ $# -gt 0 ]]; do
  case $1 in
    --function-app)
      FUNCTION_APP="$2"
      shift 2
      ;;
    --function-url)
      FUNCTION_URL="$2"
      shift 2
      ;;
    --logic-app-url)
      LOGIC_APP_URL="$2"
      shift 2
      ;;
    --logic-app)
      USE_LOGIC_APP=true
      shift
      ;;
    --mapping-only)
      MAPPING_ONLY=true
      shift
      ;;
    --minimal)
      PAYLOAD="$MINIMAL_PAYLOAD"
      shift
      ;;
    --bulk)
      PAYLOAD="$BULK_PAYLOAD"
      shift
      ;;
    -h|--help)
      usage
      ;;
    -*)
      error "Unknown option: $1"
      ;;
    *)
      PAYLOAD_FILE="$1"
      shift
      ;;
  esac
done

# =============================================================================
# Main
# =============================================================================
if [[ -n "$PAYLOAD_FILE" ]]; then
  if [[ ! -f "$PAYLOAD_FILE" ]]; then
    error "Payload file not found: $PAYLOAD_FILE"
  fi
  PAYLOAD="$(cat "$PAYLOAD_FILE")"
  log "Using payload from: $PAYLOAD_FILE"
fi

if [[ "$USE_LOGIC_APP" == "true" ]]; then
  if [[ -z "$LOGIC_APP_URL" ]]; then
    error "Logic App URL not specified. Set LOGIC_APP_URL or use --logic-app-url"
  fi
  URL="$LOGIC_APP_URL"
  log "Sending to Logic App..."
else
  URL="$(get_function_url)"
  if [[ "$MAPPING_ONLY" == "true" ]]; then
    # Add includeMeta for mapping-only requests
    PAYLOAD=$(echo "$PAYLOAD" | jq '. + {"includeMeta": true}')
    log "Sending to X12 mapping endpoint (no storage)..."
  else
    log "Sending to order processing endpoint..."
  fi
fi

log "URL: $URL"
log ""

# Send request
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$URL" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD")

HTTP_CODE=$(echo "$RESPONSE" | tail -1)
BODY=$(echo "$RESPONSE" | sed '$d')

log "HTTP Status: $HTTP_CODE"
log ""
log "Response:"
echo "$BODY" | jq . 2>/dev/null || echo "$BODY"
