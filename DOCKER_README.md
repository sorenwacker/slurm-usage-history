# Docker Deployment Guide

This guide explains how to run the Slurm Usage History application using Docker.

## Prerequisites

- Docker (version 20.10+)
- Docker Compose (version 2.0+)

## Quick Start

1. **Configure environment variables**:
```bash
# Make sure your .env file has the required variables:
cat > .env << 'EOF'
# API Keys for data ingestion (comma-separated)
API_KEYS=dev-api-key-12345,prod-api-key-67890

# Auto-refresh interval in seconds
AUTO_REFRESH_INTERVAL=600
EOF
```

2. **Build and start the containers**:
```bash
docker-compose up -d
```

3. **Access the application**:
- Frontend: http://localhost:3100
- Backend API: http://localhost:8100
- API Documentation: http://localhost:8100/docs

## Services

### Backend
- **Port**: 8100
- **Framework**: FastAPI
- **Features**: API endpoints, data ingestion, auto-refresh

### Frontend
- **Port**: 3100
- **Server**: Nginx
- **Framework**: React + TypeScript

## Data Persistence

Job data is stored in the `./data` directory, which is mounted as a volume in the backend container. This ensures data persists across container restarts.

## Common Commands

### Start services
```bash
docker-compose up -d
```

### Stop services
```bash
docker-compose down
```

### View logs
```bash
# All services
docker-compose logs -f

# Backend only
docker-compose logs -f backend

# Frontend only
docker-compose logs -f frontend
```

### Rebuild after code changes
```bash
docker-compose up -d --build
```

### Remove all containers and volumes
```bash
docker-compose down -v
```

## Environment Variables

Configure these in your `.env` file:

- **API_KEYS**: Comma-separated list of API keys for data ingestion
- **AUTO_REFRESH_INTERVAL**: How often to check for new data files (in seconds)

## Data Ingestion Example

Once the containers are running, you can ingest data:

```bash
curl -X POST "http://localhost:8100/api/data/ingest" \
  -H "X-API-Key: dev-api-key-12345" \
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

## Troubleshooting

### Backend container won't start
```bash
# Check logs
docker-compose logs backend

# Check if data directory exists and has correct permissions
ls -la ./data
```

### Frontend can't connect to backend
- Ensure both containers are running: `docker-compose ps`
- Check backend logs: `docker-compose logs backend`
- Verify the CORS_ORIGINS setting in docker-compose.yml

### Port conflicts
If ports 3100 or 8100 are already in use, modify the port mappings in `docker-compose.yml`:

```yaml
services:
  backend:
    ports:
      - "8200:8100"  # Map host port 8200 to container port 8100

  frontend:
    ports:
      - "3200:3100"  # Map host port 3200 to container port 3100
```

## Development vs Production

### Development Mode
For development, use the non-Docker setup described in README_NEW_ARCHITECTURE.md to get hot-reload and faster iteration.

### Production Mode
Docker deployment is recommended for production:

```bash
# Use production environment file
cp .env.production .env

# Build and deploy
docker-compose up -d --build

# Monitor
docker-compose logs -f
```

## Scaling

To run multiple backend workers:

```yaml
services:
  backend:
    deploy:
      replicas: 4
```

Or use a production-grade orchestration tool like Kubernetes.

## Security Notes

- Change default API keys in production
- Use HTTPS in production (add reverse proxy like Traefik or nginx)
- Restrict CORS origins to your actual domain
- Consider using Docker secrets for sensitive data
- Run containers as non-root users in production

## Health Checks

Check if services are healthy:

```bash
# Backend health
curl http://localhost:8100/api/dashboard/health

# Frontend (should return HTML)
curl http://localhost:3100
```

## Backup

Backup your data directory regularly:

```bash
tar -czf slurm-data-backup-$(date +%Y%m%d).tar.gz ./data
```
