# Ansible Deployment Guide - Phased Migration

This document explains how to use the Ansible playbook to deploy the new FastAPI/React dashboard to daic-dash alongside the existing Plotly/Dash dashboard.

## Overview

The Ansible configuration now supports a **phased deployment approach**:

- **Phase 1 (Testing Mode)**: Deploy new dashboard at `/v2-preview/` with HTTP Basic Auth, while old dashboard continues at `/`
- **Phase 2 (Production Mode)**: Switch to new dashboard at `/` with SAML authentication

## Directory Structure

```
ansible/
├── playbook.yml                    # Main deployment playbook
├── hosts                           # Inventory file (simple format)
├── host_vars/
│   ├── example.yml                 # Template configuration (tracked in git)
│   ├── daic-dash.yml               # Actual server config (git-ignored)
│   └── README.md                   # Instructions for using host_vars
├── files/
│   └── saml/
│       └── certs/
│           ├── sp.crt              # SAML SP certificate (git-ignored)
│           ├── sp.key              # SAML SP private key (git-ignored)
│           └── README.md           # Certificate instructions
├── templates/
│   ├── nginx-testing.conf.j2       # Nginx config for Phase 1 (testing)
│   ├── nginx.conf.j2               # Nginx config for Phase 2 (production)
│   └── ...                         # Other templates
└── docs/
    ├── PHASED_DEPLOYMENT.md        # Detailed 3-phase migration guide
    ├── BASIC_AUTH_SETUP.md         # HTTP Basic Auth instructions
    └── MIGRATION_GUIDE_DAIC.md     # Specific guide for daic-dash
```

## Quick Start - Phase 1 (Testing Deployment)

### 1. Verify Configuration

The `ansible/host_vars/daic-dash.yml` file should already be configured with:

```yaml
deployment_mode: testing  # Uses nginx-testing.conf.j2 for Phase 1
saml_enabled: true        # But SAML won't be used in testing mode
```

### 2. Check SAML Certificates

Verify certificates are in place:

```bash
ls -la ansible/files/saml/certs/
# Should show: sp.crt, sp.key
```

These were copied from the old deployment and will be deployed to `/opt/slurm-usage-history/saml/certs/`.

### 3. Run Deployment

```bash
cd ansible
ansible-playbook -i hosts playbook.yml
```

This will:
- Install system dependencies (Python, Node.js, nginx, etc.)
- Deploy application to `/opt/slurm-usage-history`
- Build frontend with Vite
- Copy SAML certificates
- Configure nginx with testing mode (nginx-testing.conf.j2)
- Start backend service on port 8100
- Serve new dashboard at `/v2-preview/` (protected with Basic Auth)
- Leave old dashboard running at `/` (unchanged)

### 4. Create HTTP Basic Auth Password File

On the daic-dash server:

```bash
# SSH to server
ssh sdrwacker@daic-dash

# Create password file
sudo htpasswd -c /opt/slurm-usage-history/.htpasswd testuser

# Enter password when prompted

# Reload nginx
sudo nginx -t && sudo systemctl reload nginx
```

See `docs/BASIC_AUTH_SETUP.md` for detailed instructions.

### 5. Test New Dashboard

Access the testing URL:

```
https://daic-dash.your-domain.edu/v2-preview/
```

You'll be prompted for username/password (Basic Auth), then the new dashboard loads.

Old dashboard remains accessible at:

```
https://daic-dash.your-domain.edu/
```

## Phase 2 - Production Cutover

When testing is complete and you're ready to switch to the new dashboard:

### 1. Update Host Configuration

Edit `ansible/host_vars/daic-dash.yml`:

```yaml
deployment_mode: production  # Switch to nginx.conf.j2
saml_enabled: true           # Enable SAML authentication
```

### 2. Verify SAML Configuration

Ensure `daic-dash.yml` has correct SAML IdP settings (extract from old deployment if needed).

### 3. Register SAML Endpoints with IdP

Update your Identity Provider with new SAML endpoints:

- **ACS URL**: `https://daic-dash.your-domain.edu/api/saml/acs`
- **SLS URL**: `https://daic-dash.your-domain.edu/api/saml/sls`
- **Metadata URL**: `https://daic-dash.your-domain.edu/api/saml/metadata`

### 4. Run Deployment

```bash
cd ansible
ansible-playbook -i hosts playbook.yml
```

This will:
- Switch nginx to production configuration
- New dashboard now at `/` with SAML authentication
- Old dashboard no longer accessible via nginx (but still running on port 8050 for fallback)

