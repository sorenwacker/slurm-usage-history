# Ansible Deployment Guide

This repository includes a complete Ansible setup for deploying the Slurm Usage History application with SAML authentication and automatic restart capabilities.

## What's Included

The Ansible deployment provides:

1. **Full Application Stack**
   - FastAPI backend with gunicorn workers
   - React frontend (built and served via nginx)
   - SAML SSO authentication
   - API key authentication for data ingestion

2. **System Integration**
   - Systemd service for backend (auto-restart on failure/reboot)
   - Nginx reverse proxy with optional SSL/TLS
   - Proper file permissions and service isolation
   - Production-ready configuration

3. **SAML Support**
   - Complete SAML 2.0 SP implementation
   - JWT-based session management
   - Automatic certificate generation
   - IdP integration support

## Quick Start

```bash
# 1. Navigate to ansible directory
cd ansible

# 2. Configure your deployment
cp inventory.yml.example inventory.yml
cp group_vars/all.yml.example group_vars/all.yml

# 3. Edit configuration files
nano inventory.yml          # Set your server IP
nano group_vars/all.yml     # Set all required variables

# 4. Deploy
ansible-playbook -i inventory.yml playbook.yml
```

## Documentation

- **[ansible/README.md](ansible/README.md)** - Complete deployment guide with:
  - Prerequisites and requirements
  - Detailed configuration instructions
  - SAML setup and IdP registration
  - SSL/TLS configuration (Let's Encrypt, self-signed, existing certs)
  - Troubleshooting guide
  - Security best practices

- **[ansible/QUICKSTART.md](ansible/QUICKSTART.md)** - Condensed quick reference:
  - Minimal steps to deploy
  - Common commands
  - Quick troubleshooting

## Key Features

### Automatic Restart
The backend service is configured with systemd to:
- Start automatically on system boot
- Restart on failure (up to 5 times in 5 minutes)
- Restart with 10-second delay between attempts

### SAML Authentication
- Full SAML 2.0 Service Provider (SP)
- Support for any SAML-compliant IdP
- Automatic SP certificate generation
- Session management with JWT tokens
- Login, logout, and metadata endpoints

### Production Ready
- Gunicorn with multiple workers
- Nginx reverse proxy with compression
- Security headers enabled
- Read-only file system for backend (except data directory)
- Systemd hardening (NoNewPrivileges, PrivateTmp, etc.)

## File Structure

```
ansible/
├── README.md                          # Complete guide
├── QUICKSTART.md                      # Quick reference
├── playbook.yml                       # Main Ansible playbook
├── inventory.yml.example              # Inventory template
├── group_vars/
│   └── all.yml.example               # Variables template
└── templates/
    ├── slurm-usage-backend.service.j2 # Systemd service
    ├── nginx.conf.j2                  # Nginx configuration
    ├── env.j2                         # Environment variables
    └── saml_settings.json.j2          # SAML configuration
```

## Deployment Targets

The playbook can deploy to:
- Physical workstations
- Virtual machines
- Cloud instances
- Multiple servers simultaneously

## Requirements

**Control machine** (where you run Ansible):
- Ansible 2.9+
- SSH access to target server(s)

**Target server**:
- Ubuntu 20.04+ or Debian 11+
- 2GB+ RAM, 10GB+ disk
- SSH with sudo access

**For SAML**:
- SAML IdP (Okta, Azure AD, Shibboleth, etc.)
- Domain name (recommended)
- SSL certificate (recommended for production)

## After Deployment

### Access Your Application
- Main app: `https://your-server/`
- API docs: `https://your-server/docs`
- SAML login: `https://your-server/saml/login`
- Health check: `https://your-server/api/dashboard/health`

### Manage Services
```bash
# View status
sudo systemctl status slurm-usage-backend

# Restart backend
sudo systemctl restart slurm-usage-backend

# View logs
sudo journalctl -u slurm-usage-backend -f
```

### Update Application
```bash
# Pull latest code and restart
ansible-playbook -i inventory.yml playbook.yml --tags deploy,service
```

## Backend Changes

The following SAML support has been added to the backend:

### New Files
- `backend/app/core/saml_auth.py` - SAML authentication module
- `backend/app/api/saml.py` - SAML endpoints (login, ACS, SLS, metadata)

### Modified Files
- `backend/app/main.py` - Added SAML router
- `pyproject.toml` - Added python3-saml and PyJWT dependencies

### New Dependencies
- `python3-saml>=1.15.0` - SAML 2.0 support
- `PyJWT>=2.8.0` - JWT session tokens

### SAML Endpoints
- `GET /saml/login` - Initiate SAML login
- `POST /saml/acs` - Assertion Consumer Service (IdP callback)
- `GET /saml/metadata` - SP metadata XML
- `GET /saml/logout` - Initiate logout
- `GET|POST /saml/sls` - Single Logout Service
- `GET /saml/status` - SAML configuration status

## Environment Variables

New environment variables for SAML:
```bash
ENABLE_SAML=true                                    # Enable SAML auth
SAML_SETTINGS_PATH=/path/to/saml/settings.json    # SAML config
SECRET_KEY=your-secret-key                         # JWT signing key
BASE_URL=https://your-server                       # Application URL
```

## Security Notes

1. **Always use HTTPS in production** - SAML requires secure communication
2. **Generate strong keys** - Use `openssl rand -hex 32` for secret_key
3. **Protect credentials** - Never commit `inventory.yml` or `group_vars/all.yml`
4. **Enable firewall** - Only expose ports 80/443
5. **Keep updated** - Regularly update system packages

## Support

For detailed information, see:
- [ansible/README.md](ansible/README.md) - Full deployment guide
- [ansible/QUICKSTART.md](ansible/QUICKSTART.md) - Quick reference
- [README_NEW_ARCHITECTURE.md](README_NEW_ARCHITECTURE.md) - Application architecture

## License

GPLv3+
