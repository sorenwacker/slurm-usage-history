# Quick Start Guide

Get SLURM Dashboard up and running in 5 minutes.

## TL;DR

```bash
# Install from GitLab
pip install "slurm-dashboard[all] @ git+https://gitlab.ewi.tudelft.nl/sdrwacker/slurm-usage-history.git"

# Collect data (on cluster)
slurm-dashboard-agent --output /data/slurm-usage/$(hostname)

# Start dashboard (on server) - frontend included
export DATA_PATH=/data/slurm-usage
slurm-dashboard
```

Open browser to `http://localhost:8100`

Frontend is included with `[web]` extra - no separate build needed.

**Note:** Once published to PyPI, you can use `pip install slurm-dashboard[all]` instead.

## Step-by-Step

### 1. Install Package

Choose your installation based on needs:

**From PyPI (when published):**
```bash
# Minimum (data processing only)
pip install slurm-dashboard

# For cluster agent
pip install slurm-dashboard[agent]

# For web dashboard
pip install slurm-dashboard[web]

# Everything (recommended)
pip install slurm-dashboard[all]
```

**From GitLab (before PyPI release or for development):**
```bash
# With pip
pip install "slurm-dashboard[all] @ git+https://gitlab.ewi.tudelft.nl/sdrwacker/slurm-usage-history.git"

# With uv (faster)
uv pip install "slurm-dashboard[all] @ git+https://gitlab.ewi.tudelft.nl/sdrwacker/slurm-usage-history.git"

# For cluster agent only
pip install "slurm-dashboard[agent] @ git+https://gitlab.ewi.tudelft.nl/sdrwacker/slurm-usage-history.git"
```

### 2. Collect SLURM Data

On your SLURM cluster head node:

```bash
# Create data directory
mkdir -p /data/slurm-usage

# Run agent (collects last 7 days by default)
slurm-dashboard-agent --output /data/slurm-usage/$(hostname)

# Verify data was created
ls -lh /data/slurm-usage/$(hostname)/weekly-data/
```

**Automate with cron:**

```bash
# Edit crontab
crontab -e

# Add weekly collection (every Monday at 2 AM)
0 2 * * 1 slurm-dashboard-agent --output /data/slurm-usage/$(hostname) 2>&1 | logger -t slurm-dashboard-agent
```

### 3. Configure Environment

Create a `.env` file with your configuration:

```bash
# Create .env file
cat > .env << 'EOF'
# Required: Path to SLURM data
DATA_PATH=/data/slurm-usage

# Optional: API configuration
API_PREFIX=/api
AUTO_REFRESH_INTERVAL=600

# Optional: CORS origins (comma-separated)
CORS_ORIGINS=http://localhost:5173,http://localhost:8100

# Optional: SAML authentication
ENABLE_SAML=false

# Optional: Logging
LOG_LEVEL=INFO
EOF
```

Or copy from example:
```bash
cp .env.example .env
# Edit with your values
nano .env
```

### 4. Start Backend

```bash
# Start backend with integrated frontend
slurm-dashboard

# Or with auto-reload for development
slurm-dashboard --reload
```

Backend is now running at `http://localhost:8100`

Test API: `curl http://localhost:8100/api/dashboard/health`

### 5. Access Dashboard

Open browser to:
- Dashboard: `http://localhost:8100`
- Backend API docs: `http://localhost:8100/docs`

The frontend is pre-built and served directly by FastAPI.

### 6. Frontend Development (Optional)

Only needed if you want to modify the frontend:

```bash
cd frontend

# Install dependencies
npm install

# Start development server with hot reload
npm run dev
```

Development server runs at `http://localhost:5173` with hot module replacement.

## Production Deployment

### Option 1: Automated (Ansible)

```bash
cd ansible
ansible-playbook -i inventory.yml playbook.yml
```

### Option 2: Manual

See [INSTALL.md](INSTALL.md) for detailed production setup.

## Common Commands

### Data Collection

```bash
# Collect last 7 days
slurm-dashboard-agent --output /data/slurm-usage/CLUSTER

# Collect specific date range
slurm-dashboard-agent --start 2024-01-01 --end 2024-12-31 --output /data/slurm-usage/CLUSTER

# Analyze waiting times
slurm-dashboard-wait-times --input /data/slurm-usage/CLUSTER
```

### Backend Management

```bash
# Development
slurm-dashboard --reload

# Production (with Gunicorn)
gunicorn backend.app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8100

# Check logs
tail -f /var/log/slurm-dashboard-backend.log
```

### Frontend Management

```bash
# Development
npm run dev

# Build for production
VITE_API_URL=https://dashboard.example.com npm run build

# Preview production build
npm run preview
```

## Environment Variables

Create `.env` file in project root:

```bash
# Required
DATA_PATH=/data/slurm-usage

# Optional
API_PREFIX=/api
AUTO_REFRESH_INTERVAL=600
CORS_ORIGINS=http://localhost:5173,https://dashboard.example.com

# SAML (optional)
ENABLE_SAML=false
SAML_SETTINGS_PATH=/etc/slurm-dashboard/saml.json
```

## Troubleshooting

### No data showing in dashboard

1. Check data path:
   ```bash
   ls -la $DATA_PATH
   ```

2. Verify parquet files exist:
   ```bash
   find $DATA_PATH -name "*.parquet"
   ```

3. Check backend logs:
   ```bash
   # Development
   Check terminal output

   # Production
   journalctl -u slurm-dashboard-backend -n 50
   ```

### Backend won't start

1. Check DuckDB installation:
   ```bash
   python -c "import duckdb; print('OK')"
   ```

2. Verify data path is accessible:
   ```bash
   python -c "from pathlib import Path; print(Path('$DATA_PATH').exists())"
   ```

3. Check port availability:
   ```bash
   lsof -i :8100
   ```

### Frontend build fails

1. Check Node.js version:
   ```bash
   node --version  # Should be 20+
   ```

2. Clear cache:
   ```bash
   rm -rf node_modules dist
   npm install
   ```

### Charts show empty data

1. Check date range matches available data:
   ```bash
   # List available date ranges
   find $DATA_PATH -name "*.parquet" | head
   ```

2. Clear browser cache and hard refresh (Ctrl+Shift+R)

3. Check browser console for errors (F12)

## Next Steps

- Read [INSTALL.md](INSTALL.md) for production deployment
- Configure [SAML authentication](INSTALL.md#saml-authentication-optional)
- Set up [automated backups](INSTALL.md#data-backup)
- Explore [API documentation](http://localhost:8100/docs)

## Getting Help

- Check [FAQ](docs/FAQ.md)
- Open an [issue](https://gitlab.ewi.tudelft.nl/sdrwacker/slurm-usage-history/-/issues)
- Contact: s.wacker@tudelft.nl
