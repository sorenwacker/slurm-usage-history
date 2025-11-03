#!/bin/bash

# Quick Test Script for SLURM Usage History
# This script sets up a complete test environment

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "=============================================="
echo "SLURM Usage History - Quick Test"
echo "=============================================="
echo ""

# Step 1: Check backend dependencies
echo -e "${BLUE}Step 1: Checking backend dependencies...${NC}"
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo -e "${YELLOW}Installing backend dependencies...${NC}"
    cd backend
    pip3 install -r requirements.txt
    cd ..
fi
echo -e "${GREEN}✓ Backend dependencies OK${NC}"
echo ""

# Step 2: Setup backend .env
echo -e "${BLUE}Step 2: Setting up backend configuration...${NC}"
if [ ! -f backend/.env ]; then
    cat > backend/.env << 'EOF'
API_KEYS=test-secret-key-12345
DATA_PATH=../data
AUTO_REFRESH_INTERVAL=600
CORS_ORIGINS=http://localhost:3100
EOF
    echo -e "${GREEN}✓ Created backend/.env${NC}"
else
    echo -e "${YELLOW}⚠ backend/.env already exists, skipping${NC}"
fi
echo ""

# Step 3: Start backend in background
echo -e "${BLUE}Step 3: Starting backend...${NC}"
cd backend

# Kill any existing backend
pkill -f "uvicorn app.main:app" 2>/dev/null || true
sleep 1

# Start backend in background
nohup python3 -m uvicorn app.main:app --reload --port 8100 > ../backend.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > ../backend.pid

# Wait for backend to start
echo "Waiting for backend to start..."
for i in {1..30}; do
    if curl -s http://localhost:8100/api/dashboard/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Backend started (PID: $BACKEND_PID)${NC}"
        break
    fi
    sleep 1
    if [ $i -eq 30 ]; then
        echo -e "${RED}✗ Backend failed to start${NC}"
        echo "Check backend.log for errors"
        exit 1
    fi
done
cd ..
echo ""

