# Phased Deployment Guide - New Dashboard Alongside Old

This guide documents the phased approach to deploying the new FastAPI/React dashboard alongside the existing Plotly/Dash dashboard.

## Overview

**Goal**: Deploy and test new dashboard without touching SAML or affecting production users.

**Strategy**: Three-phase deployment
1. Phase 1: Deploy at secret URL for internal testing (no SAML)
2. Phase 2: Register SAML, prepare for cutover
3. Phase 3: Switch production traffic to new dashboard

---

## Phase 1: Internal Testing Deployment

### Objective
Deploy new dashboard at a secret URL path for internal testing without SAML authentication.

### URLs During Phase 1
```
Production (unchanged):
  https://daic-dash.example.edu/              → Old Dash (with SAML)

Testing (new):
  https://daic-dash.example.edu/v2-preview/   → New Dashboard (no auth)
```

### Deployment Steps

#### 1. Prepare Ansible Configuration

Edit `ansible/host_vars/daic-dash.yml`:
```yaml
# Deployment mode: testing (will use nginx-testing.conf)
deployment_mode: testing

# SAML disabled for phase 1 testing
saml_enabled: false

# Other settings remain the same
app_user: slurmusage
app_base_dir: /opt/slurm-usage-history
app_data_dir: /data/slurm-usage-history
backend_port: 8100
```

#### 2. Run Ansible Deployment

```bash
cd ansible
ansible-playbook -i hosts playbook.yml --ask-become-pass

# Or for specific host:
ansible-playbook -i hosts playbook.yml --limit daic-dash --ask-become-pass
```

#### 3. Verify Deployment

```bash
# SSH to daic-dash
ssh sdrwacker@daic-dash

# Check new backend is running
sudo systemctl status slurm-usage-history-backend

# Check logs
sudo journalctl -u slurm-usage-history-backend -f

# Test health endpoint
curl http://localhost:8100/health

# Check nginx configuration
sudo nginx -t
sudo systemctl status nginx
```

#### 4. Test the New Dashboard

**From your local machine with SSH tunnel:**
```bash
# Create SSH tunnel
ssh -L 8100:localhost:8100 sdrwacker@daic-dash

# In browser, visit:
http://localhost:8100/api/dashboard/metadata
```

