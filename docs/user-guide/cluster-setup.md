# Cluster Setup Guide

Quick guide for installing and configuring the SLURM data collection agent on your cluster.

## Prerequisites

- SLURM cluster with `sacct` access
- Python 3.10-3.12 (3.14+ not yet supported by pandas)
- Conda or venv for isolated environments
- Git (for GitLab installation)
- Network access to dashboard API

## Installation on Cluster

### Recommended: Using Conda

Conda provides the most reliable installation on older cluster systems (e.g., with GCC 4.8).

```bash
# Create conda environment with Python 3.11
conda create -n slurm-dash python=3.11 -y
conda activate slurm-dash

# On older systems (GCC < 8.4), install modern compilers first
conda install -y gcc_linux-64 gxx_linux-64

# Install the agent
pip install "git+https://gitlab.ewi.tudelft.nl/reit/slurm-usage-history.git#egg=slurm-dashboard[agent]"

# Add to PATH if needed
export PATH="$HOME/.local/bin:$PATH"

# Verify installation
slurm-dashboard --help
```

### Alternative: Using venv

If conda is not available:

```bash
# Create virtual environment with Python 3.10-3.12
python3.11 -m venv ~/slurm-dash-venv
source ~/slurm-dash-venv/bin/activate

# Install the agent
pip install "git+https://gitlab.ewi.tudelft.nl/reit/slurm-usage-history.git#egg=slurm-dashboard[agent]"

# Verify installation
slurm-dashboard --help
```

### From PyPI (When Published)

```bash
pip install slurm-dashboard[agent]
slurm-dashboard --help
```

### Important Notes

