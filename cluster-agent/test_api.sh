#!/bin/bash

# Test script for SLURM Usage History Exporter API
# This script tests the /api/data/ingest endpoint

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================="
echo "SLURM Usage History Exporter - API Test"
echo "========================================="
echo ""

# Check if API_URL and API_KEY are provided
if [ -z "$1" ]; then
    echo -e "${RED}Error: API URL not provided${NC}"
    echo ""
    echo "Usage: $0 <API_URL> <API_KEY>"
    echo "Example: $0 https://dashboard.example.com your-api-key"
    exit 1
fi

if [ -z "$2" ]; then
    echo -e "${RED}Error: API KEY not provided${NC}"
    echo ""
    echo "Usage: $0 <API_URL> <API_KEY>"
    echo "Example: $0 https://dashboard.example.com your-api-key"
    exit 1
fi

API_URL="$1"
API_KEY="$2"

echo -e "${YELLOW}Testing API endpoint...${NC}"
echo "API URL: $API_URL"
echo "API Key: ${API_KEY:0:10}..."
echo ""

# Test 1: Health check
echo "Test 1: Health check"
echo "GET $API_URL/api/dashboard/health"
echo ""

HEALTH_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" "$API_URL/api/dashboard/health")
HTTP_CODE=$(echo "$HEALTH_RESPONSE" | grep "HTTP_CODE" | cut -d':' -f2)
RESPONSE_BODY=$(echo "$HEALTH_RESPONSE" | sed '/HTTP_CODE/d')

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ Health check successful${NC}"
    echo "Response: $RESPONSE_BODY"
else
    echo -e "${RED}✗ Health check failed (HTTP $HTTP_CODE)${NC}"
    echo "Response: $RESPONSE_BODY"
    exit 1
fi

echo ""
echo "---"
echo ""

# Test 2: Submit test data
echo "Test 2: Data ingestion"
echo "POST $API_URL/api/data/ingest"
echo ""

# Create test payload
TEST_PAYLOAD=$(cat <<'EOF'
{
  "hostname": "test-cluster",
  "jobs": [
    {
      "JobID": "12345",
      "User": "testuser",
      "Account": "test-account",
      "Partition": "test-partition",
      "State": "COMPLETED",
      "QOS": "normal",
      "Submit": "2024-10-31T10:00:00",
      "Start": "2024-10-31T10:05:00",
      "End": "2024-10-31T11:00:00",
      "CPUHours": 4.0,
      "GPUHours": 0.0,
      "AllocCPUS": 4,
      "AllocGPUS": 0,
      "AllocNodes": 1,
      "NodeList": "node001"
    }
  ]
}
EOF
)

echo "Payload:"
echo "$TEST_PAYLOAD" | head -10
echo "..."
echo ""

INGEST_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" \
    -X POST \
    -H "X-API-Key: $API_KEY" \
    -H "Content-Type: application/json" \
    -d "$TEST_PAYLOAD" \
    "$API_URL/api/data/ingest")

HTTP_CODE=$(echo "$INGEST_RESPONSE" | grep "HTTP_CODE" | cut -d':' -f2)
RESPONSE_BODY=$(echo "$INGEST_RESPONSE" | sed '/HTTP_CODE/d')

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ Data ingestion successful${NC}"
    echo "Response: $RESPONSE_BODY"
else
    echo -e "${RED}✗ Data ingestion failed (HTTP $HTTP_CODE)${NC}"
    echo "Response: $RESPONSE_BODY"

    if [ "$HTTP_CODE" = "401" ]; then
        echo ""
        echo -e "${YELLOW}Hint: Check that your API key is correct${NC}"
    elif [ "$HTTP_CODE" = "500" ]; then
        echo ""
        echo -e "${YELLOW}Hint: Check backend logs for errors${NC}"
    fi

    exit 1
fi

echo ""
echo "---"
echo ""

# Test 3: Verify metadata includes test cluster
echo "Test 3: Verify metadata"
echo "GET $API_URL/api/dashboard/metadata"
echo ""

METADATA_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" "$API_URL/api/dashboard/metadata")
HTTP_CODE=$(echo "$METADATA_RESPONSE" | grep "HTTP_CODE" | cut -d':' -f2)
RESPONSE_BODY=$(echo "$METADATA_RESPONSE" | sed '/HTTP_CODE/d')

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ Metadata fetch successful${NC}"

    # Check if test-cluster appears in metadata
    if echo "$RESPONSE_BODY" | grep -q "test-cluster"; then
        echo -e "${GREEN}✓ Test cluster found in metadata${NC}"
    else
        echo -e "${YELLOW}⚠ Test cluster not yet in metadata (may need auto-refresh)${NC}"
    fi

    echo "Available clusters:"
    echo "$RESPONSE_BODY" | grep -o '"hostnames":\[[^]]*\]' || echo "Could not parse hostnames"
else
    echo -e "${RED}✗ Metadata fetch failed (HTTP $HTTP_CODE)${NC}"
    echo "Response: $RESPONSE_BODY"
fi

echo ""
echo "========================================="
echo -e "${GREEN}All tests completed!${NC}"
echo "========================================="
echo ""
echo "Summary:"
echo "  ✓ Health check: OK"
echo "  ✓ Data ingestion: OK"
echo "  ✓ API authentication: OK"
echo ""
echo "Your API is ready to receive data from clusters!"
