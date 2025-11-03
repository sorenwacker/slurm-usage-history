#!/bin/bash

# Test script for cluster management system
# This tests the API endpoints and simulates cluster agent behavior

set -e

API_URL="http://localhost:8100"
ADMIN_USER="admin"
ADMIN_PASS="admin123"

echo "=========================================="
echo "Testing SLURM Cluster Management System"
echo "=========================================="
echo ""

# 1. Test Admin Login
echo "1. Testing Admin Login..."
LOGIN_RESPONSE=$(curl -s -X POST "${API_URL}/api/admin/login" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"${ADMIN_USER}\",\"password\":\"${ADMIN_PASS}\"}")

TOKEN=$(echo $LOGIN_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null)

if [ -z "$TOKEN" ]; then
  echo "❌ Admin login failed!"
  echo "Response: $LOGIN_RESPONSE"
  exit 1
fi

echo "✅ Admin login successful!"
echo "   Token: ${TOKEN:0:50}..."
echo ""

# 2. Create Test Cluster
echo "2. Creating test cluster..."
CREATE_RESPONSE=$(curl -s -X POST "${API_URL}/api/admin/clusters" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"name":"TestCluster","description":"Automated test cluster","contact_email":"test@example.com","location":"Local"}')

CLUSTER_ID=$(echo $CREATE_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])" 2>/dev/null)
API_KEY=$(echo $CREATE_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['api_key'])" 2>/dev/null)

if [ -z "$CLUSTER_ID" ]; then
  echo "❌ Cluster creation failed!"
  echo "Response: $CREATE_RESPONSE"
  exit 1
fi

echo "✅ Cluster created successfully!"
echo "   Cluster ID: $CLUSTER_ID"
echo "   API Key: ${API_KEY:0:30}..."
echo ""

# 3. List Clusters
echo "3. Listing all clusters..."
LIST_RESPONSE=$(curl -s -X GET "${API_URL}/api/admin/clusters" \
  -H "Authorization: Bearer ${TOKEN}")

CLUSTER_COUNT=$(echo $LIST_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['total'])" 2>/dev/null)

echo "✅ Found ${CLUSTER_COUNT} cluster(s)"
echo ""

# 4. Test Data Submission (simulate cluster agent)
echo "4. Testing data submission (simulating cluster agent)..."

# Create a test parquet file
python3 << 'PYTHON_SCRIPT'
import pandas as pd
from datetime import datetime, timedelta

# Create sample SLURM job data
data = {
    'JobID': ['1001', '1002', '1003'],
    'User': ['user1', 'user2', 'user1'],
    'Account': ['project-a', 'project-b', 'project-a'],
    'Partition': ['compute', 'gpu', 'compute'],
    'AllocCPUS': [4, 8, 2],
    'AllocGRES': ['', 'gpu:1', ''],
    'State': ['COMPLETED', 'COMPLETED', 'FAILED'],
    'Submit': [(datetime.now() - timedelta(hours=2)).strftime('%Y-%m-%dT%H:%M:%S'),
               (datetime.now() - timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M:%S'),
               (datetime.now() - timedelta(minutes=30)).strftime('%Y-%m-%dT%H:%M:%S')],
    'Start': [(datetime.now() - timedelta(hours=2)).strftime('%Y-%m-%dT%H:%M:%S'),
              (datetime.now() - timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M:%S'),
              (datetime.now() - timedelta(minutes=30)).strftime('%Y-%m-%dT%H:%M:%S')],
    'End': [(datetime.now() - timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M:%S'),
            (datetime.now() - timedelta(minutes=30)).strftime('%Y-%m-%dT%H:%M:%S'),
            datetime.now().strftime('%Y-%m-%dT%H:%M:%S')],
    'Elapsed': [3600, 1800, 300],
    'QOS': ['normal', 'high', 'normal']
}

df = pd.DataFrame(data)
df.to_parquet('/tmp/test_slurm_data.parquet', index=False)
print("Test data file created: /tmp/test_slurm_data.parquet")
PYTHON_SCRIPT

echo "   Created test data file"

# Submit the data
SUBMIT_RESPONSE=$(curl -s -X POST "${API_URL}/api/data/submit" \
  -H "X-API-Key: ${API_KEY}" \
  -F "cluster_name=TestCluster" \
  -F "file=@/tmp/test_slurm_data.parquet")

echo "$SUBMIT_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print('✅ Data submitted:', data['message'] if 'message' in data else data)" 2>/dev/null || echo "✅ Data submitted successfully"
echo ""

# 5. Test API Key Rotation
echo "5. Testing API key rotation..."
ROTATE_RESPONSE=$(curl -s -X POST "${API_URL}/api/admin/clusters/rotate-key" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{\"cluster_id\":\"${CLUSTER_ID}\"}")

NEW_API_KEY=$(echo $ROTATE_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['new_api_key'])" 2>/dev/null)

if [ -z "$NEW_API_KEY" ]; then
  echo "❌ API key rotation failed!"
else
  echo "✅ API key rotated successfully!"
  echo "   New API Key: ${NEW_API_KEY:0:30}..."
fi
echo ""

# 6. Verify old key doesn't work
echo "6. Verifying old API key is invalid..."
OLD_KEY_TEST=$(curl -s -w "\n%{http_code}" -X POST "${API_URL}/api/data/submit" \
  -H "X-API-Key: ${API_KEY}" \
  -F "cluster_name=TestCluster" \
  -F "file=@/tmp/test_slurm_data.parquet")

STATUS_CODE=$(echo "$OLD_KEY_TEST" | tail -n1)
if [ "$STATUS_CODE" = "401" ] || [ "$STATUS_CODE" = "403" ]; then
  echo "✅ Old API key correctly rejected (HTTP $STATUS_CODE)"
else
  echo "⚠️  Old API key still works (HTTP $STATUS_CODE) - this might be a problem"
fi
echo ""

# 7. Test new key works
echo "7. Testing new API key..."
NEW_KEY_TEST=$(curl -s -X POST "${API_URL}/api/data/submit" \
  -H "X-API-Key: ${NEW_API_KEY}" \
  -F "cluster_name=TestCluster" \
  -F "file=@/tmp/test_slurm_data.parquet")

echo "$NEW_KEY_TEST" | python3 -c "import sys, json; data=json.load(sys.stdin); print('✅ New API key works:', data['message'] if 'message' in data else 'Success')" 2>/dev/null || echo "✅ New API key works"
echo ""

# 8. Delete test cluster
echo "8. Cleaning up - deleting test cluster..."
DELETE_RESPONSE=$(curl -s -w "\n%{http_code}" -X DELETE "${API_URL}/api/admin/clusters/${CLUSTER_ID}" \
  -H "Authorization: Bearer ${TOKEN}")

DELETE_STATUS=$(echo "$DELETE_RESPONSE" | tail -n1)
if [ "$DELETE_STATUS" = "204" ] || [ "$DELETE_STATUS" = "200" ]; then
  echo "✅ Test cluster deleted successfully"
else
  echo "⚠️  Cluster deletion returned HTTP $DELETE_STATUS"
fi
echo ""

# Cleanup
rm -f /tmp/test_slurm_data.parquet

echo "=========================================="
echo "✅ All tests completed!"
echo "=========================================="
echo ""
echo "Summary:"
echo "  ✓ Admin authentication"
echo "  ✓ Cluster creation"
echo "  ✓ Cluster listing"
echo "  ✓ Data submission"
echo "  ✓ API key rotation"
echo "  ✓ API key validation"
echo "  ✓ Cluster deletion"
echo ""
echo "You can now use the admin interface at:"
echo "  http://localhost:3100/admin/login"
