# Quick Start Guide - SLURM Usage History Exporter

## 5-Minute Setup

### 1. Copy to Cluster

```bash
scp -r cluster-agent/ user@cluster:/tmp/
```

### 2. Install

```bash
ssh user@cluster
cd /tmp/cluster-agent
sudo ./install.sh
```

### 3. Configure

```bash
sudo nano /etc/slurm-usage-history-exporter/config.json
```

Edit these two lines:
```json
{
  "api_url": "https://your-dashboard.example.com",
  "api_key": "your-secret-api-key"
}
```

### 4. Test

```bash
sudo slurm-usage-history-exporter --dry-run --verbose
```

### 5. Run

```bash
# Manual run
sudo slurm-usage-history-exporter

# Or enable automatic daily collection
sudo systemctl enable slurm-usage-history-exporter.timer
sudo systemctl start slurm-usage-history-exporter.timer
```

### 6. Verify

Check logs:
```bash
sudo journalctl -u slurm-usage-history-exporter.service -f
```

Check timer:
```bash
systemctl status slurm-usage-history-exporter.timer
```

## That's It!

Your cluster will now automatically submit job data to your dashboard daily at 2:00 AM.

See [README.md](README.md) for detailed documentation.