- **Python version**: Use Python 3.10-3.12 (not 3.14+, pandas doesn't support it yet)
- **PATH setup**: If `slurm-dashboard` command is not found, add `~/.local/bin` to PATH:
  ```bash
  export PATH="$HOME/.local/bin:$PATH"
  echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
  ```
- **Old systems**: On clusters with GCC < 8.4, install compilers via conda first

## Setup Data Collection

The new agent uses API-based submission - no shared filesystem required.

### 1. Get API Credentials

Contact your dashboard administrator for:
- Dashboard API URL (e.g., `https://dashboard.daic.tudelft.nl`)
- API key for authentication

The administrator creates a cluster entry via the admin panel and provides the API key.

### 2. Create Configuration File

```bash
# Activate your conda environment
conda activate slurm-dash

# Create config with your credentials
slurm-dashboard create-config \
  --api-url https://dashboard.daic.tudelft.nl \
  --api-key YOUR_API_KEY_HERE \
  --cluster-name DAIC \
  --local-data-path /data/slurm-usage/DAIC \
  -o config.json
```

This creates a `config.json` file with mode `0600` (readable only by you) containing:
```json
{
  "api_url": "https://dashboard.daic.tudelft.nl",
  "api_key": "YOUR_API_KEY_HERE",
  "cluster_name": "DAIC",
  "local_data_path": "/data/slurm-usage/DAIC",
  "timeout": 30,
  "collection_window_days": 7
}
```

### 3. Test with Dry Run

```bash
# Test data extraction without submitting
slurm-dashboard run --config config.json --dry-run --verbose
```

You should see:
- Number of jobs extracted
- Total CPU-hours and GPU-hours
- Sample job record

### 4. Run for Real

```bash
# Submit data to dashboard
slurm-dashboard run --config config.json
```

Check the dashboard to verify data appears.

### 5. Automated Collection with Cron

```bash
# Edit crontab
crontab -e

# Add daily collection at 2 AM
# Adjust paths based on your conda installation
0 2 * * * source ~/miniforge3/etc/profile.d/conda.sh && conda activate slurm-dash && slurm-dashboard run --config ~/config.json >> ~/agent.log 2>&1
```

**For venv instead of conda:**
```bash
0 2 * * * source ~/slurm-dash-venv/bin/activate && slurm-dashboard run --config ~/config.json >> ~/agent.log 2>&1
```

### 6. Verify Cron Job

```bash
# Check crontab
crontab -l

# Watch the log file
tail -f ~/agent.log
```

**Advantages of this approach:**
- No NFS required
- HTTPS encryption
- API key authentication
- Works across networks/firewalls
- Simple configuration file
- Optional local data backup

### Error Handling and Recovery

**If API submission fails:**

The agent extracts data from SLURM's accounting database (sacct), which retains historical data. If submission fails:

1. Error is logged to `~/agent.log` (or wherever your cron logs)
2. Next cron run will retry the same period (default: last 7 days)
3. No data is lost - SLURM keeps accounting data persistently
4. Overlapping submissions are handled - dashboard deduplicates jobs by JobID

**Checking for failures:**

```bash
# Check recent log entries
tail -20 ~/agent.log

# Look for errors
grep -i error ~/agent.log

# Check if agent is running
ps aux | grep slurm-dashboard
```

**Manual recovery after outage:**

If the dashboard was down for an extended period, you can backfill data:

```bash
# Collect specific date range
slurm-dashboard run \
  --config config.json \
  --start-date 2025-01-01 \
  --end-date 2025-01-31
```

**Future enhancement:**

Local data backup (via `local_data_path` config option) will save extracted data locally before submission, providing an additional safety layer. This feature is planned for a future release.

---

## Advanced Configuration

### Collect Specific Date Range

```bash
# Collect specific period
slurm-dashboard run \
  --config config.json \
  --start-date 2024-01-01 \
  --end-date 2024-12-31
```

### Override Cluster Name

```bash
# Override cluster name from config
slurm-dashboard run \
  --config config.json \
  --cluster-name MyCluster
```

### Custom SLURM Path

If SLURM commands are not in your PATH:

```bash
# Add SLURM to PATH before running
export PATH=/usr/local/slurm/bin:$PATH
slurm-dashboard run --config config.json
```

## Troubleshooting

### "sacct: command not found"

Ensure SLURM client tools are installed and in PATH:

```bash
# Find sacct
which sacct

# If not in PATH, add it
export PATH=/path/to/slurm/bin:$PATH
```

### Permission Denied on Output Directory

```bash
# Check permissions
ls -ld /data/slurm-usage

# Fix permissions (adjust as needed)
chmod 755 /data/slurm-usage
```

### No Data in Parquet Files

```bash
# Check if sacct returns data
sacct --starttime $(date -d '7 days ago' +%Y-%m-%d) --format=JobID,Start,End,State

# If no output, check SLURM accounting configuration
sacctmgr show configuration
```

### Python 3.14 Installation Fails

pandas doesn't yet support Python 3.14. Use Python 3.10-3.12:

```bash
# Recreate conda environment with correct Python version
conda create -n slurm-dash python=3.11 -y
conda activate slurm-dash
pip install "git+https://gitlab.ewi.tudelft.nl/reit/slurm-usage-history.git#egg=slurm-dashboard[agent]"
```

### GCC Too Old (GCC < 8.4)

On older systems, pandas compilation fails. Install modern compilers via conda:

```bash
conda activate slurm-dash
conda install -y gcc_linux-64 gxx_linux-64
pip install "git+https://gitlab.ewi.tudelft.nl/reit/slurm-usage-history.git#egg=slurm-dashboard[agent]"
```

### Command Not Found

If `slurm-dashboard` is not found after installation:

```bash
# Add ~/.local/bin to PATH
export PATH="$HOME/.local/bin:$PATH"

# Make permanent
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc

# Or use full path
~/.local/bin/slurm-dashboard --help
```

### GitLab Access Issues

If you can't access GitLab from the cluster, ask your administrator to:

1. Build the wheel file on a machine with GitLab access
2. Copy it to the cluster
3. Install with: `pip install slurm_dashboard-*.whl[agent]`

## Security Considerations

1. **Read-only SLURM access**: Agent only reads from SLURM accounting database
2. **Config file permissions**: config.json is created with mode 0600 (user-readable only)
3. **API authentication**: All uploads use HTTPS with API key authentication
4. **No data leakage**: Agent only uploads job metadata (no job outputs or user data)

## Next Steps

After setting up data collection:

1. Set up the dashboard server - see [INSTALL.md](../getting-started/installation.md)
2. Configure automated reports - see documentation
3. Set up SAML authentication (optional) - see [INSTALL.md](../getting-started/installation.md#saml-authentication-optional)

## Support

- Issues: https://gitlab.ewi.tudelft.nl/sdrwacker/slurm-usage-history/-/issues
- Documentation: See README.md and QUICKSTART.md
