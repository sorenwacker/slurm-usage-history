# SLURM Usage History Exporter - Cluster Agent

A standalone tool for extracting SLURM job data from your cluster and submitting it directly to your usage dashboard.

## Features

- **Zero Dependencies**: Standalone Python script with minimal requirements
- **Auto-Configuration**: Automatically detects cluster name from SLURM
- **Flexible Scheduling**: Run manually, via cron, or systemd timer
- **Robust**: Built-in retries, error handling, and logging
- **Secure**: API key authentication, secure configuration storage
- **Efficient**: Extracts only completed jobs, filters out noise
- **Production-Ready**: Systemd service included for automated collection

## Requirements

- Python 3.8 or higher
- SLURM client tools (`sacct` command)
- Access to SLURM accounting database (may require admin privileges)
- Network access to dashboard API
- Root access for system-wide installation (or user access for local install)

## Quick Start

### 1. Installation

On your SLURM cluster login/management node:

```bash
# Copy the cluster-agent directory to your cluster
scp -r cluster-agent/ user@cluster:/tmp/

# SSH to the cluster
ssh user@cluster

# Run installation (requires root)
cd /tmp/cluster-agent
sudo ./install.sh
```

The installation script will:
- Install Python dependencies
- Copy files to `/opt/slurm-usage-history-exporter/`
- Create configuration directory in `/etc/slurm-usage-history-exporter/`
- Set up systemd service and timer
- Create symlink in `/usr/local/bin/`

### 2. Configuration

Edit the configuration file:

```bash
sudo nano /etc/slurm-usage-history-exporter/config.json
```

Minimal configuration:

```json
{
  "api_url": "https://your-dashboard.example.com",
  "api_key": "your-secret-api-key",
  "timeout": 30
}
```

**Configuration Options:**

| Option | Required | Description |
|--------|----------|-------------|
| `api_url` | Yes | URL of your dashboard backend API |
| `api_key` | Yes | API key for authentication (must match backend config) |
| `timeout` | No | HTTP request timeout in seconds (default: 30) |
| `cluster_name` | No | Override cluster name (auto-detected if omitted) |
| `collection_window_days` | No | Number of days to collect (default: 7) |

**Getting your API key:**

The API key must match one of the keys configured in your dashboard backend. Check your backend `.env` file:

```bash
# On your dashboard server
grep API_KEYS /path/to/backend/.env
```

### 3. Test the Exporter