**Or directly via secret URL** (if you're on the network):
```
https://daic-dash.example.edu/v2-preview/
```

### Testing Checklist

- [ ] Dashboard loads without errors
- [ ] Can select hostname/cluster
- [ ] Charts render correctly
- [ ] Filters work (partition, account, date range)
- [ ] Weekly/Monthly views work
- [ ] Data matches old dashboard
- [ ] Report generation works
- [ ] Admin panel accessible (if needed)
- [ ] Performance is acceptable

### Security During Phase 1

Since SAML is disabled, access control options:

1. **IP Restriction** (nginx)
   ```nginx
   location /v2-preview/ {
       # Only allow from specific IPs
       allow 192.168.1.0/24;  # Your internal network
       allow 10.0.0.0/8;       # VPN range
       deny all;

       alias /opt/slurm-usage-history/frontend/dist/;
       # ...
   }
   ```

2. **SSH Tunnel** (most secure for initial testing)
   ```bash
   ssh -L 8443:localhost:443 sdrwacker@daic-dash
   # Access via https://localhost:8443/v2-preview/
   ```

3. **Basic Auth** (temporary)
   ```nginx
   location /v2-preview/ {
       auth_basic "Testing Area";
       auth_basic_user_file /etc/nginx/.htpasswd;
       # ...
   }
   ```

---

## Phase 2: SAML Registration & Preparation

### Objective
Register new SAML endpoints with IdP and prepare for cutover.

### Prerequisites
- Phase 1 testing completed successfully
- Team has approved new dashboard
- Ready to update IdP configuration

### Steps

#### 1. Extract Current SAML Configuration

On daic-dash server:
```bash
# Find current SAML config from old dashboard
cd /home/sdrwacker/workspace/slurm-usage-history
grep -r "entityId\|AssertionConsumerService" . | grep -v ".pyc"

# Extract IdP metadata
# (Location depends on your old setup - could be in config.py, settings.py, etc.)
```

#### 2. Update Ansible Configuration

Edit `ansible/host_vars/daic-dash.yml`:
```yaml
# Enable SAML for phase 2
saml_enabled: true

# SAML SP Configuration (reuse existing Entity ID if possible)
saml_sp_entity_id: "https://daic-dash.example.edu/saml/metadata"

# NEW endpoints for FastAPI backend
saml_sp_acs_url: "https://daic-dash.example.edu/api/saml/acs"
saml_sp_sls_url: "https://daic-dash.example.edu/api/saml/sls"

# IdP Configuration (copy from old setup)
saml_idp_entity_id: "https://idp.your-domain.edu/idp/shibboleth"
saml_idp_sso_url: "https://idp.your-domain.edu/idp/profile/SAML2/Redirect/SSO"
saml_idp_slo_url: "https://idp.your-domain.edu/idp/profile/SAML2/Redirect/SLO"
saml_idp_x509_cert: |
  -----BEGIN CERTIFICATE-----
  (paste IdP certificate here)
  -----END CERTIFICATE-----

# JWT Session Configuration
jwt_secret_key: "{{ lookup('password', '/dev/null length=64 chars=ascii_letters,digits') }}"
session_expiry_hours: 24
```

#### 3. Register with Identity Provider

Update your IdP configuration to add new Assertion Consumer Service URL:

**New ACS URL:** `https://daic-dash.example.edu/api/saml/acs`
**New SLS URL:** `https://daic-dash.example.edu/api/saml/sls`
**Metadata URL:** `https://daic-dash.example.edu/api/saml/metadata`

Keep old URLs active during transition:
- Old ACS: `https://daic-dash.example.edu/saml/acs` (for old dashboard)
- New ACS: `https://daic-dash.example.edu/api/saml/acs` (for new dashboard)

#### 4. Test SAML at Secret URL

Update nginx config to enable SAML for `/v2-preview/`:
```nginx
location /v2-preview/api/saml/ {
    proxy_pass http://127.0.0.1:8100/api/saml/;
    # ... proxy settings
}
```

Test SAML login at `https://daic-dash.example.edu/v2-preview/`

---

## Phase 3: Production Cutover

### Objective
Switch production traffic from old dashboard to new dashboard.

### Pre-Cutover Checklist

- [ ] Phase 1 & 2 testing complete
- [ ] SAML working correctly
- [ ] Performance tested with real data
- [ ] Backup of old dashboard configuration
- [ ] Rollback plan documented
- [ ] Communication sent to users

### Cutover Steps

#### 1. Backup Current Configuration

```bash
# On daic-dash server
sudo cp /etc/nginx/sites-available/daic-dash /etc/nginx/sites-available/daic-dash.backup.$(date +%Y%m%d)
sudo systemctl stop plotly-dashboard  # or whatever your old service is called
```

#### 2. Switch Nginx Configuration

```bash
# Update to production nginx config
sudo cp /opt/slurm-usage-history/nginx-production.conf /etc/nginx/sites-available/daic-dash

# Test configuration
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx
```

#### 3. Verify Production

```bash
# Test main URL
curl -I https://daic-dash.example.edu/

# Check SAML
curl https://daic-dash.example.edu/api/saml/metadata

# Monitor logs
sudo journalctl -u slurm-usage-history-backend -f
```

#### 4. Monitor

Watch for:
- Error rates in logs
- User login issues
- Performance problems
- User feedback

### Post-Cutover URLs

```
Production (new):
  https://daic-dash.example.edu/              → New Dashboard (with SAML)

Old Dashboard (fallback):
  Still running on port 8050, not exposed via nginx
  Can access via SSH tunnel if needed for comparison
```

---

## Rollback Procedure

If issues arise, rollback to old dashboard:

```bash
# On daic-dash server

# 1. Restore old nginx config
sudo cp /etc/nginx/sites-available/daic-dash.backup.YYYYMMDD /etc/nginx/sites-available/daic-dash

# 2. Test and reload
sudo nginx -t && sudo systemctl reload nginx

# 3. Restart old dashboard
sudo systemctl start plotly-dashboard

# 4. Verify
curl -I https://daic-dash.example.edu/
```

The new dashboard continues running at port 8100, so you can investigate issues and try cutover again later.

---

## Timeline Recommendation

- **Phase 1**: 1-2 weeks of internal testing
- **Phase 2**: 3-5 days for SAML setup and testing
- **Phase 3**: Cutover during low-usage period (weekend/evening)

---

## Keeping Old Dashboard as Fallback

After successful cutover, you can keep the old dashboard running for 2-4 weeks as a safety net:

1. Leave service running on port 8050
2. Not exposed via nginx (no public access)
3. Accessible via SSH tunnel if comparison needed
4. Decommission after confidence period

```bash
# To access old dashboard for comparison
ssh -L 8050:localhost:8050 sdrwacker@daic-dash

# Visit in browser
http://localhost:8050
```

---

## Notes

- Change `/v2-preview/` to any secret path you prefer (`/beta-test-xyz/`, `/internal-preview/`, etc.)
- Old dashboard continues working throughout all phases
- No impact to users until Phase 3 cutover
- Easy rollback at any point
