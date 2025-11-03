# Testing the SLURM Usage History System

Quick guide to test the complete system.

## Fastest Way to Test (5 minutes)

Run the automated test script:

```bash
./quick_test.sh
```

This will:
1. ✅ Install backend dependencies
2. ✅ Create backend configuration
3. ✅ Start the backend server
4. ✅ Test health endpoint
5. ✅ Submit test data (4 jobs)
6. ✅ Verify data storage
7. ✅ Test metadata endpoint
8. ✅ Test filtering

**Result:** Backend running with test data at `http://localhost:8100`

## Next: View in Dashboard

After running `quick_test.sh`:

```bash
cd frontend
npm install
npm run dev
```

Open browser: `http://localhost:3100`

You should see:
- "test-cluster" in dropdown
- 4 jobs displayed
- Charts and visualizations

## Testing the Cluster Agent

### Option 1: Manual API Test

Test the API endpoint directly:

```bash
cd cluster-agent
./test_api.sh http://localhost:8100 test-secret-key-12345
```

### Option 2: Test Exporter Script (requires SLURM)

If you have SLURM access:

```bash
cd cluster-agent

# Create local config
cat > config_local.json << EOF
{
  "api_url": "http://localhost:8100",
  "api_key": "test-secret-key-12345"
}
EOF

# Dry run
python3 slurm-usage-history-exporter.py \
  --config config_local.json \
  --start-date 2024-10-01 \
  --end-date 2024-10-31 \
  --dry-run \
  --verbose

# Real submission
python3 slurm-usage-history-exporter.py \
  --config config_local.json \
  --start-date 2024-10-01 \
  --end-date 2024-10-31
```

## Complete Testing Guide

For comprehensive testing instructions, see:
- **`TESTING_GUIDE.md`** - Complete testing documentation
  - Local testing (no cluster needed)
  - Testing with real SLURM data
  - End-to-end testing
  - Multi-cluster testing
  - Troubleshooting

## Deployment Guides

Once testing is complete:
- **`cluster-agent/QUICKSTART.md`** - 5-minute cluster deployment
- **`cluster-agent/README.md`** - Complete agent documentation
- **`CLUSTER_DEPLOYMENT.md`** - Full deployment guide
- **`ARCHITECTURE_OVERVIEW.md`** - System architecture

## Quick Reference

### Start Backend
```bash
cd backend
uvicorn app.main:app --reload --port 8100
```

### Start Frontend
```bash
cd frontend
npm run dev
```

### Test API
```bash
# Health
curl http://localhost:8100/api/dashboard/health

# Metadata
curl http://localhost:8100/api/dashboard/metadata

# Submit data
curl -X POST http://localhost:8100/api/data/ingest \
  -H "X-API-Key: test-secret-key-12345" \
  -H "Content-Type: application/json" \
  -d '{"hostname":"test","jobs":[]}'
```

### Stop Backend (if started by quick_test.sh)
```bash
kill $(cat backend.pid)
```

## Cleanup Test Data

```bash
# Remove test data
rm -rf data/test-cluster

# Remove test files
rm -f test_data.json backend.log backend.pid
```

## Need Help?

- Backend won't start? Check `backend.log`
- API errors? See **`TESTING_GUIDE.md`** troubleshooting section
- Questions? See **`ARCHITECTURE_OVERVIEW.md`** for system design

## Summary

Three ways to test:

1. **Quick automated test**: `./quick_test.sh` (recommended)
2. **Manual API test**: `cluster-agent/test_api.sh`
3. **Full deployment test**: See `TESTING_GUIDE.md`

All tests use `test-secret-key-12345` as the API key by default.