Dry run (extracts data but doesn't submit):

```bash
sudo slurm-usage-history-exporter --dry-run --verbose
```

This will show you:
- What cluster name was detected
- How many jobs will be submitted
- Sample job data
- Any errors in extraction or formatting

### 4. Manual Submission

Submit data to the dashboard:

```bash
sudo slurm-usage-history-exporter
```

Check logs:

```bash
sudo journalctl -u slurm-usage-history-exporter.service -f
```

### 5. Enable Automatic Collection

Enable the systemd timer to run daily:

```bash
sudo systemctl enable slurm-usage-history-exporter.timer
sudo systemctl start slurm-usage-history-exporter.timer
```

Check timer status:

```bash
sudo systemctl status slurm-usage-history-exporter.timer
sudo systemctl list-timers slurm-usage-history-exporter.timer
```

## Usage

### Command-Line Options

```bash
slurm-usage-history-exporter [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--config PATH` | Path to config file (default: `/etc/slurm-usage-history-exporter/config.json`) |
| `--start-date YYYY-MM-DD` | Start date for data collection (default: 7 days ago) |
| `--end-date YYYY-MM-DD` | End date for data collection (default: today) |
| `--cluster-name NAME` | Override auto-detected cluster name |
| `--dry-run` | Extract and format but don't submit to API |
| `--verbose` | Enable verbose debug logging |
| `--help` | Show help message |

### Examples

**Collect last 30 days:**

```bash
slurm-usage-history-exporter --start-date 2024-01-01 --end-date 2024-01-31
```

**Test with custom config:**

```bash
slurm-usage-history-exporter --config /path/to/config.json --dry-run
```

**Debug mode:**

```bash
slurm-usage-history-exporter --verbose
```

## How It Works

### Data Extraction Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. SLURM sacct Command                                      │
│    Extracts completed jobs from accounting database         │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Data Parsing & Formatting                                │
│    - Parses AllocTRES (CPU, GPU, Memory)                   │
│    - Calculates elapsed time in hours                       │
│    - Computes CPU-hours and GPU-hours                       │
│    - Counts allocated nodes                                 │
│    - Filters out RUNNING/PENDING/Unknown jobs              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. API Submission                                           │
│    POST /api/data/ingest                                    │
│    Headers: X-API-Key                                       │
│    Body: { hostname, jobs: [...] }                          │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Dashboard Backend                                         │
│    - Validates API key                                       │
│    - Processes job records                                   │
│    - Stores in parquet format                               │
│    - Auto-refreshes dashboard                               │
└─────────────────────────────────────────────────────────────┘
```

### What Data Gets Collected

For each completed SLURM job:

- **Identification**: JobID, User, Account, Partition
- **Status**: State (COMPLETED, FAILED, etc.), QOS
- **Timing**: Submit time, Start time, End time, Waiting time, Duration
- **Resources**: Allocated CPUs, GPUs, Nodes, Memory
- **Utilization**: CPU-hours, GPU-hours
- **Infrastructure**: Node list, Cluster name

### Security Considerations

1. **API Key Protection**: Config file is set to `600` permissions (owner read/write only)
2. **HTTPS**: Always use HTTPS for API URL in production
3. **Minimal Privileges**: Service runs with security hardening enabled
4. **No Sensitive Data**: Only job metadata is collected (no job content)
5. **Audit Trail**: All submissions logged via systemd journal

## Scheduling

### Systemd Timer (Recommended)

The included timer runs daily at 2:00 AM:

```bash
sudo systemctl enable slurm-usage-history-exporter.timer
sudo systemctl start slurm-usage-history-exporter.timer
```

View next scheduled run:

```bash
systemctl list-timers slurm-usage-history-exporter.timer
```

### Cron Alternative

If you prefer cron:

```bash
# Edit root's crontab
sudo crontab -e

# Add daily collection at 2:00 AM
0 2 * * * /usr/local/bin/slurm-usage-history-exporter >> /var/log/slurm-usage-history-exporter.log 2>&1
```

### Manual Runs

For testing or one-off collections:

```bash
# Collect last week
slurm-usage-history-exporter

# Collect specific date range
slurm-usage-history-exporter --start-date 2024-01-01 --end-date 2024-01-31

# Dry run to preview
slurm-usage-history-exporter --dry-run --verbose
```

## Troubleshooting

### Issue: "sacct command not found"

**Solution**: Install SLURM client tools or ensure `sacct` is in PATH:

```bash
# Check if sacct exists
which sacct

# If not found, install slurm-client package (Ubuntu/Debian)
sudo apt-get install slurm-client

# Or (RHEL/CentOS)
sudo yum install slurm-slurmd
```

### Issue: "Permission denied" when running sacct

**Solution**: The exporter needs access to SLURM accounting. Options:

1. Run as a user with accounting privileges
2. Add the user to the SLURM admin group
3. Configure SLURM to allow accounting queries

Test manually:

```bash
sacct --allusers --starttime=2024-01-01 --endtime=2024-01-31
```

### Issue: "Connection refused" or "Connection timeout"

**Solution**: Check network connectivity to dashboard:

```bash
# Test connectivity
curl -I https://your-dashboard.example.com/api/dashboard/health

# Check firewall
sudo iptables -L -n | grep OUTPUT

# Verify API URL in config
cat /etc/slurm-usage-history-exporter/config.json
```

### Issue: "Invalid API key" or 401/403 errors

**Solution**: Verify API key matches backend configuration:

1. Check backend `.env` file for `API_KEYS`
2. Ensure no extra spaces or newlines in config.json
3. Test with curl:

```bash
curl -X POST https://your-dashboard.example.com/api/data/ingest \
  -H "X-API-Key: your-key-here" \
  -H "Content-Type: application/json" \
  -d '{"hostname":"test","jobs":[]}'
```

### Issue: No data appearing in dashboard

**Solution**: Check the submission logs:

```bash
# View recent logs
sudo journalctl -u slurm-usage-history-exporter.service -n 50

# Follow logs in real-time
sudo journalctl -u slurm-usage-history-exporter.service -f

# Check for errors
sudo journalctl -u slurm-usage-history-exporter.service | grep ERROR
```

Verify data was received by backend:

```bash
# On dashboard server, check for new parquet files
ls -lth /path/to/data/your-cluster/weekly-data/
```

### Issue: "No jobs found in specified date range"

**Solution**: This means sacct returned no completed jobs. Check:

```bash
# Test sacct manually
sacct --allusers --starttime=2024-01-01 --endtime=2024-01-31 --format=JobID,State

# Check SLURM accounting is enabled
scontrol show config | grep AccountingStorage
```

### Issue: Import errors or missing dependencies

**Solution**: Reinstall Python dependencies:

```bash
sudo pip3 install -r requirements.txt --upgrade
```

## Monitoring

### Check Service Status

```bash
# Service status
sudo systemctl status slurm-usage-history-exporter.service

# Timer status
sudo systemctl status slurm-usage-history-exporter.timer

# View logs
sudo journalctl -u slurm-usage-history-exporter.service -f
```

### View Recent Submissions

```bash
# Last 50 log lines
sudo journalctl -u slurm-usage-history-exporter.service -n 50

# Today's logs
sudo journalctl -u slurm-usage-history-exporter.service --since today

# Logs with timestamps
sudo journalctl -u slurm-usage-history-exporter.service -o short-precise
```

### Metrics to Monitor

Look for these in the logs:

- Number of jobs extracted
- Number of jobs submitted
- Total CPU-hours and GPU-hours
- API response status
- Errors or warnings

Example successful output:

```
INFO - Initialized extractor for cluster: cluster01
INFO - Extracting jobs from 2024-10-24 to 2024-10-31
INFO - Extracted 1523 raw job records
INFO - Filtered to 1485 completed job records
INFO - Formatted 1485 jobs for submission
INFO - Submitting 1485 jobs to https://dashboard.example.com/api/data/ingest
INFO - Successfully submitted: Successfully ingested 1485 jobs for cluster01
```

## Local/User Installation

If you don't have root access, you can install locally:

```bash
# Create local directories
mkdir -p ~/.local/bin
mkdir -p ~/.config/slurm-usage-history-exporter

# Install dependencies to user site
pip3 install --user -r requirements.txt

# Copy script
cp slurm-usage-history-exporter.py ~/.local/bin/slurm-usage-history-exporter
chmod +x ~/.local/bin/slurm-usage-history-exporter

# Copy config
cp config.json.example ~/.config/slurm-usage-history-exporter/config.json

# Edit config
nano ~/.config/slurm-usage-history-exporter/config.json

# Run exporter
~/.local/bin/slurm-usage-history-exporter --config ~/.config/slurm-usage-history-exporter/config.json
```

For scheduled runs, use user cron:

```bash
crontab -e

# Add:
0 2 * * * ~/.local/bin/slurm-usage-history-exporter --config ~/.config/slurm-usage-history-exporter/config.json
```

## Uninstallation

To remove the exporter:

```bash
# Stop and disable timer
sudo systemctl stop slurm-usage-history-exporter.timer
sudo systemctl disable slurm-usage-history-exporter.timer

# Remove systemd files
sudo rm /etc/systemd/system/slurm-usage-history-exporter.service
sudo rm /etc/systemd/system/slurm-usage-history-exporter.timer
sudo systemctl daemon-reload

# Remove installation
sudo rm -rf /opt/slurm-usage-history-exporter
sudo rm /usr/local/bin/slurm-usage-history-exporter

# Remove configuration (WARNING: deletes API key)
sudo rm -rf /etc/slurm-usage-history-exporter

# Uninstall Python dependencies (optional)
sudo pip3 uninstall pandas requests urllib3
```

## Advanced Configuration

### Custom Date Ranges

Collect specific periods:

```bash
# Last 30 days
slurm-usage-history-exporter --start-date $(date -d '30 days ago' +%Y-%m-%d)

# Specific month
slurm-usage-history-exporter --start-date 2024-01-01 --end-date 2024-01-31

# Yesterday only
slurm-usage-history-exporter --start-date $(date -d yesterday +%Y-%m-%d) --end-date $(date +%Y-%m-%d)
```

### Multiple Clusters

If managing multiple clusters, install on each and use unique cluster names:

```json
{
  "api_url": "https://dashboard.example.com",
  "api_key": "shared-api-key",
  "cluster_name": "cluster01"
}
```

The dashboard will automatically separate data by hostname.

### Proxy Configuration

If behind a proxy, set environment variables:

```bash
export HTTP_PROXY=http://proxy.example.com:8080
export HTTPS_PROXY=http://proxy.example.com:8080
slurm-usage-history-exporter
```

Or add to systemd service:

```ini
[Service]
Environment="HTTP_PROXY=http://proxy.example.com:8080"
Environment="HTTPS_PROXY=http://proxy.example.com:8080"
```

## Support

For issues or questions:

1. Check the troubleshooting section above
2. Review logs: `journalctl -u slurm-usage-history-exporter.service`
3. Run with `--verbose --dry-run` to debug
4. Check dashboard backend logs
5. Open an issue on the project repository

## License

This tool is part of the SLURM Usage History project.