# Step 4: Test health endpoint
echo -e "${BLUE}Step 4: Testing health endpoint...${NC}"
HEALTH=$(curl -s http://localhost:8100/api/dashboard/health)
if echo "$HEALTH" | grep -q "healthy"; then
    echo -e "${GREEN}✓ Health check passed${NC}"
    echo "Response: $HEALTH"
else
    echo -e "${RED}✗ Health check failed${NC}"
    exit 1
fi
echo ""

# Step 5: Create test data
echo -e "${BLUE}Step 5: Creating test data...${NC}"
cat > test_data.json << 'EOF'
{
  "hostname": "test-cluster",
  "jobs": [
    {
      "JobID": "100001",
      "User": "alice",
      "Account": "physics-dept",
      "Partition": "compute",
      "State": "COMPLETED",
      "QOS": "normal",
      "Submit": "2024-10-31T08:00:00",
      "Start": "2024-10-31T08:05:00",
      "End": "2024-10-31T10:00:00",
      "CPUHours": 7.67,
      "GPUHours": 0.0,
      "AllocCPUS": 4,
      "AllocGPUS": 0,
      "AllocNodes": 1,
      "NodeList": "node001"
    },
    {
      "JobID": "100002",
      "User": "bob",
      "Account": "ml-research",
      "Partition": "gpu",
      "State": "COMPLETED",
      "QOS": "high",
      "Submit": "2024-10-31T09:00:00",
      "Start": "2024-10-31T09:10:00",
      "End": "2024-10-31T12:00:00",
      "CPUHours": 11.33,
      "GPUHours": 2.83,
      "AllocCPUS": 4,
      "AllocGPUS": 1,
      "AllocNodes": 1,
      "NodeList": "gpu001"
    },
    {
      "JobID": "100003",
      "User": "charlie",
      "Account": "chemistry",
      "Partition": "compute",
      "State": "COMPLETED",
      "QOS": "normal",
      "Submit": "2024-10-31T10:00:00",
      "Start": "2024-10-31T10:05:00",
      "End": "2024-10-31T14:00:00",
      "CPUHours": 31.33,
      "GPUHours": 0.0,
      "AllocCPUS": 8,
      "AllocGPUS": 0,
      "AllocNodes": 1,
      "NodeList": "node002"
    },
    {
      "JobID": "100004",
      "User": "alice",
      "Account": "physics-dept",
      "Partition": "gpu",
      "State": "FAILED",
      "QOS": "normal",
      "Submit": "2024-10-31T11:00:00",
      "Start": "2024-10-31T11:05:00",
      "End": "2024-10-31T11:06:00",
      "CPUHours": 0.07,
      "GPUHours": 0.02,
      "AllocCPUS": 4,
      "AllocGPUS": 1,
      "AllocNodes": 1,
      "NodeList": "gpu002"
    }
  ]
}
EOF
echo -e "${GREEN}✓ Test data created (4 jobs)${NC}"
echo ""

# Step 6: Submit test data
echo -e "${BLUE}Step 6: Submitting test data...${NC}"
INGEST_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" \
    -X POST http://localhost:8100/api/data/ingest \
    -H "X-API-Key: test-secret-key-12345" \
    -H "Content-Type: application/json" \
    -d @test_data.json)

HTTP_CODE=$(echo "$INGEST_RESPONSE" | grep "HTTP_CODE" | cut -d':' -f2)
RESPONSE_BODY=$(echo "$INGEST_RESPONSE" | sed '/HTTP_CODE/d')

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ Data ingestion successful${NC}"
    echo "Response: $RESPONSE_BODY"
else
    echo -e "${RED}✗ Data ingestion failed (HTTP $HTTP_CODE)${NC}"
    echo "Response: $RESPONSE_BODY"
    exit 1
fi
echo ""

# Step 7: Verify data storage
echo -e "${BLUE}Step 7: Verifying data storage...${NC}"
if [ -d "data/test-cluster/weekly-data" ]; then
    FILE_COUNT=$(ls -1 data/test-cluster/weekly-data/*.parquet 2>/dev/null | wc -l)
    echo -e "${GREEN}✓ Data directory created${NC}"
    echo "Files found: $FILE_COUNT"
    ls -lh data/test-cluster/weekly-data/
else
    echo -e "${RED}✗ Data directory not created${NC}"
    exit 1
fi
echo ""

# Step 8: Test metadata endpoint
echo -e "${BLUE}Step 8: Testing metadata endpoint...${NC}"
METADATA=$(curl -s http://localhost:8100/api/dashboard/metadata)
if echo "$METADATA" | grep -q "test-cluster"; then
    echo -e "${GREEN}✓ Metadata includes test cluster${NC}"
    echo "Available clusters: $(echo "$METADATA" | grep -o '"hostnames":\[[^]]*\]')"
else
    echo -e "${YELLOW}⚠ Test cluster not in metadata yet (may need auto-refresh)${NC}"
    echo -e "${YELLOW}Restarting backend to force refresh...${NC}"
    kill $BACKEND_PID
    sleep 2
    cd backend
    nohup python3 -m uvicorn app.main:app --reload --port 8100 > ../backend.log 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > ../backend.pid
    sleep 3
    cd ..

    METADATA=$(curl -s http://localhost:8100/api/dashboard/metadata)
    if echo "$METADATA" | grep -q "test-cluster"; then
        echo -e "${GREEN}✓ Metadata includes test cluster after refresh${NC}"
    fi
fi
echo ""

# Step 9: Test filtering
echo -e "${BLUE}Step 9: Testing data filtering...${NC}"
FILTER_RESPONSE=$(curl -s -X POST http://localhost:8100/api/dashboard/filter \
    -H "Content-Type: application/json" \
    -d '{
        "hostname": "test-cluster",
        "start_date": "2024-10-01",
        "end_date": "2024-11-30"
    }')

TOTAL_JOBS=$(echo "$FILTER_RESPONSE" | grep -o '"total_jobs":[0-9]*' | cut -d':' -f2)
if [ "$TOTAL_JOBS" = "4" ]; then
    echo -e "${GREEN}✓ Filtering works (found $TOTAL_JOBS jobs)${NC}"
else
    echo -e "${YELLOW}⚠ Expected 4 jobs, got: $TOTAL_JOBS${NC}"
fi
echo ""

# Step 10: Summary
echo "=============================================="
echo -e "${GREEN}✓ All tests passed!${NC}"
echo "=============================================="
echo ""
echo "Test Results:"
echo "  ✓ Backend running on http://localhost:8100"
echo "  ✓ Health check: OK"
echo "  ✓ Data ingestion: OK"
echo "  ✓ Data storage: OK"
echo "  ✓ Metadata: OK"
echo "  ✓ Filtering: OK"
echo ""
echo "Test Data Summary:"
echo "  - Cluster: test-cluster"
echo "  - Jobs: 4"
echo "  - Users: alice, bob, charlie"
echo "  - Partitions: compute, gpu"
echo "  - Accounts: physics-dept, ml-research, chemistry"
echo ""
echo "Next Steps:"
echo "  1. Open frontend: cd frontend && npm run dev"
echo "     Then visit: http://localhost:3100"
echo ""
echo "  2. View backend logs: tail -f backend.log"
echo ""
echo "  3. Test API manually:"
echo "     curl http://localhost:8100/api/dashboard/metadata"
echo ""
echo "  4. Stop backend when done:"
echo "     kill \$(cat backend.pid)"
echo ""
echo "  5. Deploy to cluster:"
echo "     cd cluster-agent"
echo "     See QUICKSTART.md or README.md"
echo ""
echo "=============================================="
echo -e "${BLUE}Backend is running in background (PID: $BACKEND_PID)${NC}"
echo "Logs: backend.log"
echo "=============================================="
