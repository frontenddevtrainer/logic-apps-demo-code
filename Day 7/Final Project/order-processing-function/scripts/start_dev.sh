#!/bin/bash
# Development startup script
# Starts Azurite and Azure Functions

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

echo "=== Order Processing Function - Development Environment ==="
echo ""

# Check if Azurite is already running
if lsof -i:10000 > /dev/null 2>&1; then
    echo "Azurite is already running on port 10000"
else
    echo "Starting Azurite..."
    mkdir -p "$PROJECT_DIR/azurite"
    npx azurite --location "$PROJECT_DIR/azurite" \
        --blobHost 127.0.0.1 \
        --queueHost 127.0.0.1 \
        --tableHost 127.0.0.1 \
        --skipApiVersionCheck &

    # Wait for Azurite to start
    sleep 3
    echo "Azurite started"
fi

echo ""

# Activate virtual environment and setup containers
echo "Setting up Azurite containers..."
source "$PROJECT_DIR/venv/bin/activate"
python3 "$SCRIPT_DIR/setup_azurite.py"

echo ""
echo "Starting Azure Functions..."
echo ""

# Start Azure Functions
func start
