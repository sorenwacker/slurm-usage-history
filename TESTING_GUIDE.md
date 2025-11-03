# Testing Guide - SLURM Usage History Exporter

This guide shows you how to test the complete system, from local development to production deployment.

## Table of Contents

1. [Local Testing (No Cluster Required)](#local-testing-no-cluster-required)
2. [Testing with Real SLURM Data](#testing-with-real-slurm-data)
3. [End-to-End Testing](#end-to-end-testing)
4. [Troubleshooting Tests](#troubleshooting-tests)

---

## Local Testing (No Cluster Required)

You can test the entire system on your local machine without a SLURM cluster.

### Step 1: Start the Backend

```bash
cd /Users/sdrwacker/workspace/slurm-usage-history/backend

# Create .env file if it doesn't exist
cp .env.example .env

# Edit .env and set a test API key
nano .env
```

Set in `.env`:
```bash
API_KEYS=test-secret-key-12345
DATA_PATH=../data
AUTO_REFRESH_INTERVAL=600
CORS_ORIGINS=http://localhost:3100
```

Install dependencies and start:
```bash
# Install dependencies (if not already done)
pip install -r requirements.txt

# Start the backend
uvicorn app.main:app --reload --port 8100
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8100
INFO:     Application startup complete.
```

### Step 2: Test the Health Endpoint

In a new terminal:

```bash
# Test health endpoint
curl http://localhost:8100/api/dashboard/health

# Expected response:
# {"status":"healthy","timestamp":"...","data_loaded":true,"hostnames":[]}
```

### Step 3: Test Data Ingestion with curl

Create a test data file:

```bash
cat > test_payload.json << 'EOF'
{
  "hostname": "test-cluster-local",
  "jobs": [
    {
      "JobID": "100001",
      "User": "alice",
      "Account": "research-group-a",
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
      "Account": "research-group-b",
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
      "User": "alice",
      "Account": "research-group-a",
      "Partition": "compute",
      "State": "FAILED",
      "QOS": "normal",
      "Submit": "2024-10-31T10:00:00",
      "Start": "2024-10-31T10:05:00",
      "End": "2024-10-31T10:06:00",
      "CPUHours": 0.07,
      "GPUHours": 0.0,
      "AllocCPUS": 4,
      "AllocGPUS": 0,
      "AllocNodes": 1,
      "NodeList": "node002"
    }
  ]
}
EOF
```

Submit the test data:

```bash
curl -X POST http://localhost:8100/api/data/ingest \
  -H "X-API-Key: test-secret-key-12345" \
  -H "Content-Type: application/json" \
  -d @test_payload.json

# Expected response:
# {
#   "success": true,
#   "message": "Successfully ingested 3 jobs for test-cluster-local",
#   "jobs_processed": 3,
#   "hostname": "test-cluster-local"
# }
```

### Step 4: Verify Data Was Stored

```bash
# Check that data directory was created
ls -la data/test-cluster-local/weekly-data/

# You should see a parquet file like:
# jobs_20241031_143022.parquet
```

### Step 5: Test Metadata Endpoint

```bash
curl http://localhost:8100/api/dashboard/metadata | jq

# Expected response should include:
# {
#   "hostnames": ["test-cluster-local"],
#   "partitions": {
#     "test-cluster-local": ["compute", "gpu"]
#   },
#   "accounts": {
#     "test-cluster-local": ["research-group-a", "research-group-b"]
#   },
#   ...
# }
```

### Step 6: Test Filtering

```bash
cat > filter_request.json << 'EOF'
{
  "hostname": "test-cluster-local",
  "start_date": "2024-10-01",
  "end_date": "2024-11-30",
  "partitions": ["compute", "gpu"],
  "states": ["COMPLETED"]
}
EOF

curl -X POST http://localhost:8100/api/dashboard/filter \
  -H "Content-Type: application/json" \
  -d @filter_request.json | jq

# Expected response should show 2 completed jobs
```

### Step 7: Test the Automated Test Script

Use the provided test script:

```bash
cd cluster-agent
./test_api.sh http://localhost:8100 test-secret-key-12345

# This will run all three tests:
# ✓ Health check
# ✓ Data ingestion
# ✓ Metadata verification
```

### Step 8: Start the Frontend

```bash
cd /Users/sdrwacker/workspace/slurm-usage-history/frontend

# Install dependencies (if not already done)
npm install

# Start development server
npm run dev

# Open browser to http://localhost:3100
```

You should now see:
- "test-cluster-local" in the cluster dropdown
- Filters populated (partitions: compute, gpu)
- The 3 jobs displayed in charts/tables

---

## Testing with Real SLURM Data

If you have access to a SLURM cluster, you can test with real job data.

### Option A: Test Locally (Extract Data, Submit from Local Machine)

#### Step 1: Extract SLURM Data on Cluster

On your SLURM cluster:

```bash
# SSH to cluster
ssh user@your-cluster

# Get job data (requires SLURM access)
sacct --format=JobID,User,QOS,Account,Partition,Submit,Start,End,State,Elapsed,AllocCPUS,AllocTRES,Cluster \
      --parsable2 \
      --allusers \
      --starttime=2024-10-01 \
      --endtime=2024-10-31 \
      > jobs_october.txt

# Download to local machine
exit
scp user@your-cluster:jobs_october.txt .
```

#### Step 2: Convert to JSON Format

Create a Python script to convert:

```python
#!/usr/bin/env python3
# convert_sacct_to_json.py

import json
import sys
from datetime import datetime

def parse_tres(tres_str):
    """Parse AllocTRES string."""
    cpu = 0
    gpu = 0

    if not tres_str:
        return cpu, gpu

    for item in tres_str.split(','):
        if '=' in item:
            key, val = item.split('=', 1)
            if 'cpu' in key.lower():
                try:
                    cpu = int(val)
                except:
                    pass
            elif 'gpu' in key.lower() or 'gres/gpu' in key.lower():
                try:
                    gpu = int(val)
                except:
                    pass

    return cpu, gpu

def parse_elapsed(elapsed_str):
    """Convert elapsed time to hours."""
    if not elapsed_str or elapsed_str == 'Unknown':
        return 0.0

    try:
        total_seconds = 0
        if '-' in elapsed_str:
            days, time_part = elapsed_str.split('-')
            total_seconds += int(days) * 86400
        else:
            time_part = elapsed_str

        parts = time_part.split(':')
        if len(parts) == 3:
            h, m, s = parts
            total_seconds += int(h) * 3600 + int(m) * 60 + float(s)
        elif len(parts) == 2:
            m, s = parts
            total_seconds += int(m) * 60 + float(s)

        return total_seconds / 3600.0
    except:
        return 0.0

# Read sacct output
with open(sys.argv[1], 'r') as f:
    lines = f.readlines()

# Parse header
headers = lines[0].strip().split('|')
jobs = []

for line in lines[1:]:
    if not line.strip():
        continue

    fields = line.strip().split('|')
    job = dict(zip(headers, fields))

    # Skip running or unknown jobs
    if job.get('State') in ['RUNNING', 'Unknown', 'PENDING']:
        continue

    # Parse AllocTRES
    cpu, gpu = parse_tres(job.get('AllocTRES', ''))

    # Calculate hours
    elapsed_hours = parse_elapsed(job.get('Elapsed', '0'))
    cpu_hours = elapsed_hours * cpu
    gpu_hours = elapsed_hours * gpu

    # Build job record
    job_record = {
        "JobID": job.get('JobID', ''),
        "User": job.get('User', ''),
        "Account": job.get('Account', 'unknown'),
        "Partition": job.get('Partition', 'unknown'),
        "State": job.get('State', ''),
        "QOS": job.get('QOS') if job.get('QOS') else None,
        "Submit": job.get('Submit', ''),
        "Start": job.get('Start') if job.get('Start') not in ['Unknown', ''] else None,
        "End": job.get('End') if job.get('End') not in ['Unknown', ''] else None,
        "CPUHours": round(cpu_hours, 2),
        "GPUHours": round(gpu_hours, 2),
        "AllocCPUS": cpu,
        "AllocGPUS": gpu,
        "AllocNodes": 1,
        "NodeList": None
    }

    jobs.append(job_record)

# Create payload
payload = {
    "hostname": job.get('Cluster', 'unknown-cluster'),
    "jobs": jobs
}

# Write JSON
output_file = sys.argv[1].replace('.txt', '.json')
with open(output_file, 'w') as f:
    json.dump(payload, f, indent=2)

print(f"Converted {len(jobs)} jobs to {output_file}")
```

Run the converter:

```bash
python3 convert_sacct_to_json.py jobs_october.txt

# This creates jobs_october.json
```

#### Step 3: Submit to Local Backend

```bash
curl -X POST http://localhost:8100/api/data/ingest \
  -H "X-API-Key: test-secret-key-12345" \
  -H "Content-Type: application/json" \
  -d @jobs_october.json

# Check the response
```

### Option B: Test the Exporter Script Locally

You can test the exporter script on your local machine if you have SLURM client tools:

```bash
cd cluster-agent

# Create a local config
cat > config_local.json << EOF
{
  "api_url": "http://localhost:8100",
  "api_key": "test-secret-key-12345",
  "cluster_name": "my-cluster"
}
EOF

# Test with dry-run (won't submit)
python3 slurm-usage-history-exporter.py \
  --config config_local.json \
  --start-date 2024-10-01 \
  --end-date 2024-10-31 \
  --dry-run \
  --verbose

# If dry-run looks good, submit for real
python3 slurm-usage-history-exporter.py \
  --config config_local.json \
  --start-date 2024-10-01 \
  --end-date 2024-10-31 \
  --verbose
```

---

## End-to-End Testing

Test the complete workflow from cluster to dashboard.

### Step 1: Deploy to Cluster (Test Mode)

On your SLURM cluster:

```bash
# Copy cluster-agent
scp -r cluster-agent/ user@cluster:/tmp/

# SSH to cluster
ssh user@cluster

# Navigate to directory
cd /tmp/cluster-agent

# Install (skip if testing without root)
sudo ./install.sh

# Or for local install:
pip3 install --user -r requirements.txt
```

### Step 2: Configure for Testing

```bash
# Create test config
cat > config_test.json << EOF
{
  "api_url": "http://YOUR-LAPTOP-IP:8100",
  "api_key": "test-secret-key-12345",
  "cluster_name": "$(hostname -s)"
}
EOF
```

**Note:** Replace `YOUR-LAPTOP-IP` with your laptop's IP address that's accessible from the cluster.

### Step 3: Test Extraction

```bash
# Dry run first
./slurm-usage-history-exporter.py \
  --config config_test.json \
  --start-date $(date -d '7 days ago' +%Y-%m-%d) \
  --end-date $(date +%Y-%m-%d) \
  --dry-run \
  --verbose

# Check output - should show:
# - Number of jobs found
# - Sample job data
# - Cluster name detected
```

### Step 4: Submit Test Data

```bash
# Submit for real
./slurm-usage-history-exporter.py \
  --config config_test.json \
  --start-date $(date -d '7 days ago' +%Y-%m-%d) \
  --end-date $(date +%Y-%m-%d) \
  --verbose

# Should see:
# INFO - Successfully submitted: Successfully ingested X jobs for ...
```

### Step 5: Verify in Dashboard

On your local machine:

```bash
# Check metadata includes your cluster
curl http://localhost:8100/api/dashboard/metadata | jq '.hostnames'

# Should include your cluster name

# Open frontend
# http://localhost:3100

# Select your cluster from dropdown
# Verify jobs appear
```

### Step 6: Test Automated Collection

If you installed with systemd:

```bash
# On cluster
sudo systemctl start slurm-usage-history-exporter.service

# Check status
sudo systemctl status slurm-usage-history-exporter.service

# View logs
sudo journalctl -u slurm-usage-history-exporter.service -f

# Enable timer for automatic runs
sudo systemctl enable slurm-usage-history-exporter.timer
sudo systemctl start slurm-usage-history-exporter.timer

# Check timer status
systemctl status slurm-usage-history-exporter.timer

# See when it will run next
systemctl list-timers slurm-usage-history-exporter.timer
```

---

## Testing Multiple Clusters

To test the multi-cluster feature:

### Step 1: Create Multiple Test Datasets

```bash
# Create data for cluster 1
cat > cluster1_payload.json << 'EOF'
{
  "hostname": "cluster-hpc-01",
  "jobs": [
    {
      "JobID": "1001",
      "User": "alice",
      "Account": "physics",
      "Partition": "compute",
      "State": "COMPLETED",
      "Submit": "2024-10-31T08:00:00",
      "Start": "2024-10-31T08:05:00",
      "End": "2024-10-31T10:00:00",
      "CPUHours": 7.67,
      "GPUHours": 0.0,
      "AllocCPUS": 4,
      "AllocGPUS": 0,
      "AllocNodes": 1
    }
  ]
}
EOF

# Create data for cluster 2
cat > cluster2_payload.json << 'EOF'
{
  "hostname": "cluster-gpu-02",
  "jobs": [
    {
      "JobID": "2001",
      "User": "bob",
      "Account": "ml-research",
      "Partition": "gpu",
      "State": "COMPLETED",
      "Submit": "2024-10-31T09:00:00",
      "Start": "2024-10-31T09:10:00",
      "End": "2024-10-31T12:00:00",
      "CPUHours": 11.33,
      "GPUHours": 2.83,
      "AllocCPUS": 4,
      "AllocGPUS": 1,
      "AllocNodes": 1
    }
  ]
}
EOF
```

### Step 2: Submit Both

```bash
# Submit cluster 1 data
curl -X POST http://localhost:8100/api/data/ingest \
  -H "X-API-Key: test-secret-key-12345" \
  -H "Content-Type: application/json" \
  -d @cluster1_payload.json

# Submit cluster 2 data
curl -X POST http://localhost:8100/api/data/ingest \
  -H "X-API-Key: test-secret-key-12345" \
  -H "Content-Type: application/json" \
  -d @cluster2_payload.json
```

### Step 3: Verify Both Clusters Appear

```bash
# Check metadata
curl http://localhost:8100/api/dashboard/metadata | jq '.hostnames'

# Should show:
# ["cluster-hpc-01", "cluster-gpu-02"]

# Check data directories
ls -la data/
# Should see:
# cluster-hpc-01/
# cluster-gpu-02/
```

### Step 4: Test Cluster-Specific Queries

```bash
# Query cluster 1
curl -X POST http://localhost:8100/api/dashboard/filter \
  -H "Content-Type: application/json" \
  -d '{"hostname":"cluster-hpc-01"}' | jq

# Query cluster 2
curl -X POST http://localhost:8100/api/dashboard/filter \
  -H "Content-Type: application/json" \
  -d '{"hostname":"cluster-gpu-02"}' | jq
```

---

## Troubleshooting Tests

### Backend Won't Start

```bash
# Check if port is already in use
lsof -i :8100

# Try a different port
uvicorn app.main:app --reload --port 8101

# Check Python version (need 3.8+)
python3 --version

# Check dependencies
pip install -r requirements.txt
```

### API Returns 401 Unauthorized

```bash
# Check API key in .env
cat backend/.env | grep API_KEYS

# Make sure you're using the same key in curl
curl -X POST http://localhost:8100/api/data/ingest \
  -H "X-API-Key: YOUR-KEY-FROM-ENV" \
  -H "Content-Type: application/json" \
  -d '{"hostname":"test","jobs":[]}'

# Check backend logs for details
# (should show in terminal where uvicorn is running)
```

### Data Not Appearing in Dashboard

```bash
# Check if data files were created
ls -la data/*/weekly-data/

# If files exist, check backend auto-refresh
# Default is 600 seconds (10 minutes)
# Restart backend to force reload:
# Ctrl+C in backend terminal, then restart

# Check metadata endpoint
curl http://localhost:8100/api/dashboard/metadata | jq

# Check frontend is querying correct cluster
# Open browser console (F12) and check network requests
```

### Cluster Can't Reach Backend

```bash
# Check firewall on your laptop
sudo ufw status  # Ubuntu
sudo firewall-cmd --list-all  # RHEL/CentOS

# Allow port 8100
sudo ufw allow 8100  # Ubuntu
sudo firewall-cmd --add-port=8100/tcp --permanent  # RHEL

# Test connectivity from cluster
ssh user@cluster
curl -I http://YOUR-LAPTOP-IP:8100/api/dashboard/health

# If timeout, check network configuration
```

### Exporter Script Errors

```bash
# Check Python dependencies on cluster
pip3 list | grep -E "pandas|requests"

# Install if missing
pip3 install --user pandas requests

# Test sacct command manually
sacct --allusers --starttime=2024-10-01 --endtime=2024-10-31

# If permission denied, check SLURM access
scontrol show config | grep AccountingStorage
```

---

## Quick Test Checklist

Use this checklist for rapid testing:

- [ ] Backend starts without errors
- [ ] Health endpoint returns 200: `curl http://localhost:8100/api/dashboard/health`
- [ ] Can submit test data with API key
- [ ] Data file created in `data/{hostname}/weekly-data/`
- [ ] Metadata endpoint shows cluster: `curl http://localhost:8100/api/dashboard/metadata`
- [ ] Frontend starts and connects to backend
- [ ] Cluster appears in dropdown
- [ ] Charts display test data
- [ ] (If testing on cluster) Exporter dry-run succeeds
- [ ] (If testing on cluster) Exporter submits data successfully
- [ ] (If testing systemd) Timer is enabled and scheduled

---

## Automated Test Script

For quick validation, use the included test script:

```bash
cd cluster-agent

# Test local backend
./test_api.sh http://localhost:8100 test-secret-key-12345

# Test production backend
./test_api.sh https://your-production-url.com your-production-api-key
```

This runs all three critical tests and reports success/failure.

---

## Production Testing Checklist

Before deploying to production:

- [ ] Backend uses HTTPS (not HTTP)
- [ ] Strong API key generated (32+ characters)
- [ ] API key stored securely in backend `.env`
- [ ] CORS_ORIGINS configured for production frontend URL
- [ ] Data directory has adequate storage space
- [ ] Backend server has adequate RAM (recommend 4GB+ for large datasets)
- [ ] Firewall rules configured
- [ ] Test data ingestion from each cluster
- [ ] Verify auto-refresh works (wait 10 minutes or restart backend)
- [ ] Test frontend with real data
- [ ] Monitor backend logs for errors
- [ ] Test cluster agent systemd timer

---

## Summary

You now have multiple ways to test:

1. **Local-only testing** - No cluster needed, test with curl
2. **Real SLURM data** - Extract from cluster, convert, submit
3. **Direct exporter testing** - Run the Python script directly
4. **End-to-end testing** - Full cluster deployment
5. **Multi-cluster testing** - Verify multiple clusters work
6. **Automated testing** - Use the test script

Choose the method that matches your current setup and access level!