### 5. Verify Production

```bash
# Test main URL
curl -I https://daic-dash.your-domain.edu/

# Check SAML metadata
curl https://daic-dash.your-domain.edu/api/saml/metadata
```

## Deployment Modes Comparison

| Feature | Testing Mode (`deployment_mode: testing`) | Production Mode (`deployment_mode: production`) |
|---------|------------------------------------------|------------------------------------------------|
| **Nginx Template** | `nginx-testing.conf.j2` | `nginx.conf.j2` |
| **New Dashboard URL** | `/v2-preview/` | `/` |
| **Authentication** | HTTP Basic Auth | SAML |
| **Old Dashboard** | Still at `/` | Not exposed (can access via SSH tunnel to port 8050) |
| **SAML Registration** | Not required | Required |

## Useful Commands

### Check Deployment Status

```bash
# SSH to server
ssh sdrwacker@daic-dash

# Check backend service
sudo systemctl status slurm-usage-history-backend

# View backend logs
sudo journalctl -u slurm-usage-history-backend -f

# Check nginx config
sudo nginx -t

# Check nginx status
sudo systemctl status nginx
```

### Update Only Nginx Configuration

If you've made changes to nginx templates:

```bash
cd ansible
ansible-playbook -i hosts playbook.yml --tags nginx
```

### Update Only Backend Service

```bash
cd ansible
ansible-playbook -i hosts playbook.yml --tags deploy,systemd,service
```

### Rollback to Old Dashboard

If issues arise, see `docs/PHASED_DEPLOYMENT.md` for rollback procedures.

## Configuration Variables

Key variables in `ansible/host_vars/daic-dash.yml`:

| Variable | Purpose | Example |
|----------|---------|---------|
| `deployment_mode` | Controls which nginx template is used | `testing` or `production` |
| `app_base_dir` | Installation directory | `/opt/slurm-usage-history` |
| `app_data_dir` | Data directory (mounted drive) | `/data/slurm-usage-history` |
| `old_dashboard_port` | Port for old Plotly/Dash dashboard | `8050` |
| `backend_port` | Port for new FastAPI backend | `8100` |
| `saml_enabled` | Enable SAML authentication | `true` |

## Troubleshooting

### Backend not starting

```bash
sudo journalctl -u slurm-usage-history-backend -n 50
```

Common issues:
- Database connection problems (check `app_data_dir` is accessible)
- Python dependencies missing (rerun deployment)
- Port 8100 already in use

### Nginx configuration errors

```bash
sudo nginx -t
```

Common issues:
- Template variables not defined in `host_vars/`
- Missing SSL certificates
- Syntax errors in nginx templates

### SAML authentication not working

Check:
- SAML certificates are in place: `ls -la /opt/slurm-usage-history/saml/certs/`
- IdP configuration matches in `host_vars/daic-dash.yml`
- ACS/SLS URLs registered with IdP
- Backend logs for SAML errors

### Basic Auth not prompting

Check:
- `.htpasswd` file exists: `ls -la /opt/slurm-usage-history/.htpasswd`
- File permissions: `sudo chmod 640 /opt/slurm-usage-history/.htpasswd`
- Nginx config has `auth_basic` directives (testing mode only)

## Security Notes

1. **Sensitive Files**: `host_vars/daic-dash.yml` and SAML certificates are git-ignored
2. **HTTPS Required**: Both testing and production modes require HTTPS
3. **Basic Auth**: Only for Phase 1 testing - remove when switching to production
4. **SAML Certificates**: Reused from old deployment to avoid IdP re-registration

## Next Steps

1. **Phase 1**: Deploy in testing mode, test thoroughly at `/v2-preview/`
2. **Phase 2**: Switch to production mode, update IdP, cutover to new dashboard
3. **Cleanup**: After confidence period, decommission old Plotly/Dash dashboard

See `docs/PHASED_DEPLOYMENT.md` for detailed timeline and checklist.

## References

- [Phased Deployment Guide](../docs/PHASED_DEPLOYMENT.md) - Complete 3-phase migration strategy
- [Basic Auth Setup](../docs/BASIC_AUTH_SETUP.md) - HTTP Basic Authentication instructions
- [DAIC Migration Guide](../docs/MIGRATION_GUIDE_DAIC.md) - Specific guide for daic-dash server
- [Host Vars README](host_vars/README.md) - Using host-specific configuration
- [SAML Certificates README](files/saml/certs/README.md) - Certificate management
