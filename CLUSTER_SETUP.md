# Cluster Setup Guide

Quick guide for installing and configuring the SLURM data collection agent on your cluster.

## Prerequisites

- SLURM cluster with `sacct` access
- Python 3.10+
- Git (for GitLab installation)
- Network access to GitLab (or use PyPI when published)

## Installation on Cluster

### Option 1: From GitLab (Current)

Install directly from the repository:

**With Python venv (recommended for cluster systems):**
```bash
# Create virtual environment
python3 -m venv ~/slurm-dashboard-env

# Activate it
source ~/slurm-dashboard-env/bin/activate

# Install agent
pip install "slurm-dashboard[agent] @ git+https://gitlab.ewi.tudelft.nl/sdrwacker/slurm-usage-history.git"

# Verify installation
slurm-dashboard-agent --help
```

**With uv (faster, creates venv automatically):**
```bash
# Create and install in one step
uv venv ~/slurm-dashboard-env
source ~/slurm-dashboard-env/bin/activate
uv pip install "slurm-dashboard[agent] @ git+https://gitlab.ewi.tudelft.nl/sdrwacker/slurm-usage-history.git"

# Verify installation
slurm-dashboard-agent --help
```

**Note:** Remember to activate the virtual environment before running the agent.

### Option 2: From PyPI (When Published)

```bash
# With pip
pip install slurm-dashboard[agent]

# With uv
uv pip install slurm-dashboard[agent]

# Verify
slurm-dashboard-agent --help
```

## Setup Data Collection

### 1. Create Data Directory

```bash
# Choose a location accessible to the dashboard server (e.g., NFS mount)
mkdir -p /data/slurm-usage
```

### 2. Test Manual Collection

```bash
# Collect last 7 days of data
slurm-dashboard-agent --output /data/slurm-usage/$(hostname)

# Verify data was created
ls -lh /data/slurm-usage/$(hostname)/weekly-data/
```

You should see parquet files like `2024-W45.parquet`.

### 3. Automated Collection with Cron

```bash
# Edit crontab
crontab -e

# Add weekly collection (every Monday at 2 AM)
# Note: Use full path to venv python
0 2 * * 1 /home/yourusername/slurm-dashboard-env/bin/slurm-dashboard-agent --output /data/slurm-usage/$(hostname) 2>&1 | logger -t slurm-dashboard-agent
```

**Alternative: Daily collection (more granular)**
```bash
# Collect daily at 2 AM
0 2 * * * /home/yourusername/slurm-dashboard-env/bin/slurm-dashboard-agent --output /data/slurm-usage/$(hostname) 2>&1 | logger -t slurm-dashboard-agent
```

**Tip:** Find the full path with `which slurm-dashboard-agent` while your venv is activated.

### 4. Verify Cron Job

```bash
# Check crontab
crontab -l

# Check system logs for agent output
grep slurm-dashboard-agent /var/log/syslog
# or on systemd systems:
journalctl -t slurm-dashboard-agent
```

## Advanced Configuration

### Collect Specific Date Range

```bash
# Collect specific period
slurm-dashboard-agent \
  --start 2024-01-01 \
  --end 2024-12-31 \
  --output /data/slurm-usage/$(hostname)
```

### Multiple Clusters

If you manage multiple clusters, use distinct output directories:

```bash
# On cluster1
slurm-dashboard-agent --output /data/slurm-usage/cluster1

# On cluster2
slurm-dashboard-agent --output /data/slurm-usage/cluster2
```

The dashboard will automatically detect and show all clusters.

### Custom SLURM Partition

If your SLURM installation is non-standard:

```bash
# Ensure sacct is in PATH
export PATH=/usr/local/slurm/bin:$PATH

# Run agent
slurm-dashboard-agent --output /data/slurm-usage/$(hostname)
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

### uv Installation Issues

If `uv pip install` fails with environment errors:

```bash
# Error: Failed to inspect Python interpreter from conda prefix
# Solution: Use regular pip instead
pip install "slurm-dashboard[agent] @ git+https://gitlab.ewi.tudelft.nl/sdrwacker/slurm-usage-history.git"

# Or specify Python explicitly with uv
uv pip install --python $(which python3) "slurm-dashboard[agent] @ git+https://gitlab.ewi.tudelft.nl/sdrwacker/slurm-usage-history.git"
```

### GitLab Access Issues

If you can't access GitLab from the cluster:

1. **Use PyPI** (when published): `pip install slurm-dashboard[agent]`
2. **Download and install manually**:
   ```bash
   # On machine with GitLab access:
   git clone https://gitlab.ewi.tudelft.nl/sdrwacker/slurm-usage-history.git
   cd slurm-usage-history
   python -m build  # or: uv build

   # Copy dist/*.whl to cluster
   scp dist/slurm_dashboard-*.whl cluster:/tmp/

   # On cluster:
   pip install /tmp/slurm_dashboard-*.whl[agent]
   ```

## Data Storage Recommendations

### Storage Size

- **Per job record**: ~500 bytes compressed
- **1 million jobs/week**: ~500 MB
- **1 year of data**: ~25 GB

Plan accordingly based on your cluster size.

### NFS Mount

If using NFS for shared storage:

```bash
# Example /etc/fstab entry
server:/data/slurm-usage  /data/slurm-usage  nfs  defaults,rw  0  0
```

### Retention Policy

Keep at least 1-2 years of data for trend analysis:

```bash
# Clean up data older than 2 years (optional)
find /data/slurm-usage/$(hostname)/weekly-data -name "*.parquet" -mtime +730 -delete
```

## Security Considerations

1. **Read-only access**: The agent only reads from SLURM accounting database
2. **File permissions**: Ensure data directory is only writable by authorized users
3. **Network**: Agent doesn't require network access (only local SLURM access)

## Next Steps

After setting up data collection:

1. Set up the dashboard server - see [INSTALL.md](INSTALL.md)
2. Configure automated reports - see documentation
3. Set up SAML authentication (optional) - see [INSTALL.md](INSTALL.md#saml-authentication-optional)

## Support

- Issues: https://gitlab.ewi.tudelft.nl/sdrwacker/slurm-usage-history/-/issues
- Documentation: See README.md and QUICKSTART.md
