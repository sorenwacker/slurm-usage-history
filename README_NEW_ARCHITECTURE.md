# Slurm Usage History - New Web Application

This is a reimplementation of the Slurm Usage History dashboard as a modern web application with API capabilities.

## Architecture

### Backend: FastAPI
- **Location**: `/backend`
- **Framework**: FastAPI with Python 3.10+
- **Features**:
  - RESTful API for dashboard data
  - API key authentication for data ingestion
  - Automatic data refresh
  - Reuses existing PandasDataStore

### Frontend: React + TypeScript
- **Location**: `/frontend`
- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **Features**:
  - Modern, responsive dashboard UI
  - Interactive Plotly charts
  - Advanced filtering capabilities
  - Real-time data updates

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- uv (Python package manager)

### 1. Install Dependencies

**Backend**:
```bash
uv sync
```

**Frontend**:
```bash
cd frontend
npm install
```

### 2. Configuration

**Root `.env` file**:
```bash
# API Keys for data ingestion (comma-separated)
API_KEYS=your-secret-key-1,your-secret-key-2

# Data directory path
DATA_PATH=./data

# Auto-refresh interval in seconds
AUTO_REFRESH_INTERVAL=600

# CORS origins for frontend
CORS_ORIGINS=http://localhost:3100
```

**Frontend `.env` file**:
```bash
cd frontend
cp .env.example .env
# Default VITE_API_URL=http://localhost:8100
```

### 3. Start the Application

**Terminal 1 - Backend**:
```bash
cd backend
python run.py
```
Backend will run on `http://localhost:8100`
API docs available at `http://localhost:8100/docs`

**Terminal 2 - Frontend**:
```bash
cd frontend
npm run dev
```
Frontend will run on `http://localhost:3100`

## API Endpoints

### Data Ingestion

**POST /api/data/ingest**
- **Auth**: Requires `X-API-Key` header
- **Purpose**: Submit job data for storage
- **Request Body**:
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

### Dashboard API

**GET /api/dashboard/health** - Health check

**GET /api/dashboard/metadata** - Get available filters and date ranges

**POST /api/dashboard/filter** - Filter and query job data

**GET /api/dashboard/stats/{hostname}** - Get cluster statistics

## Example: Ingesting Data

```bash
curl -X POST "http://localhost:8100/api/data/ingest" \
  -H "X-API-Key: your-secret-key-1" \
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

## Project Structure

```
slurm-usage-history/
├── backend/
│   ├── app/
│   │   ├── api/           # API endpoints
│   │   ├── core/          # Configuration and auth
│   │   ├── models/        # Pydantic models
│   │   └── main.py        # FastAPI app
│   ├── run.py             # Development server
│   └── README.md
├── frontend/
│   ├── src/
│   │   ├── api/           # API client
│   │   ├── components/    # React components
│   │   ├── pages/         # Page components
│   │   ├── types/         # TypeScript types
│   │   └── App.tsx
│   ├── package.json
│   └── README.md
├── src/                   # Original Dash application
│   └── slurm_usage_history/
│       └── app/
│           └── datastore.py  # Reused by backend
├── data/                  # Job data storage
├── .env                   # Configuration
└── pyproject.toml
```

## Features

### Data Ingestion
- Secure API endpoint with key authentication
- Automatic parquet file generation with derived columns
- Support for multiple clusters

### Dashboard
- Real-time visualization of CPU/GPU usage
- Job statistics by account, partition, and state
- Time-based filtering
- Interactive charts
- Responsive design

### Data Management
- Automatic data refresh (configurable interval)
- Efficient parquet storage
- Pandas-based querying

## Production Deployment

### Backend
```bash
gunicorn backend.app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8100
```

### Frontend
```bash
cd frontend
npm run build
# Serve dist/ directory with nginx or similar
```

## Migration from Plotly Dash

The new application replaces the Plotly Dash implementation with:
- Separated backend API (FastAPI) and frontend (React)
- API endpoint for external data ingestion
- Modern, maintainable codebase
- Better performance and scalability

The original Dash application code remains in `src/slurm_usage_history/app/` and the datastore is reused by the new backend.

## Documentation

- [Backend README](backend/README.md)
- [Frontend README](frontend/README.md)
- API Documentation: http://localhost:8100/docs (when running)

## License

GPLv3+
