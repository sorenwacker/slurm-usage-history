# Local Development Setup with Docker and SAML

This guide explains how to set up a complete local development environment with SAML authentication using Docker.

## Prerequisites

- Docker Desktop installed and running
- Docker Compose v2.0+
- At least 4GB RAM available for Docker

## Quick Start

### 1. Start the Development Environment

```bash
# Build and start all services
docker-compose -f docker-compose.dev.yml up --build

# Or run in detached mode
docker-compose -f docker-compose.dev.yml up --build -d
```

### 2. Access the Services

Once all containers are running:

- **Dashboard**: http://localhost:8100
- **Frontend Dev Server**: http://localhost:5173 (with hot reload)
- **SAML IdP**: http://localhost:8080/simplesaml
- **API Documentation**: http://localhost:8100/docs

### 3. Test SAML Login

Visit http://localhost:8100 and you'll be redirected to the SAML login page.

**Test Users:**

| Username | Password | Role | Description |
|----------|----------|------|-------------|
| admin | admin | Admin | Full admin access |
| user | user | User | Regular user access |
| testuser | testuser | User | Another test user |

### 4. Stop the Environment

```bash
# Stop all containers
docker-compose -f docker-compose.dev.yml down

# Stop and remove volumes (clean slate)
docker-compose -f docker-compose.dev.yml down -v
```

## Architecture

The development environment consists of three containers:

```
┌─────────────────────────────────────────────────────────────┐
│  Browser                                                     │
└───────┬──────────────────────────────┬──────────────────────┘
        │                              │
        │ http://localhost:8100        │ http://localhost:8080
        │                              │
        ▼                              ▼
┌─────────────────┐          ┌────────────────────┐
│  Backend        │          │  SAML IdP          │
│  (FastAPI)      │◄────────►│  (SimpleSAMLphp)   │
│  Port: 8100     │          │  Port: 8080        │
└─────────────────┘          └────────────────────┘
        ▲
        │
        │ API calls
        │
┌─────────────────┐
│  Frontend       │
│  (Vite/React)   │
│  Port: 5173     │
└─────────────────┘
```

## Services

### Backend (FastAPI)

- **Port**: 8100
- **Container**: `slurm-backend-dev`
- **Hot Reload**: Enabled (changes to `backend/` directory reload automatically)
- **SAML**: Enabled with SimpleSAMLphp IdP
- **Data**: `./data` mounted as `/data`

**Environment Variables:**
- `ENABLE_SAML=true`
- `SAML_SETTINGS_PATH=/app/saml/settings.json`
- `DEBUG=true`
- `RELOAD=true`

### Frontend (React + Vite)

- **Port**: 5173
- **Container**: `slurm-frontend-dev`
- **Hot Reload**: Enabled (changes to `frontend/` directory reload automatically)
- **API URL**: Configured to use `http://localhost:8100`

### SAML Identity Provider (SimpleSAMLphp)

- **Port**: 8080
- **Container**: `slurm-saml-idp`
- **Admin Interface**: http://localhost:8080/simplesaml
- **Test Users**: Configured in `docker/saml-idp/authsources.php`

## Development Workflow

### Making Backend Changes

1. Edit files in `backend/` directory
2. The backend will automatically reload (hot reload enabled)
3. Check logs: `docker-compose -f docker-compose.dev.yml logs -f backend`

### Making Frontend Changes

1. Edit files in `frontend/` directory
2. Vite dev server will hot reload automatically
3. Access at http://localhost:5173
4. Check logs: `docker-compose -f docker-compose.dev.yml logs -f frontend`

### SAML Configuration

SAML settings are in `docker/saml-config/settings.json`. Changes require backend restart:

```bash
docker-compose -f docker-compose.dev.yml restart backend
```

### Adding Test Users

Edit `docker/saml-idp/authsources.php` and restart the IdP:

```bash
docker-compose -f docker-compose.dev.yml restart saml-idp
```

## Testing SAML Flow

1. **Visit Dashboard**: http://localhost:8100
2. **Redirect to IdP**: Automatically redirected to SimpleSAMLphp login
3. **Login**: Use test credentials (admin/admin)
4. **Return to Dashboard**: After successful auth, redirected back with session

### SAML Endpoints

- **SP Metadata**: http://localhost:8100/saml/metadata
- **SAML Status**: http://localhost:8100/saml/status
- **Current User**: http://localhost:8100/saml/me (requires auth)
- **IdP Metadata**: http://localhost:8080/simplesaml/saml2/idp/metadata.php

## Creating Test Data

If you don't have SLURM data, you can generate test data:

```bash
# Generate test data for a cluster
docker-compose -f docker-compose.dev.yml exec backend \
  python scripts/generate_test_cluster_data.py \
  --output /data/TESTCLUSTER \
  --weeks 4
```

## Troubleshooting

### Backend won't start

```bash
# Check backend logs
docker-compose -f docker-compose.dev.yml logs backend

# Common issues:
# - Port 8100 already in use
# - SAML certificates not generated
# - Missing dependencies
```

### SAML login fails

```bash
# Check SAML configuration
docker-compose -f docker-compose.dev.yml exec backend \
  cat /app/saml/settings.json

# Check SAML certificates
docker-compose -f docker-compose.dev.yml exec backend \
  ls -la /app/saml/certs/

# Check IdP is accessible from backend
docker-compose -f docker-compose.dev.yml exec backend \
  curl -v http://saml-idp:8080/simplesaml/saml2/idp/metadata.php
```

### Port conflicts

If ports 8100, 5173, or 8080 are already in use, edit `docker-compose.dev.yml` and change the port mappings:

```yaml
ports:
  - "9100:8100"  # Change 9100 to any free port
```

### Clean rebuild

```bash
# Stop everything and remove volumes
docker-compose -f docker-compose.dev.yml down -v

# Remove images
docker-compose -f docker-compose.dev.yml down --rmi all

# Rebuild from scratch
docker-compose -f docker-compose.dev.yml up --build
```

## Accessing Containers

```bash
# Backend shell
docker-compose -f docker-compose.dev.yml exec backend /bin/bash

# Frontend shell
docker-compose -f docker-compose.dev.yml exec frontend /bin/sh

# IdP shell
docker-compose -f docker-compose.dev.yml exec saml-idp /bin/bash
```

## Database Access

DuckDB database files are in `./data/`. You can query them directly:

```bash
# Install DuckDB CLI
brew install duckdb  # macOS
# or use Docker
docker run -it -v $(pwd)/data:/data duckdb/duckdb

# Query data
docker-compose -f docker-compose.dev.yml exec backend \
  python -c "import duckdb; conn = duckdb.connect(); conn.execute('SELECT * FROM read_parquet(\"/data/TESTCLUSTER/weekly-data/*.parquet\") LIMIT 10').fetchall()"
```

## Production vs Development

### Key Differences

| Feature | Development | Production |
|---------|-------------|-----------|
| Hot Reload | ✓ Enabled | ✗ Disabled |
| Debug Mode | ✓ Enabled | ✗ Disabled |
| SAML Strict | ✗ Disabled | ✓ Enabled |
| CORS | Wide open | Restricted |
| HTTPS | Not required | Required |
| Certificates | Self-signed | Real certs |

### Switching to Production

Use `docker-compose.yml` instead of `docker-compose.dev.yml`:

```bash
docker-compose up --build
```

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SimpleSAMLphp Documentation](https://simplesamlphp.org/docs/stable/)
- [python3-saml Documentation](https://github.com/SAML-Toolkits/python3-saml)
- [Project README](README.md)
