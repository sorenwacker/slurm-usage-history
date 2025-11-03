# DAIC Deployment Guide

Quick guide for deploying to `dashboard.daic.tudelft.nl` with your existing nginx and Let's Encrypt setup.

## Your Current Setup

From your existing nginx config, you have:
- Domain: `dashboard.daic.tudelft.nl`
- SSL: Let's Encrypt certificates (auto-renewed)
- Current service on port `8080`
- Nginx already configured with SSL

## What Will Change

The new deployment will:
- Keep your existing Let's Encrypt SSL certificates ✅
- Keep your nginx SSL configuration ✅
- Add a new backend service on port `8100` (FastAPI)
- Update nginx to serve the new React frontend
- Add SAML authentication endpoints
- Add systemd service for auto-restart

**Your port 8080 service will remain untouched** - the new app runs on port 8100.

## Quick Deployment

### 1. Prepare Configuration

```bash
cd ansible

# Use DAIC-specific configuration
cp inventory-daic.yml inventory.yml
cp group_vars/daic.yml group_vars/all.yml

# Edit the inventory with your SSH user
nano inventory.yml
# Change: ansible_user: sdrwacker  # to your username
```

### 2. Create Secrets File

```bash
# Generate secrets
API_KEY1=$(openssl rand -base64 32)
API_KEY2=$(openssl rand -base64 32)
SECRET_KEY=$(openssl rand -hex 32)

echo "Generated secrets (save these securely!):"
echo "API_KEY1: $API_KEY1"
echo "API_KEY2: $API_KEY2"
echo "SECRET_KEY: $SECRET_KEY"

# Create encrypted secrets
ansible-vault create group_vars/secrets.yml

# Add to the file:
---
api_keys: "$API_KEY1,$API_KEY2"
secret_key: "$SECRET_KEY"
saml_idp_cert: |
  (paste TU Delft IdP certificate here)
```

### 3. Get TU Delft SAML Info

Contact TU Delft IT Services for:
- IdP Entity ID
- IdP SSO URL
- IdP Certificate

Or download from: https://idp.tudelft.nl/saml/metadata (if available)

Update in `group_vars/all.yml`:
```yaml
saml_idp_entity_id: "https://idp.tudelft.nl/saml/metadata"
saml_idp_sso_url: "https://idp.tudelft.nl/saml/sso"
```

### 4. Deploy Application

```bash
# Full deployment
ansible-playbook -i inventory.yml playbook.yml --ask-vault-pass

# This will:
# - Install dependencies (Python 3.10, Node.js, etc.)
# - Deploy the application to /opt/slurm-usage-history
# - Create systemd service (slurm-usage-backend)
# - Build React frontend
# - Update nginx configuration
# - Start services
```

### 5. Update Nginx (Careful!)

The playbook creates a new nginx config but doesn't replace your existing one automatically.

**Option A: Review and manually switch** (Recommended)
```bash
# On the server, review the new config
ssh dashboard.daic.tudelft.nl
sudo cat /etc/nginx/sites-available/slurm-usage-history

# Test it
sudo nginx -t -c /etc/nginx/sites-available/slurm-usage-history

# If OK, switch
sudo mv /etc/nginx/sites-enabled/default /etc/nginx/sites-enabled/default.backup
sudo ln -s /etc/nginx/sites-available/slurm-usage-history /etc/nginx/sites-enabled/slurm-usage-history
sudo nginx -t
sudo systemctl reload nginx
```

**Option B: Use update playbook**
```bash
ansible-playbook -i inventory.yml playbook-update-nginx.yml
```

### 6. Register with TU Delft IdP

After deployment:

```bash
# Get SP metadata
curl https://dashboard.daic.tudelft.nl/saml/metadata > sp-metadata.xml

# Send to TU Delft IT Services with this info:
# - Entity ID: https://dashboard.daic.tudelft.nl/saml/metadata
# - ACS URL: https://dashboard.daic.tudelft.nl/saml/acs
# - SLS URL: https://dashboard.daic.tudelft.nl/saml/sls
```

### 7. Test

```bash
# Test backend health
curl https://dashboard.daic.tudelft.nl/api/dashboard/health

# Test SAML login (in browser)
# Visit: https://dashboard.daic.tudelft.nl/saml/login

# Check backend logs
ssh dashboard.daic.tudelft.nl
sudo journalctl -u slurm-usage-backend -f
```

## Port Configuration

- **Port 8080**: Your existing service (unchanged)
- **Port 8100**: New FastAPI backend (localhost only, proxied by nginx)
- **Port 80**: HTTP (redirects to HTTPS)
- **Port 443**: HTTPS (nginx handles SSL)

## File Locations

- Application: `/opt/slurm-usage-history/`
- Data: `/opt/slurm-usage-history/data/`
- SAML config: `/opt/slurm-usage-history/saml/`
- Frontend: `/opt/slurm-usage-history/frontend/dist/`
- Systemd service: `/etc/systemd/system/slurm-usage-backend.service`
- Nginx config: `/etc/nginx/sites-available/slurm-usage-history`
- Logs: `journalctl -u slurm-usage-backend`

## Managing the Service

```bash
# Check status
sudo systemctl status slurm-usage-backend

# Restart
sudo systemctl restart slurm-usage-backend

# View logs
sudo journalctl -u slurm-usage-backend -f

# Stop
sudo systemctl stop slurm-usage-backend

# Disable auto-start
sudo systemctl disable slurm-usage-backend
```

## Update Application Code

```bash
# Pull latest code and restart
ansible-playbook -i inventory.yml playbook.yml --tags deploy,service --ask-vault-pass
```

## Rollback Plan

If something goes wrong:

```bash
# On the server:

# 1. Stop new service
sudo systemctl stop slurm-usage-backend

# 2. Restore original nginx config
sudo rm /etc/nginx/sites-enabled/slurm-usage-history
sudo mv /etc/nginx/sites-enabled/default.backup /etc/nginx/sites-enabled/default
sudo systemctl reload nginx

# 3. Your port 8080 service should still be running
```

## Troubleshooting

### Backend won't start
```bash
sudo journalctl -u slurm-usage-backend -n 100
sudo systemctl status slurm-usage-backend

# Check if dependencies installed
/opt/slurm-usage-history/.venv/bin/python --version
```

### Nginx errors
```bash
sudo nginx -t
sudo tail -f /var/log/nginx/error.log
```

### SAML issues
```bash
# Check SAML config
sudo cat /opt/slurm-usage-history/saml/settings.json

# Check certificates
sudo ls -la /opt/slurm-usage-history/saml/certs/
```

### Port conflicts
```bash
# Check what's on port 8100
sudo netstat -tulpn | grep 8100

# If needed, change backend_port in group_vars/all.yml
```

## Let's Encrypt Certificate Renewal

Your existing certbot renewal will continue to work. The new nginx config uses the same certificate paths:
```
ssl_certificate /etc/letsencrypt/live/dashboard.daic.tudelft.nl/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/dashboard.daic.tudelft.nl/privkey.pem;
```

No changes needed!

## Security Notes

1. **SAML authentication** will be required to access the dashboard
2. **API keys** still needed for data ingestion (automated jobs)
3. Backend runs on **localhost only** (not exposed directly)
4. Systemd service runs with **security hardening** enabled

## Questions?

- See main [README.md](README.md) for detailed documentation
- See [SECRETS.md](SECRETS.md) for secrets management
- Check logs: `sudo journalctl -u slurm-usage-backend -f`
