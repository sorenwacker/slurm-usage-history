# Slurm Usage History - Docker Quick Start

Modern web application for visualizing SLURM cluster usage with API-based data ingestion.

## 🚀 Quick Start with Docker

### 1. Configure API Keys

```bash
# Edit .env and set your API keys
nano .env

# Or use this example:
cat > .env << 'ENVEOF'
API_KEYS=your-secret-key-here
AUTO_REFRESH_INTERVAL=600
ENVEOF
```

### 2. Start the Application

```bash
docker-compose up -d
```

That's it! The application is now running:

- 🌐 **Dashboard**: http://localhost:3100
- 🔌 **API**: http://localhost:8100
- 📚 **API Docs**: http://localhost:8100/docs

### 3. Ingest Data

```bash
curl -X POST "http://localhost:8100/api/data/ingest" \
  -H "X-API-Key: your-secret-key-here" \
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

## 📦 What's Included

- **Backend**: FastAPI with automatic data refresh
- **Frontend**: React dashboard with interactive charts
- **Data Storage**: Persistent volume for job data
- **API Authentication**: Secure data ingestion with API keys

## 🛠️ Common Commands

```bash
# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild after changes
docker-compose up -d --build

# Check status
docker-compose ps
```

## 📖 Documentation

- [Docker Deployment Guide](DOCKER_README.md) - Detailed Docker usage
- [Full Architecture](README_NEW_ARCHITECTURE.md) - Complete documentation
- [Backend API](backend/README.md) - API reference
- [Frontend](frontend/README.md) - Frontend details

## 🔧 Development

For local development without Docker, see [README_NEW_ARCHITECTURE.md](README_NEW_ARCHITECTURE.md).

## 📊 Features

- Real-time visualization of CPU/GPU usage
- Filter by cluster, date, partition, account, and state
- Secure API endpoint for data ingestion
- Automatic data refresh
- Responsive, modern UI
- REST API with OpenAPI documentation
