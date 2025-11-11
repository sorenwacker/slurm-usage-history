# SLURM Dashboard

Web dashboard for SLURM cluster usage analytics powered by DuckDB.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

**[Documentation](https://sdrwacker.pages.ewi.tudelft.nl/slurm-usage-history)** | **[GitHub Mirror](https://github.com/tudelft-reit/slurm-dashboard)**

## Key Features

- **92% less memory** (13GB → 1.1GB) and **15x faster** queries with DuckDB
- React + FastAPI interface with interactive charts
- SAML 2.0 authentication
- Multi-cluster support
- PDF report generation

## Quick Start

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

## Development

```bash
git clone https://github.com/tudelft-reit/slurm-dashboard.git
cd slurm-dashboard
uv pip install -e ".[all,dev]"
./build_frontend.sh
uv run pytest
```

## License & Contact

GPL-3.0-or-later | [Issues](https://github.com/tudelft-reit/slurm-dashboard/issues) | s.wacker@tudelft.nl | TU Delft REIT
