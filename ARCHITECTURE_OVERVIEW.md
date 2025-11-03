# SLURM Usage History - Complete Architecture

## Overview

The SLURM Usage History system is designed to collect job data from **multiple SLURM clusters** and display it in a unified dashboard. The architecture consists of three main components:

1. **Cluster Agents** - Deployed on each SLURM cluster
2. **Backend API** - Centralized data ingestion and query service
3. **Frontend Dashboard** - Web-based visualization interface

## Multi-Cluster Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│ Cluster 1 (hpc-cluster-01)                                      │
│                                                                  │
│  ┌────────────────────────────────────────┐                    │
│  │ slurm-usage-history-exporter           │                    │
│  │ - Extracts job data via sacct          │                    │
│  │ - Submits as "hpc-cluster-01"          │                    │
│  └──────────────────┬─────────────────────┘                    │
└────────────────────┼──────────────────────────────────────────┘
                     │
                     │ HTTPS POST /api/data/ingest
                     │ X-API-Key: shared-secret
                     │ {"hostname": "hpc-cluster-01", "jobs": [...]}
                     │
┌─────────────────────────────────────────────────────────────────┐
│ Cluster 2 (gpu-cluster-02)                                      │
│                                                                  │
│  ┌────────────────────────────────────────┐                    │
│  │ slurm-usage-history-exporter           │                    │
│  │ - Extracts job data via sacct          │                    │
│  │ - Submits as "gpu-cluster-02"          │                    │
│  └──────────────────┬─────────────────────┘                    │
└────────────────────┼──────────────────────────────────────────┘
                     │
                     │ HTTPS POST /api/data/ingest
                     │ X-API-Key: shared-secret
                     │ {"hostname": "gpu-cluster-02", "jobs": [...]}
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ Dashboard Server                                                 │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Backend API (FastAPI)                                     │  │
│  │                                                            │  │
│  │ POST /api/data/ingest                                     │  │
│  │  - Validates API key (supports multiple clusters)        │  │
│  │  - Routes data by hostname                                │  │
│  │  - Stores: data/{hostname}/weekly-data/*.parquet         │  │
│  │                                                            │  │
│  │ GET /api/dashboard/metadata                               │  │
│  │  - Returns available clusters and filters                │  │
│  │                                                            │  │
│  │ POST /api/dashboard/filter                                │  │
│  │  - Queries data for specific cluster                     │  │
│  └──────────────────────┬───────────────────────────────────┘  │
│                         │                                        │
│  ┌──────────────────────▼───────────────────────────────────┐  │
│  │ Data Storage (Organized by Cluster)                      │  │
│  │                                                            │  │
│  │ data/                                                     │  │
│  │ ├── hpc-cluster-01/                                       │  │
│  │ │   └── weekly-data/                                      │  │
│  │ │       ├── jobs_20241031_120000.parquet                 │  │
│  │ │       └── jobs_20241101_120000.parquet                 │  │
│  │ │                                                          │  │
│  │ └── gpu-cluster-02/                                       │  │
│  │     └── weekly-data/                                      │  │
│  │         ├── jobs_20241031_120000.parquet                 │  │
│  │         └── jobs_20241101_120000.parquet                 │  │
│  └──────────────────────┬───────────────────────────────────┘  │
│                         │                                        │
│  ┌──────────────────────▼───────────────────────────────────┐  │
│  │ Frontend (React)                                          │  │
│  │                                                            │  │
│  │ - Cluster selection dropdown                             │  │
│  │ - Filters per cluster (partitions, accounts, users)      │  │
│  │ - Visualizations (charts, tables)                        │  │
│  └────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Cluster Agent (`slurm-usage-history-exporter`)

**Location:** Installed on each SLURM cluster
**Purpose:** Extract job data and submit to dashboard

**Features:**
- Auto-detects cluster name from SLURM config
- Extracts completed jobs via `sacct`
- Calculates CPU-hours, GPU-hours, resource metrics
- Submits to central API with cluster identifier
- Runs automatically (daily via systemd timer)

**Configuration:**
```json
{
  "api_url": "https://dashboard.example.com",
  "api_key": "shared-secret-key",
  "cluster_name": "hpc-cluster-01"
}
```

**Installation:** See `cluster-agent/QUICKSTART.md`

### 2. Backend API

**Location:** Centralized dashboard server
**Technology:** FastAPI + Python
**Purpose:** Receive data from multiple clusters, store, and serve queries

#### Key Endpoints

##### Data Ingestion (requires API key)

```http
POST /api/data/ingest
Headers:
  X-API-Key: your-secret-api-key
  Content-Type: application/json

Body:
{
  "hostname": "hpc-cluster-01",
  "jobs": [
    {
      "JobID": "12345",
      "User": "username",
      "Account": "project-a",
      "Partition": "compute",
      "State": "COMPLETED",
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
```

**Response:**
```json
{
  "success": true,
  "message": "Successfully ingested 1 jobs for hpc-cluster-01",
  "jobs_processed": 1,
  "hostname": "hpc-cluster-01"
}
```

**What it does:**
1. Validates API key from `X-API-Key` header
2. Creates directory structure: `data/{hostname}/weekly-data/`
3. Converts job records to pandas DataFrame
4. Adds derived columns (SubmitDay, SubmitYearMonth, WaitingTime, etc.)
5. Saves as timestamped parquet file: `jobs_{timestamp}.parquet`
6. Returns success response

##### Dashboard Queries (no auth required)

```http
GET /api/dashboard/health
```
Returns health status and list of available clusters

```http
GET /api/dashboard/metadata
```
Returns metadata for all clusters:
- Available clusters (hostnames)
- Partitions per cluster
- Accounts per cluster
- Users per cluster
- Date ranges per cluster

```http
POST /api/dashboard/filter
Body:
{
  "hostname": "hpc-cluster-01",
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "partitions": ["compute"],
  "accounts": ["project-a"]
}
```
Returns filtered job data for specified cluster

#### Multi-Cluster Support

The backend **automatically supports multiple clusters** through:

1. **Hostname-based routing:** Each cluster's data is stored in `data/{hostname}/`
2. **Shared API key:** All clusters can use the same API key (or different keys)
3. **Automatic metadata indexing:** Frontend dropdowns automatically populated
4. **Independent filtering:** Each cluster's data is queried separately

#### Authentication

**API Key Configuration (`backend/.env`):**
```bash
# Comma-separated list of valid API keys
API_KEYS=secret-key-1,secret-key-2,secret-key-3

# All clusters can share the same key
# Or each cluster can have its own key
```

**Security:**
- Required for data ingestion only
- Validated via `X-API-Key` header
- Dashboard queries don't require auth (read-only)
- Uses FastAPI Security with APIKeyHeader

### 3. Frontend Dashboard

**Location:** Dashboard server
**Technology:** React + TypeScript + Vite
**Purpose:** Visualize data from all clusters

**Features:**
- Cluster selection (dropdown populated from metadata)
- Date range filtering
- Multi-select filters (partitions, accounts, users, QOS)
- Interactive charts (Plotly.js)
- Resource utilization metrics
- Job statistics and trends

**Cluster Selection:**
The frontend automatically detects available clusters by calling `/api/dashboard/metadata` and populating the cluster dropdown.

## Data Flow

### Ingestion Flow

```
1. Cluster Agent runs (daily at 2:00 AM)
   ↓
2. Extracts jobs via: sacct --allusers --starttime=... --endtime=...
   ↓
3. Formats data (parses AllocTRES, calculates metrics)
   ↓
4. Submits to API:
   POST /api/data/ingest
   X-API-Key: {key}
   {"hostname": "cluster-name", "jobs": [...]}
   ↓
5. Backend validates API key
   ↓
6. Backend creates/updates: data/{hostname}/weekly-data/jobs_{timestamp}.parquet
   ↓
7. Backend returns success response
   ↓
8. Auto-refresh picks up new data (every 10 minutes by default)
```

### Query Flow

```
1. User opens dashboard in browser
   ↓
2. Frontend requests metadata: GET /api/dashboard/metadata
   ↓
3. Backend scans all data directories
   ↓
4. Backend returns available clusters and filters
   ↓
5. Frontend populates dropdowns
   ↓
6. User selects cluster and filters
   ↓
7. Frontend submits filter request: POST /api/dashboard/filter
   ↓
8. Backend loads parquet files for specified cluster
   ↓
9. Backend filters and aggregates data
   ↓
10. Backend returns filtered results
   ↓
11. Frontend renders charts and tables
```

## File Structure

```
slurm-usage-history/
├── cluster-agent/                          # Deploy to each SLURM cluster
│   ├── slurm-usage-history-exporter.py     # Main extraction script
│   ├── slurm-usage-history-exporter.service # Systemd service
│   ├── slurm-usage-history-exporter.timer   # Systemd timer
│   ├── install.sh                           # Installation script
│   ├── config.json.example                  # Configuration template
│   └── README.md                            # Documentation
│
├── backend/                                 # Dashboard server
│   ├── app/
│   │   ├── api/
│   │   │   ├── data.py                     # POST /api/data/ingest
│   │   │   └── dashboard.py                # Dashboard query endpoints
│   │   ├── core/
│   │   │   ├── auth.py                     # API key authentication
│   │   │   └── config.py                   # Settings from .env
│   │   ├── models/
│   │   │   └── data_models.py              # Pydantic models
│   │   └── main.py                         # FastAPI app
│   ├── .env.example                         # Configuration template
│   └── requirements.txt
│
├── frontend/                                # Dashboard UI
│   ├── src/
│   │   ├── components/
│   │   ├── services/
│   │   └── App.tsx
│   └── package.json
│
└── data/                                    # Data storage (created automatically)
    ├── cluster-01/
    │   └── weekly-data/
    │       ├── jobs_20241031_120000.parquet
    │       └── jobs_20241101_120000.parquet
    ├── cluster-02/
    │   └── weekly-data/
    │       └── jobs_20241031_120000.parquet
    └── cluster-03/
        └── weekly-data/
            └── jobs_20241031_120000.parquet
```

## Adding a New Cluster

To add a new SLURM cluster to the system:

### Step 1: Configure Backend (if not already done)

On dashboard server:

```bash
cd /path/to/slurm-usage-history/backend

# Edit .env file
nano .env

# Ensure API_KEYS is set
API_KEYS=your-secret-key
```

### Step 2: Deploy Agent to New Cluster

On the new SLURM cluster:

```bash
# Copy cluster-agent directory
scp -r cluster-agent/ user@new-cluster:/tmp/

# SSH and install
ssh user@new-cluster
cd /tmp/cluster-agent
sudo ./install.sh

# Configure
sudo nano /etc/slurm-usage-history-exporter/config.json
```

Set configuration:
```json
{
  "api_url": "https://your-dashboard.example.com",
  "api_key": "your-secret-key",
  "cluster_name": "new-cluster-name"
}
```

### Step 3: Test

```bash
# Test extraction
sudo slurm-usage-history-exporter --dry-run --verbose

# Submit test data
sudo slurm-usage-history-exporter

# Enable automatic collection
sudo systemctl enable slurm-usage-history-exporter.timer
sudo systemctl start slurm-usage-history-exporter.timer
```

### Step 4: Verify

1. Check logs: `journalctl -u slurm-usage-history-exporter.service -f`
2. Check data appeared: `ls data/new-cluster-name/weekly-data/`
3. Open dashboard and select new cluster from dropdown

**That's it!** The new cluster will automatically appear in the dashboard.

## Configuration Reference

### Cluster Agent Configuration

**Location:** `/etc/slurm-usage-history-exporter/config.json`

```json
{
  "api_url": "https://dashboard.example.com",
  "api_key": "secret-key",
  "cluster_name": "optional-override",
  "timeout": 30,
  "collection_window_days": 7
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `api_url` | Yes | Dashboard backend URL (with https://) |
| `api_key` | Yes | API key for authentication |
| `cluster_name` | No | Override auto-detected cluster name |
| `timeout` | No | HTTP timeout in seconds (default: 30) |
| `collection_window_days` | No | Days of data to collect (default: 7) |

### Backend Configuration

**Location:** `/path/to/backend/.env`

```bash
# API Keys (comma-separated)
API_KEYS=key1,key2,key3

# Data storage path
DATA_PATH=../data

# Auto-refresh interval (seconds)
AUTO_REFRESH_INTERVAL=600

# CORS origins (comma-separated)
CORS_ORIGINS=http://localhost:3100,https://dashboard.example.com
```

| Variable | Description |
|----------|-------------|
| `API_KEYS` | Comma-separated list of valid API keys |
| `DATA_PATH` | Path to data directory (absolute or relative) |
| `AUTO_REFRESH_INTERVAL` | How often to check for new data files (seconds) |
| `CORS_ORIGINS` | Allowed CORS origins for frontend |

## Security Considerations

### API Key Management

1. **Generation:** Use strong random keys
   ```bash
   python3 -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **Distribution:** Securely share keys with cluster admins
3. **Rotation:** Change keys periodically, update all clusters
4. **Storage:** Keep `.env` file permissions at 600

### Network Security

1. **Use HTTPS:** Always use HTTPS in production for `api_url`
2. **Firewall Rules:** Allow only necessary traffic between clusters and dashboard
3. **API Rate Limiting:** Consider adding rate limits to `/api/data/ingest`

### Data Privacy

1. **Job Metadata Only:** Only job accounting data is collected (no job content)
2. **User Privacy:** Dashboard can be configured to anonymize usernames
3. **Access Control:** Consider adding authentication to dashboard queries

## Monitoring

### Backend Health

```bash
# Check if backend is running
curl https://your-dashboard.example.com/api/dashboard/health

# Check available clusters
curl https://your-dashboard.example.com/api/dashboard/metadata
```

### Cluster Agent Health

On each cluster:

```bash
# Check timer status
systemctl status slurm-usage-history-exporter.timer

# View recent logs
journalctl -u slurm-usage-history-exporter.service -n 50

# Check last submission
ls -lth /path/to/data/{cluster-name}/weekly-data/ | head
```

## Troubleshooting

### Cluster Not Appearing in Dashboard

1. **Check agent logs:** `journalctl -u slurm-usage-history-exporter.service`
2. **Verify API key:** Compare cluster config with backend `.env`
3. **Test connectivity:** `curl -I https://dashboard.example.com/api/dashboard/health`
4. **Check data files:** `ls data/{cluster-name}/weekly-data/`

### Authentication Errors (401/403)

1. **Verify API key matches** between cluster config and backend `.env`
2. **Check for whitespace** in keys
3. **Test manually:**
   ```bash
   curl -X POST https://dashboard.example.com/api/data/ingest \
     -H "X-API-Key: your-key" \
     -H "Content-Type: application/json" \
     -d '{"hostname":"test","jobs":[]}'
   ```

### Data Not Updating

1. **Check auto-refresh interval:** Default is 600 seconds (10 minutes)
2. **Manually trigger refresh:** Restart backend
3. **Verify parquet files exist:** `ls data/*/weekly-data/*.parquet`

## Performance

### Scalability

- **Clusters:** No hard limit, tested with 10+ clusters
- **Jobs per submission:** Tested with 100K+ jobs per submission
- **Data retention:** Parquet files are efficient, 1 year ≈ 500MB per cluster
- **Query performance:** In-memory pandas DataFrames, sub-second queries

### Optimization

1. **Data pruning:** Periodically archive old parquet files
2. **Batch size:** Submit data in reasonable batches (1-7 days at a time)
3. **Caching:** Backend uses LRU cache for frequently accessed queries
4. **Compression:** Parquet files are automatically compressed

## Summary

The SLURM Usage History system is designed for **multi-cluster deployments**:

✅ **Already supports multiple clusters** - No code changes needed
✅ **Easy to add new clusters** - Deploy agent, configure, done
✅ **Centralized management** - Single dashboard for all clusters
✅ **Automatic discovery** - Clusters appear automatically
✅ **Secure** - API key authentication, HTTPS support
✅ **Scalable** - Handles many clusters and large datasets

The backend `/api/data/ingest` endpoint is **ready to receive data from as many clusters as you need**.
