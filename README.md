# SLURM Dashboard

Web dashboard for SLURM cluster usage analytics powered by DuckDB.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

**[Documentation](https://sdrwacker.pages.ewi.tudelft.nl/slurm-usage-history)** | **[GitHub Mirror](https://github.com/sorenwacker/slurm-dashboard)**

## Key Features

- **92% less memory** (13GB → 1.1GB) and **15x faster** queries with DuckDB
- React + FastAPI interface with interactive charts
- SAML 2.0 authentication
- Multi-cluster support
- PDF report generation

## Quick Start

```bash
# Install
pip install slurm-dashboard[all]

# Collect data on SLURM cluster
slurm-dashboard-agent --output /data/slurm-usage/$(hostname)

# Start dashboard
export DATA_PATH=/data/slurm-usage
slurm-dashboard
# → http://localhost:8100
```

See [documentation](https://sdrwacker.pages.ewi.tudelft.nl/slurm-usage-history) for production deployment and configuration.

## Development

```bash
git clone https://gitlab.ewi.tudelft.nl/sdrwacker/slurm-usage-history.git
cd slurm-usage-history
uv pip install -e ".[all,dev]"
./build_frontend.sh
uv run pytest
```

## License & Contact

GPL-3.0-or-later | [Issues](https://gitlab.ewi.tudelft.nl/sdrwacker/slurm-usage-history/-/issues) | s.wacker@tudelft.nl | TU Delft REIT
