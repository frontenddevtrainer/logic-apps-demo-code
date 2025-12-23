# Upload Test Files to Blob Storage
# This script uploads the sample CSV files to the incoming-orders container

param(
    [Parameter(Mandatory=$true)]
    [string]$StorageAccountName,

    [Parameter(Mandatory=$false)]
    [string]$TestFile = "all"
)

# Set error action preference
$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "CSV to X12 Blob Storage Upload Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get storage context
Write-Host "Connecting to storage account: $StorageAccountName" -ForegroundColor Yellow
try {
    $ctx = New-AzStorageContext -StorageAccountName $StorageAccountName -UseConnectedAccount
    Write-Host "✓ Connected successfully" -ForegroundColor Green
} catch {
    Write-Host "✗ Failed to connect to storage account" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Make sure you're logged in with: Connect-AzAccount" -ForegroundColor Yellow
    exit 1
}

# Container name
$containerName = "incoming-orders"

# Check if container exists
Write-Host ""
Write-Host "Checking if container exists: $containerName" -ForegroundColor Yellow
$container = Get-AzStorageContainer -Name $containerName -Context $ctx -ErrorAction SilentlyContinue
if (-not $container) {
    Write-Host "✗ Container '$containerName' not found" -ForegroundColor Red
    Write-Host "Please create the container first." -ForegroundColor Yellow
    exit 1
}
Write-Host "✓ Container found" -ForegroundColor Green

# Function to upload file
function Upload-TestFile {
    param(
        [string]$FilePath,
        [string]$Description,
        [string]$ExpectedResult
    )

    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Uploading: $Description" -ForegroundColor Yellow
    Write-Host "File: $FilePath" -ForegroundColor Gray
    Write-Host ""

    if (-not (Test-Path $FilePath)) {
        Write-Host "✗ File not found: $FilePath" -ForegroundColor Red
        return
    }

    $fileName = Split-Path -Leaf $FilePath

    try {
        Set-AzStorageBlobContent `
            -File $FilePath `
            -Container $containerName `
            -Blob $fileName `
            -Context $ctx `
            -Force | Out-Null

        Write-Host "✓ File uploaded successfully" -ForegroundColor Green
        Write-Host ""
        Write-Host "Expected Result:" -ForegroundColor Cyan
        Write-Host $ExpectedResult -ForegroundColor White
        Write-Host ""
        Write-Host "Waiting 90 seconds for Logic App to process..." -ForegroundColor Yellow
        Start-Sleep -Seconds 90

    } catch {
        Write-Host "✗ Upload failed" -ForegroundColor Red
        Write-Host "Error: $_" -ForegroundColor Red
    }
}

# Test cases
$test1Description = "Test 1: Valid CSV (2 line items)"
$test1Expected = @"
  ✓ Logic App should trigger
  ✓ X12 file created in x12-output container
  ✓ CSV moved to archive container
  ✓ incoming-orders container empty
"@

$test2Description = "Test 2: Invalid CSV (missing OrderNumber)"
$test2Expected = @"
  ✓ Logic App should trigger
  ✓ Validation fails
  ✓ Error JSON created in validation-errors container
  ✓ CSV moved to errors container
  ✗ No X12 file created
"@

$test3Description = "Test 3: Multi-line CSV (4 line items)"
$test3Expected = @"
  ✓ Logic App should trigger
  ✓ X12 file created with 4 PO1 segments
  ✓ CTT segment shows count of 4
  ✓ SE segment count is 14
"@

# Menu
if ($TestFile -eq "all") {
    Write-Host ""
    Write-Host "Select test to run:" -ForegroundColor Cyan
    Write-Host "1. Test 1: Valid CSV (Happy Path)"
    Write-Host "2. Test 2: Invalid CSV (Missing OrderNumber)"
    Write-Host "3. Test 3: Multi-line CSV (4 line items)"
    Write-Host "4. Run All Tests"
    Write-Host ""
    $choice = Read-Host "Enter choice (1-4)"
} else {
    $choice = $TestFile
}

switch ($choice) {
    "1" {
        Upload-TestFile `
            -FilePath "sample-data/orders.csv" `
            -Description $test1Description `
            -ExpectedResult $test1Expected
    }
    "2" {
        Upload-TestFile `
            -FilePath "sample-data/orders-invalid.csv" `
            -Description $test2Description `
            -ExpectedResult $test2Expected
    }
    "3" {
        Upload-TestFile `
            -FilePath "sample-data/orders-multi-line.csv" `
            -Description $test3Description `
            -ExpectedResult $test3Expected
    }
    "4" {
        Write-Host ""
        Write-Host "Running all tests sequentially..." -ForegroundColor Cyan

        Upload-TestFile `
            -FilePath "sample-data/orders.csv" `
            -Description $test1Description `
            -ExpectedResult $test1Expected

        Upload-TestFile `
            -FilePath "sample-data/orders-invalid.csv" `
            -Description $test2Description `
            -ExpectedResult $test2Expected

        Upload-TestFile `
            -FilePath "sample-data/orders-multi-line.csv" `
            -Description $test3Description `
            -ExpectedResult $test3Expected

        Write-Host ""
        Write-Host "========================================" -ForegroundColor Cyan
        Write-Host "All tests completed!" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Cyan
    }
    default {
        Write-Host "Invalid choice" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "1. Check Logic App run history in Azure Portal"
Write-Host "2. Verify blob containers:"
Write-Host "   - x12-output (for successful X12 files)"
Write-Host "   - validation-errors (for failed validations)"
Write-Host "   - archive (for processed CSV files)"
Write-Host "   - errors (for failed CSV files)"
Write-Host ""
Write-Host "TIP: Use Azure Storage Explorer to view containers" -ForegroundColor Yellow
Write-Host ""
