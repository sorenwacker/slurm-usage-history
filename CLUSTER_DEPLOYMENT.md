# Cluster Deployment Guide

This guide explains how to deploy the SLURM data collection agent on your cluster to automatically feed data to your dashboard.

## Overview

The cluster agent is a lightweight, standalone tool that:
- Runs directly on your SLURM cluster
- Extracts job data using the `sacct` command
- Submits data to your dashboard API via HTTPS
- Can run manually, on a schedule, or via systemd timer

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ SLURM Cluster                                                │
│                                                              │
│  ┌──────────────────┐         ┌──────────────────┐         │
│  │  Compute Nodes   │────────▶│  SLURM Control   │         │
│  │  (Running Jobs)  │         │  (sacct data)    │         │
│  └──────────────────┘         └─────────┬────────┘         │
│                                          │                   │
│                                          ▼                   │
│                              ┌────────────────────┐         │
│                              │ Cluster Agent      │         │
│                              │ slurm-usage-history-exporter.py  │         │
│                              │                    │         │
│                              │ - Extracts via     │         │
│                              │   sacct            │         │
│                              │ - Formats data     │         │
│                              │ - Submits to API   │         │
│                              └─────────┬──────────┘         │
└────────────────────────────────────────┼──────────────────┘
                                         │
                                         │ HTTPS
                                         │ (API Key Auth)
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────┐
│ Dashboard Server                                             │
│                                                              │
│  ┌──────────────────┐         ┌──────────────────┐         │
│  │  Backend API     │────────▶│  Data Storage    │         │
│  │  (FastAPI)       │         │  (Parquet files) │         │
│  │                  │         │                  │         │
│  │ /api/data/ingest │         │ auto-refresh     │         │
│  └──────────────────┘         └─────────┬────────┘         │
│                                          │                   │
│                                          ▼                   │
│                              ┌────────────────────┐         │
│                              │  Frontend          │         │
│                              │  (React Dashboard) │         │
│                              └────────────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

## What's Included

The `cluster-agent/` directory contains everything needed for deployment:

```
cluster-agent/
├── slurm-usage-history-exporter.py          # Main extraction & submission script
├── config.json.example         # Configuration template
├── requirements.txt            # Python dependencies
├── install.sh                  # Automated installation script
├── slurm-usage-history-exporter.service     # Systemd service definition
├── slurm-usage-history-exporter.timer       # Systemd timer for scheduling
├── README.md                   # Complete documentation
└── QUICKSTART.md              # 5-minute setup guide
```

## Deployment Options

### Option 1: Systemd Timer (Recommended)

Best for: Production clusters with systemd

**Features:**
- Automatic daily collection
- Runs at 2:00 AM daily
- Persistent (runs after reboot if missed)
- Integrated logging via journald
- Easy monitoring and management

**Setup:**
```bash
cd cluster-agent
sudo ./install.sh
sudo nano /etc/slurm-usage-history-exporter/config.json  # Configure
sudo systemctl enable slurm-usage-history-exporter.timer
sudo systemctl start slurm-usage-history-exporter.timer
```

### Option 2: Cron Job

Best for: Systems without systemd, user-level installs

**Features:**
- Simple and universal
- Runs on any system with cron
- Can run as regular user

**Setup:**
```bash
# Install locally
pip3 install --user -r requirements.txt
cp slurm-usage-history-exporter.py ~/.local/bin/
cp config.json.example ~/.config/slurm-usage-history-exporter.json
# Edit config, then add to crontab:
crontab -e
# Add: 0 2 * * * ~/.local/bin/slurm-usage-history-exporter.py --config ~/.config/slurm-usage-history-exporter.json
```

### Option 3: Manual Execution

Best for: Testing, one-off data collection, custom scheduling

**Features:**
- Full control over when to run
- Good for debugging
- Can collect historical data

**Setup:**
```bash
cd cluster-agent
pip3 install -r requirements.txt
./slurm-usage-history-exporter.py --config config.json --start-date 2024-01-01 --end-date 2024-12-31
```

## Prerequisites

### On the Cluster

- Python 3.8 or higher
- SLURM client tools (`sacct` command)
- Access to SLURM accounting database
- Network access to dashboard server
- (Optional) Root access for system-wide installation

### On the Dashboard Server

1. **Backend must be running** with API accessible
2. **API key configured** in backend `.env`:
   ```bash
   API_KEYS=your-secret-key-1,your-secret-key-2
   ```
3. **Firewall rules** allow incoming HTTPS from cluster
4. **Data directory** has write permissions

## Step-by-Step Deployment

