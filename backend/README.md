# Slurm Usage History - Backend API

FastAPI-based backend for the Slurm Usage History dashboard with data ingestion capabilities.

## Features

- **Data Ingestion API**: POST endpoint to submit job data with API key authentication
- **Dashboard API**: Query endpoints for retrieving and filtering job data
- **Auto-refresh**: Automatic data reload when new files are detected
- **CORS enabled**: Ready for frontend integration

## Setup

1. Install dependencies with uv:
```bash
uv sync
```

2. Configure environment variables:
```bash
cp backend/.env.example backend/.env
# Edit .env and configure DATA_PATH, ADMIN_USERNAME, etc.
```

3. Run the development server:
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8100
```

The API will be available at `http://localhost:8100`

API documentation is available at `http://localhost:8100/docs`

## API Endpoints

### Data Ingestion

**POST /api/data/ingest**
- Requires `X-API-Key` header
- Submit job data for a cluster
- Request body:
```json
{
  "hostname": "cluster01",
  "jobs": [
    {
      "JobID": "12345",
      "User": "username",
      "Account": "project-account",
      "Partition": "compute",
      "State": "COMPLETED",
      "QOS": "normal",
      "Submit": "2024-01-01T10:00:00",
      "Start": "2024-01-01T10:05:00",
      "End": "2024-01-01T11:00:00",
      "CPUHours": 4.5,
      "GPUHours": 0.0,
      "AllocCPUS": 4,
      "AllocGPUS": 0,
      "AllocNodes": 1,
      "NodeList": "node001"
    }
  ]
}
```

### Dashboard Endpoints

**GET /api/dashboard/health**
- Health check endpoint

**GET /api/dashboard/metadata**
- Get metadata for all clusters (available filters, date ranges)

**POST /api/dashboard/filter**
- Filter job data with criteria
- Request body:
```json
{
  "hostname": "cluster01",
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "partitions": ["compute"],
  "accounts": ["project-account"],
  "users": null,
  "qos": null,
  "states": ["COMPLETED"]
}
```

**GET /api/dashboard/stats/{hostname}**
- Get statistics for a specific cluster

## Example: Ingest Data

```bash
curl -X POST "http://localhost:8100/api/data/ingest" \
  -H "X-API-Key: your-secret-api-key-1" \
  -H "Content-Type: application/json" \
  -d '{
    "hostname": "cluster01",
    "jobs": [
      {
        "JobID": "12345",
        "User": "testuser",
        "Account": "test-project",
        "Partition": "compute",
        "State": "COMPLETED",
        "Submit": "2024-01-01T10:00:00",
        "Start": "2024-01-01T10:05:00",
        "End": "2024-01-01T11:00:00",
        "CPUHours": 4.5,
        "GPUHours": 0.0,
        "AllocCPUS": 4,
        "AllocGPUS": 0,
        "AllocNodes": 1
      }
    ]
  }'
```

## Production Deployment

For production, use uvicorn with gunicorn:

```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8100
```
