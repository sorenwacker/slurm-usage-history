# SLURM Usage History Dashboard

Modern web dashboard for SLURM cluster usage analytics with DuckDB-powered data processing.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

## Features

- **High-performance analytics** - DuckDB engine with 92% memory reduction and 15x faster queries
- **Modern web interface** - React + FastAPI with real-time interactive charts
- **Enterprise SSO** - SAML 2.0 authentication with role-based access control
- **Flexible deployment** - API-based agent or shared filesystem
- **PDF reports** - Generate and share usage insights
- **Multi-cluster support** - Manage multiple SLURM clusters from one dashboard

## Documentation

**Full documentation:** [https://sdrwacker.pages.ewi.tudelft.nl/slurm-usage-history](https://sdrwacker.pages.ewi.tudelft.nl/slurm-usage-history)

- [Quick Start Guide](docs/getting-started/quickstart.md) - Get running in 5 minutes
- [Installation Guide](docs/getting-started/installation.md) - Production deployment
- [Cluster Setup](docs/user-guide/cluster-setup.md) - Configure SLURM data collection
- [Configuration](docs/user-guide/configuration.md) - Customize dashboard and clusters

## Quick Start

### 1. Install Package

```bash
# Full installation (dashboard + agent)
pip install slurm-dashboard[all]

# Or from GitLab for latest development version
pip install "slurm-dashboard[all] @ git+https://gitlab.ewi.tudelft.nl/sdrwacker/slurm-usage-history.git"
```

### 2. Collect Data on SLURM Cluster

```bash
# Run agent to collect usage data
slurm-dashboard-agent --output /data/slurm-usage/$(hostname)

# Or upload via API
slurm-dashboard-agent \
  --api-url https://dashboard.example.com/api \
  --api-key your-api-key \
  --output /data/slurm-usage/CLUSTERNAME
```

### 3. Start Dashboard

```bash
export DATA_PATH=/data/slurm-usage
slurm-dashboard  # Access at http://localhost:8100
```

For production deployment, see the [Installation Guide](docs/getting-started/installation.md).

## Development

```bash
# Clone repository
git clone https://gitlab.ewi.tudelft.nl/sdrwacker/slurm-usage-history.git
cd slurm-usage-history

# Install development dependencies
uv pip install -e ".[all,dev]"

# Build frontend
./build_frontend.sh

# Run tests
pytest

# Code quality
ruff format . && ruff check .
```

## Performance

| Metric | Legacy (Pandas) | Current (DuckDB) |
|--------|----------------|------------------|
| Memory | 13 GB | 1.1 GB (92% less) |
| Query Speed | 8-12s | 0.3-0.8s (15x faster) |
| Data Loading | Full RAM | On-demand (scalable to TB+) |

## License

GPL-3.0-or-later - See [LICENSE](LICENSE)

## Contact

- **Issues**: [GitLab Issues](https://gitlab.ewi.tudelft.nl/sdrwacker/slurm-usage-history/-/issues)
- **Email**: s.wacker@tudelft.nl
- **Institution**: TU Delft Research Engineering & IT Services