### 1. Prepare the Dashboard Server

Ensure your backend is configured to accept data:

```bash
# On dashboard server
cd /path/to/slurm-usage-history/backend

# Check .env file has API keys
cat .env | grep API_KEYS

# If not set, add:
echo "API_KEYS=your-secret-key-here" >> .env

# Restart backend
docker-compose restart backend
# Or if running manually:
# pkill -f uvicorn && uvicorn app.main:app --reload
```

Test the API is accessible:

```bash
curl https://your-dashboard.example.com/api/dashboard/health
```

### 2. Copy Agent to Cluster

From your local machine:

```bash
cd /path/to/slurm-usage-history
scp -r cluster-agent/ user@cluster-login-node:/tmp/
```

### 3. Install on Cluster

SSH to cluster and run installation:

```bash
ssh user@cluster-login-node
cd /tmp/cluster-agent
sudo ./install.sh
```

The script will:
- Check for Python 3 and SLURM tools
- Install Python dependencies
- Copy files to `/opt/slurm-usage-history-exporter/`
- Create config in `/etc/slurm-usage-history-exporter/`
- Set up systemd service and timer
- Set secure permissions

### 4. Configure the Agent

Edit the configuration file:

```bash
sudo nano /etc/slurm-usage-history-exporter/config.json
```

Required settings:

```json
{
  "api_url": "https://your-dashboard.example.com",
  "api_key": "your-secret-key-here",
  "timeout": 30
}
```

Optional settings:

```json
{
  "api_url": "https://your-dashboard.example.com",
  "api_key": "your-secret-key-here",
  "timeout": 30,
  "cluster_name": "cluster01",
  "collection_window_days": 7
}
```

### 5. Test the Agent

Dry run to verify everything works:

```bash
sudo slurm-usage-history-exporter --dry-run --verbose
```

Expected output:
```
INFO - Initialized extractor for cluster: cluster01
INFO - Extracting jobs from 2024-10-24 to 2024-10-31
INFO - Extracted 1523 raw job records
INFO - Filtered to 1485 completed job records
INFO - Formatted 1485 jobs for submission
INFO - DRY RUN: Would submit the following:
INFO -   Cluster: cluster01
INFO -   Jobs: 1485
INFO -   Total CPU-hours: 45678.50
INFO -   Total GPU-hours: 1234.50
```

### 6. Submit Test Data

Actual submission:

```bash
sudo slurm-usage-history-exporter
```

Expected output:
```
INFO - Initialized extractor for cluster: cluster01
INFO - Extracting jobs from 2024-10-24 to 2024-10-31
INFO - Extracted 1523 raw job records
INFO - Filtered to 1485 completed job records
INFO - Formatted 1485 jobs for submission
INFO - Submitting 1485 jobs to https://your-dashboard.example.com/api/data/ingest
INFO - Dashboard health: {'status': 'healthy'}
INFO - Successfully submitted: Successfully ingested 1485 jobs for cluster01
INFO - Submission complete: {...}
```

### 7. Verify Data in Dashboard

Check the backend received the data:

```bash
# On dashboard server
ls -lth /path/to/data/cluster01/weekly-data/
```

You should see a new parquet file with today's timestamp.

Open your dashboard in a browser and select your cluster - you should see the data!

### 8. Enable Automatic Collection

Enable the systemd timer:

```bash
sudo systemctl enable slurm-usage-history-exporter.timer
sudo systemctl start slurm-usage-history-exporter.timer
```

Verify it's scheduled:

```bash
systemctl status slurm-usage-history-exporter.timer
systemctl list-timers slurm-usage-history-exporter.timer
```

## Monitoring

### Check Service Status

```bash
# Is the timer active?
systemctl status slurm-usage-history-exporter.timer

# When will it run next?
systemctl list-timers slurm-usage-history-exporter.timer

# View recent runs
journalctl -u slurm-usage-history-exporter.service -n 50

# Follow logs in real-time
journalctl -u slurm-usage-history-exporter.service -f
```

### Key Metrics to Monitor

From the logs, monitor:

1. **Extraction success**: Number of jobs extracted
2. **Submission success**: HTTP 200 responses
3. **Data volume**: CPU-hours and GPU-hours submitted
4. **Errors**: Any ERROR or WARNING messages

### Alerting (Optional)

Set up systemd email notifications on failure:

```bash
# Install postfix or similar for mail
sudo apt-get install mailutils

# Edit service to send mail on failure
sudo systemctl edit slurm-usage-history-exporter.service
```

