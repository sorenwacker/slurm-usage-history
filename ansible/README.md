# Ansible Deployment for Slurm Usage History

This Ansible playbook automates the deployment of the Slurm Usage History application with SAML authentication on a workstation. The application will be configured to restart automatically using systemd.

## Features

- Automated installation of all system dependencies (Python 3.10+, Node.js 18+, nginx)
- SAML SSO authentication support
- Systemd service for automatic restart on failure or reboot
- Nginx reverse proxy with optional HTTPS
- Production-ready configuration with gunicorn workers
- Secure file permissions and service isolation

## Prerequisites

### Control Machine (where you run Ansible)
- Ansible 2.9 or later
- SSH access to target workstation(s)

### Target Workstation
- Ubuntu 20.04+ or Debian 11+ (other distributions may work with modifications)
- SSH access with sudo privileges
- At least 2GB RAM, 10GB disk space

### SAML Configuration
- Access to your organization's SAML Identity Provider (IdP)
- IdP metadata (entity ID, SSO URL, X.509 certificate)
- Domain name for the application (optional but recommended)
- SSL/TLS certificate (optional, can use Let's Encrypt or self-signed)

## Quick Start

### 1. Install Ansible

```bash
# On Ubuntu/Debian
sudo apt update
sudo apt install ansible

# On macOS
brew install ansible

# Or using pip
pip install ansible
```

### 2. Configure Inventory

Edit `inventory.yml` and update the host information:

```yaml
all:
  children:
    workstations:
      hosts:
        slurm-dashboard:
          ansible_host: 192.168.1.100    # Your workstation IP
          ansible_user: your-username    # SSH username
```

### 3. Configure Variables

Copy and edit `group_vars/all.yml`:

```bash
cd ansible
cp group_vars/all.yml group_vars/all.yml.backup
nano group_vars/all.yml
```

**Critical variables to configure:**

1. **Deployment method** (choose one):
   ```yaml
   # Option 1: Git repository
   git_repo_url: "https://github.com/your-org/slurm-usage-history.git"
   git_branch: "main"

   # Option 2: Local directory (comment out git_repo_url)
   # local_app_path: "/path/to/local/slurm-usage-history"
   ```

2. **Application URLs**:
   ```yaml
   base_url: "https://slurm-dashboard.example.com"
   server_name: "slurm-dashboard.example.com"
   ```

3. **API Keys** (generate random keys):
   ```yaml
   api_keys: "secret-key-1,secret-key-2"
   ```

4. **Secret Key** (generate with `openssl rand -hex 32`):
   ```yaml
   secret_key: "your-random-secret-key-here"
   ```

5. **SAML IdP Configuration**:
   ```yaml
   saml_idp_entity_id: "https://idp.example.com/saml/metadata"
   saml_idp_sso_url: "https://idp.example.com/saml/sso"
   saml_idp_cert: |
     MIIDXTCCAkWgAwIBAgIJAKHd...
     (your IdP X.509 certificate)
   ```

6. **SSL/TLS** (if using HTTPS):
   ```yaml
   enable_https: true
   ssl_cert_path: "/etc/ssl/certs/slurm-dashboard.crt"
   ssl_key_path: "/etc/ssl/private/slurm-dashboard.key"
   ```

### 4. Test Connection

```bash
ansible -i inventory.yml workstations -m ping
```

### 5. Run Deployment

```bash
# Full deployment
ansible-playbook -i inventory.yml playbook.yml

# Or with verbose output
ansible-playbook -i inventory.yml playbook.yml -v

# Deploy only specific parts using tags
ansible-playbook -i inventory.yml playbook.yml --tags "dependencies,deploy"
```

## Available Tags

Run specific parts of the playbook using tags:

```bash
# Install dependencies only
ansible-playbook -i inventory.yml playbook.yml --tags dependencies

# Deploy application code
ansible-playbook -i inventory.yml playbook.yml --tags deploy

# Configure SAML
ansible-playbook -i inventory.yml playbook.yml --tags saml

# Update systemd services
ansible-playbook -i inventory.yml playbook.yml --tags systemd

# Update nginx configuration
ansible-playbook -i inventory.yml playbook.yml --tags nginx

# Restart services
ansible-playbook -i inventory.yml playbook.yml --tags service
```

## SAML Configuration

### Getting IdP Information

1. Contact your IT/SSO administrator for:
   - IdP Entity ID
   - SSO URL
   - SLO URL (optional)
   - IdP X.509 certificate

2. Or download IdP metadata XML and extract:
   ```xml
   <EntityDescriptor entityID="...">  <!-- This is IdP Entity ID -->
     <IDPSSODescriptor>
       <SingleSignOnService Binding="..." Location="..."/>  <!-- SSO URL -->
       <X509Certificate>...</X509Certificate>  <!-- IdP certificate -->
     </IDPSSODescriptor>
   </EntityDescriptor>
   ```

### Registering SP with IdP

After deployment, you need to register the Service Provider (SP) with your IdP:

1. Get SP metadata:
   ```bash
   curl https://slurm-dashboard.example.com/saml/metadata > sp-metadata.xml
   ```

2. Provide this metadata to your IdP administrator

3. Key SP information:
   - Entity ID: `https://slurm-dashboard.example.com/saml/metadata`
   - ACS URL: `https://slurm-dashboard.example.com/saml/acs`
   - SLS URL: `https://slurm-dashboard.example.com/saml/sls`

### Testing SAML

1. Visit: `https://slurm-dashboard.example.com/saml/login`
2. You should be redirected to your IdP login page
3. After authentication, you should be redirected back to the dashboard

### SAML Attributes

The application will receive user attributes from the IdP. Common attributes:
- `email` or `mail`: User's email address
- `displayName` or `cn`: User's full name
- `uid` or `username`: User's username
- `groups` or `memberOf`: User's group memberships

## Post-Deployment

### Verify Services

```bash
# Check backend service status
sudo systemctl status slurm-usage-backend

# Check nginx status
sudo systemctl status nginx

# View backend logs
sudo journalctl -u slurm-usage-backend -f

# View nginx logs
sudo tail -f /var/log/nginx/slurm-usage-access.log
sudo tail -f /var/log/nginx/slurm-usage-error.log
```

### Access the Application

- Main application: `https://slurm-dashboard.example.com/`
- API documentation: `https://slurm-dashboard.example.com/docs`
- SAML metadata: `https://slurm-dashboard.example.com/saml/metadata`
- Health check: `https://slurm-dashboard.example.com/api/dashboard/health`

### Restart Services

```bash
# Restart backend only
sudo systemctl restart slurm-usage-backend

# Restart nginx only
sudo systemctl restart nginx

# Restart both
sudo systemctl restart slurm-usage-backend nginx
```

### Update Application

To update the application code:

```bash
# If using git deployment
ansible-playbook -i inventory.yml playbook.yml --tags deploy,service

# This will:
# 1. Pull latest code from git
# 2. Install new dependencies
# 3. Rebuild frontend
# 4. Restart services
```

## SSL/TLS Configuration

### Option 1: Let's Encrypt (Recommended for Production)

1. Install certbot:
   ```bash
   sudo apt install certbot python3-certbot-nginx
   ```

2. Obtain certificate:
   ```bash
   sudo certbot --nginx -d slurm-dashboard.example.com
   ```

3. Update `group_vars/all.yml`:
   ```yaml
   enable_https: true
   ssl_cert_path: "/etc/letsencrypt/live/slurm-dashboard.example.com/fullchain.pem"
   ssl_key_path: "/etc/letsencrypt/live/slurm-dashboard.example.com/privkey.pem"
   ```

4. Re-run nginx configuration:
   ```bash
   ansible-playbook -i inventory.yml playbook.yml --tags nginx
   ```

### Option 2: Self-Signed Certificate (Development/Testing)

```bash
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/ssl/private/slurm-dashboard.key \
  -out /etc/ssl/certs/slurm-dashboard.crt \
  -subj "/CN=slurm-dashboard.example.com"
```

### Option 3: Existing Certificate

Copy your certificate files to the target server and update paths in `group_vars/all.yml`.

## Troubleshooting

### Backend won't start

```bash
# Check logs
sudo journalctl -u slurm-usage-backend -n 50

# Check if port 8100 is in use
sudo netstat -tulpn | grep 8100

# Verify environment file
sudo cat /opt/slurm-usage-history/.env

# Test backend manually
cd /opt/slurm-usage-history
source .venv/bin/activate
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8100
```

### SAML authentication fails

```bash
# Check SAML settings
sudo cat /opt/slurm-usage-history/saml/settings.json

# Verify certificates exist
sudo ls -la /opt/slurm-usage-history/saml/certs/

# Check SAML status endpoint
curl https://slurm-dashboard.example.com/saml/status

# View detailed backend logs
sudo journalctl -u slurm-usage-backend -f
```

### Nginx errors

```bash
# Test nginx configuration
sudo nginx -t

# Check nginx error logs
sudo tail -f /var/log/nginx/error.log

# Verify upstream backend is running
curl http://127.0.0.1:8100/api/dashboard/health
```

### Permission issues

```bash
# Verify file ownership
sudo ls -la /opt/slurm-usage-history/
sudo ls -la /opt/slurm-usage-history/data/

# Fix permissions if needed
sudo chown -R your-user:your-user /opt/slurm-usage-history/
```

## Security Considerations

1. **Firewall**: Ensure only necessary ports are open (80/443)
   ```bash
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw enable
   ```

2. **SSH Key Authentication**: Disable password authentication for SSH
3. **Keep Updated**: Regularly update system packages and application
4. **API Keys**: Use strong, randomly generated API keys
5. **Secret Key**: Use a strong secret key for JWT tokens
6. **HTTPS**: Always use HTTPS in production
7. **SAML**: Use signed assertions and requests in production

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                        Nginx                            │
│  - Serves static frontend files                         │
│  - Reverse proxy to backend API                         │
│  - SAML endpoints proxy                                 │
│  - SSL/TLS termination                                  │
└────────────┬──────────────────────────┬─────────────────┘
             │                          │
             ▼                          ▼
    Frontend (React)          Backend (FastAPI)
    /opt/.../frontend/dist    systemd: slurm-usage-backend
                              - Port 127.0.0.1:8100
                              - Gunicorn + Uvicorn workers
                              - Auto-restart on failure
                              │
                              ▼
                         Data Storage
                    /opt/.../data/*.parquet
```

## File Locations

- Application: `/opt/slurm-usage-history/`
- Data directory: `/opt/slurm-usage-history/data/`
- SAML config: `/opt/slurm-usage-history/saml/`
- Environment file: `/opt/slurm-usage-history/.env`
- Systemd service: `/etc/systemd/system/slurm-usage-backend.service`
- Nginx config: `/etc/nginx/sites-available/slurm-usage-history`
- Logs (backend): `journalctl -u slurm-usage-backend`
- Logs (nginx): `/var/log/nginx/slurm-usage-*.log`

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Review application logs
3. Consult the main project README
4. Open an issue on the project repository

## License

GPLv3+
