# SLURM Dashboard

Web dashboard for SLURM cluster usage analytics powered by DuckDB.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

**[Documentation](https://sdrwacker.pages.ewi.tudelft.nl/slurm-usage-history)** | **[GitHub](https://github.com/tudelft-reit/slurm-dashboard)**

## Key Features

- **92% less memory** (13GB → 1.1GB) and **15x faster** queries with DuckDB
- React + FastAPI interface with interactive charts
- SAML 2.0 authentication with admin panel
- Multi-cluster management with API key authentication
- Auto-generate cluster configurations from existing data
- Demo cluster generation with synthetic data
- PDF report generation with customizable templates

## Quick Start with Docker (Demo)

Try the dashboard with synthetic demo data in 3 steps:

```bash
# 1. Start the dashboard
docker-compose up -d

# 2. Generate demo data (2 years, 110k jobs with realistic patterns)
docker-compose exec backend python scripts/generate_test_cluster_data.py \
  --cluster DemoCluster --start-date 2023-01-01 --end-date 2024-12-31

# 3. Open http://localhost:3100 and select "DemoCluster" from the dropdown
```

The demo cluster includes seasonal patterns, simulated outages, and realistic job distributions.

## Production Setup

### 1. Install

```bash
pip install slurm-dashboard[all]
```

### 2. Collect Data (on SLURM cluster)

```bash
# Collect job data from SLURM and save to shared storage
slurm-dashboard-agent --output /shared/slurm-data/$(hostname)
```

This extracts job data from SLURM using `sacct` and saves it as Parquet files.

### 3. Start Dashboard (on dashboard server)

```bash
# Point to the data directory and start the web server
export DATA_PATH=/shared/slurm-data
slurm-dashboard
```

Access at **http://localhost:8100**

See [documentation](https://sdrwacker.pages.ewi.tudelft.nl/slurm-usage-history) for production deployment with SAML, systemd, and multi-cluster setup.

## Admin Panel

Access the admin panel at **http://localhost:8100/admin/login** to:

- **Manage Clusters**: Add, activate/deactivate, and configure multiple SLURM clusters
- **Generate Demo Data**: Create synthetic cluster data for testing with realistic patterns
- **Auto-generate Configs**: Automatically detect nodes, accounts, and partitions from data
- **User Management**: Control access and view user activity
- **API Keys**: Manage authentication keys for data submission agents

Default admin credentials can be configured via environment variables or SAML.

## Development

### Setup

```bash
git clone https://github.com/tudelft-reit/slurm-dashboard.git
cd slurm-dashboard
uv pip install -e ".[all,dev]"
./build_frontend.sh
uv run pytest
```

### Generate Test Data

Create synthetic cluster data for local development:

```bash
# Generate test data for a cluster (creates data/TestCluster/weekly-data/*.parquet)
python scripts/generate_test_cluster_data.py --cluster TestCluster

# Customize date range and job volume
python scripts/generate_test_cluster_data.py \
  --cluster MyCluster \
  --start-date 2024-01-01 \
  --end-date 2024-12-31 \
  --jobs-per-day 100
```

### Run Development Environment

Use Docker Compose for local development with hot-reload:

```bash
# Build and start containers
docker-compose build
docker-compose up -d

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend
```

Access the dashboard:
- **Frontend UI**: http://localhost:3100
- **Backend API**: http://localhost:8100
- **API Docs**: http://localhost:8100/docs

Stop containers:
```bash
docker-compose down
```

## License & Contact

GPL-3.0-or-later | [Issues](https://github.com/tudelft-reit/slurm-dashboard/issues) | s.wacker@tudelft.nl | TU Delft REIT