Add:
```ini
[Unit]
OnFailure=status-email-user@%n.service
```

## Troubleshooting

### No Data Appearing in Dashboard

1. **Check agent logs:**
   ```bash
   journalctl -u slurm-usage-history-exporter.service -n 100
   ```

2. **Check backend logs:**
   ```bash
   docker-compose logs backend
   ```

3. **Verify API connectivity:**
   ```bash
   curl -I https://your-dashboard.example.com/api/dashboard/health
   ```

4. **Check data files:**
   ```bash
   ls -lth /path/to/data/your-cluster/weekly-data/
   ```

### Permission Errors

If you see "Permission denied" when running `sacct`:

```bash
# Test sacct manually
sacct --allusers --starttime=2024-01-01 --endtime=2024-01-31

# If it works, the service user needs the same permissions
# Add the service user to the slurm group:
sudo usermod -aG slurm slurm-usage-history-exporter-user
```

### API Authentication Errors

If you see 401 or 403 errors:

1. Verify API key matches backend:
   ```bash
   # On dashboard server
   grep API_KEYS /path/to/backend/.env

   # On cluster
   sudo cat /etc/slurm-usage-history-exporter/config.json | grep api_key
   ```

2. Test with curl:
   ```bash
   curl -X POST https://your-dashboard.example.com/api/data/ingest \
     -H "X-API-Key: your-key" \
     -H "Content-Type: application/json" \
     -d '{"hostname":"test","jobs":[]}'
   ```

## Multiple Clusters

To deploy on multiple clusters:

1. Install the agent on each cluster
2. Use a unique `cluster_name` in each config
3. Use the same `api_key` for all clusters
4. The dashboard will automatically separate data by hostname

Example configs:

**Cluster 1:**
```json
{
  "api_url": "https://dashboard.example.com",
  "api_key": "shared-key",
  "cluster_name": "hpc-cluster-01"
}
```

**Cluster 2:**
```json
{
  "api_url": "https://dashboard.example.com",
  "api_key": "shared-key",
  "cluster_name": "gpu-cluster-02"
}
```

## Security Best Practices

1. **Use HTTPS**: Always use HTTPS for the API URL
2. **Rotate API Keys**: Change API keys periodically
3. **Restrict Permissions**: Keep config file permissions at 600
4. **Network Segmentation**: Use firewall rules to restrict access
5. **Audit Logs**: Regularly review submission logs
6. **Minimal Access**: Only grant necessary SLURM permissions

## Updating the Agent

To update to a new version:

```bash
# On cluster
cd /tmp
git clone https://github.com/your-repo/slurm-usage-history.git
cd slurm-usage-history/cluster-agent

# Stop service
sudo systemctl stop slurm-usage-history-exporter.timer
sudo systemctl stop slurm-usage-history-exporter.service

# Update files
sudo cp slurm-usage-history-exporter.py /opt/slurm-usage-history-exporter/
sudo cp slurm-usage-history-exporter.service /etc/systemd/system/
sudo cp slurm-usage-history-exporter.timer /etc/systemd/system/

# Reload and restart
sudo systemctl daemon-reload
sudo systemctl start slurm-usage-history-exporter.timer
```

Configuration is preserved during updates.

## Uninstalling

To remove the agent:

```bash
# Stop and disable
sudo systemctl stop slurm-usage-history-exporter.timer
sudo systemctl disable slurm-usage-history-exporter.timer

# Remove files
sudo rm /etc/systemd/system/slurm-usage-history-exporter.{service,timer}
sudo systemctl daemon-reload
sudo rm -rf /opt/slurm-usage-history-exporter
sudo rm /usr/local/bin/slurm-usage-history-exporter

# Remove config (WARNING: deletes API key)
sudo rm -rf /etc/slurm-usage-history-exporter
```

## Getting Help

- **Full Documentation**: See `cluster-agent/README.md`
- **Quick Start**: See `cluster-agent/QUICKSTART.md`
- **Logs**: `journalctl -u slurm-usage-history-exporter.service -f`
- **Test Mode**: `slurm-usage-history-exporter --dry-run --verbose`

## Summary

The cluster agent provides a turnkey solution for collecting SLURM data and feeding it to your dashboard. It's designed to be:

- **Easy to deploy**: Single installation script
- **Reliable**: Built-in retries and error handling
- **Secure**: API key authentication, secure storage
- **Flexible**: Manual, cron, or systemd scheduling
- **Observable**: Complete logging via journald
- **Low maintenance**: Runs automatically once configured

Deploy it once, and your dashboard will automatically stay up-to-date with your cluster's usage data!
