# SLURM Dashboard

Modern web dashboard for SLURM cluster usage analytics with DuckDB-powered data processing.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

## Features

### Data Collection & Processing
- **Efficient data collection** from SLURM via `sacct`
- **DuckDB-powered analytics** for low-memory, high-performance queries
- **Automatic data refresh** with configurable intervals
- **Parquet-based storage** for optimal compression and query speed

### Modern Web Dashboard
- **React frontend** with responsive design
- **FastAPI backend** with async support
- **Real-time interactive charts** (Plotly.js)
- **Advanced filtering** by account, partition, user, QoS, state
- **Dynamic date ranges** (day, week, month, year)
- **PDF report generation** for sharing insights

### Security & Authentication
- **SAML 2.0 integration** for SSO
- **Role-based access** (coming soon)
- **HTTPS/TLS support**

### Performance
- **95% memory reduction** vs legacy pandas implementation (13GB → 1.1GB)
- **Query caching** for faster repeated requests
- **Lazy loading** - only load data when needed
- **Multi-threaded** backend with Gunicorn + Uvicorn workers

## Quick Start

### Installation

```bash
# Core package
pip install slurm-dashboard

# With data collection agent
pip install slurm-dashboard[agent]

# With web dashboard (includes frontend)
pip install slurm-dashboard[web]

# Everything (recommended)
pip install slurm-dashboard[all]
```

### Collect Data (on SLURM cluster)

```bash
# Run agent to collect usage data
slurm-agent --output /data/slurm-usage/$(hostname)
```

### Start Dashboard (on dashboard server)

```bash
# Set data path
export DATA_PATH=/data/slurm-usage

# Start backend with integrated frontend
uvicorn backend.app.main:app --host 0.0.0.0 --port 8100

# Or use Gunicorn for production
gunicorn backend.app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8100
```

Access dashboard at `http://localhost:8100`

The web installation includes the pre-built React frontend, served directly by FastAPI.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    SLURM Cluster                            │
│  ┌──────────────┐                                           │
│  │ slurm-agent  │ → Parquet files → NFS/shared storage     │
│  └──────────────┘                                           │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                  Dashboard Server                           │
│  ┌──────────────┐    ┌────────────────┐                    │
│  │   DuckDB     │ ←→ │ FastAPI Backend│ ←→ React Frontend │
│  │  Datastore   │    │  (Gunicorn)    │     (Nginx)       │
│  └──────────────┘    └────────────────┘                    │
└─────────────────────────────────────────────────────────────┘
```

## Documentation

- **[Installation Guide](INSTALL.md)** - Detailed setup instructions
- **[Deployment with Ansible](ansible/README.md)** - Automated deployment
- **[API Documentation](http://localhost:8100/docs)** - Interactive API docs (when running)

## Usage Examples

### Agent: Automated Data Collection

```bash
# Add to crontab for weekly collection
0 2 * * 1 slurm-agent --output /data/slurm-usage/$(hostname) 2>&1 | logger -t slurm-agent
```

### Backend: Custom Configuration

```bash
# .env file
DATA_PATH=/data/slurm-usage
AUTO_REFRESH_INTERVAL=600
ENABLE_SAML=true
SAML_SETTINGS_PATH=/etc/slurm-dashboard/saml.json
```

### Frontend: Custom Build

```bash
# Set API endpoint
VITE_API_URL=https://dashboard.example.com npm run build
```

## Development

### Setup

```bash
git clone https://gitlab.ewi.tudelft.nl/sdrwacker/slurm-usage-history.git
cd slurm-usage-history

# Install with development dependencies
uv pip install -e ".[all,dev]"

# Or with pip
pip install -e ".[all,dev]"

# Build frontend for development
./build_frontend.sh

# Install pre-commit hooks
pre-commit install
```

### Run Tests

```bash
pytest
pytest --cov=slurm_usage_history
```

### Code Quality

```bash
# Format code
ruff format .

# Lint code
ruff check .

# Type checking
mypy src/
```

## Deployment

### Quick Deploy with Ansible

```bash
cd ansible
ansible-playbook -i inventory.yml playbook.yml
```

See [ansible/README.md](ansible/README.md) for configuration options.

### Manual Production Setup

See [INSTALL.md](INSTALL.md) for detailed manual deployment instructions including:
- Systemd service configuration
- Nginx setup
- SAML authentication
- Performance tuning

## Performance Benchmarks

| Metric | Pandas (Legacy) | DuckDB (New) | Improvement |
|--------|----------------|--------------|-------------|
| Memory Usage | 13 GB | 1.1 GB | **92% reduction** |
| Query Time (year) | 8-12s | 0.3-0.8s | **~15x faster** |
| Startup Time | 45s | 30s | **33% faster** |
| Data Loading | Full dataset in RAM | On-demand from disk | **Scalable to TB+** |

## Screenshots

### Dashboard Overview
![Dashboard](docs/screenshots/dashboard.png)

### Advanced Filtering
![Filtering](docs/screenshots/filters.png)

### Report Generation
![Reports](docs/screenshots/reports.png)

## Roadmap

- [ ] Multi-cluster support in single dashboard
- [ ] User quotas and allocation tracking
- [ ] Email alerts for quota limits
- [ ] Historical trend analysis with forecasting
- [ ] Cost tracking and chargeback reports
- [ ] GPU usage detailed analytics
- [ ] Node efficiency metrics

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Merge Request

## License

GNU General Public License v3.0 or later (GPL-3.0-or-later)

See [LICENSE](LICENSE) for full text.

## Authors

- **Sören Wacker** - *Initial work* - [sdrwacker](https://gitlab.ewi.tudelft.nl/sdrwacker)

## Acknowledgments

- TU Delft Research Engineering & IT Services (REIT)
- DAIC cluster team
- All contributors and users

## Support

- **Issues**: [GitLab Issues](https://gitlab.ewi.tudelft.nl/sdrwacker/slurm-usage-history/-/issues)
- **Documentation**: [Wiki](https://gitlab.ewi.tudelft.nl/sdrwacker/slurm-usage-history/-/wikis/home)
- **Contact**: s.wacker@tudelft.nl

## Citation

If you use this software in your research, please cite:

```bibtex
@software{slurm_dashboard,
  author = {Wacker, Sören},
  title = {SLURM Dashboard: Modern Web Analytics for HPC Clusters},
  year = {2024},
  url = {https://gitlab.ewi.tudelft.nl/sdrwacker/slurm-usage-history}
}
```
