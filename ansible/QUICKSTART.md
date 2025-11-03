# Quick Start Guide - Ansible Deployment

This is a condensed guide to get you up and running quickly.

## 1. Install Ansible

```bash
# Ubuntu/Debian
sudo apt install ansible

# macOS
brew install ansible
```

## 2. Configure Your Deployment

### Edit Inventory
Edit `ansible/inventory.yml`:
```yaml
slurm-dashboard:
  ansible_host: YOUR_SERVER_IP
  ansible_user: YOUR_USERNAME
```

### Edit Variables
Edit `ansible/group_vars/all.yml`:

**Required changes:**
```yaml
# Deployment source
git_repo_url: "YOUR_GIT_REPO"  # or use local_app_path

# URLs
base_url: "https://slurm.example.com"
server_name: "slurm.example.com"

# Security (generate: openssl rand -hex 32)
secret_key: "GENERATE_RANDOM_KEY_HERE"
api_keys: "key1,key2,key3"

# SAML (get from your IT/SSO team)
saml_idp_entity_id: "https://idp.example.com/saml/metadata"
saml_idp_sso_url: "https://idp.example.com/saml/sso"
saml_idp_cert: |
  YOUR_IDP_CERTIFICATE_HERE

# SSL (if using HTTPS)
enable_https: true
ssl_cert_path: "/etc/ssl/certs/your-cert.crt"
ssl_key_path: "/etc/ssl/private/your-key.key"
```

## 3. Deploy

```bash
cd ansible

# Test connection
ansible -i inventory.yml workstations -m ping

# Deploy everything
ansible-playbook -i inventory.yml playbook.yml

# Or deploy with verbose output
ansible-playbook -i inventory.yml playbook.yml -vv
```

## 4. Post-Deployment

### Register with IdP
1. Get your SP metadata:
   ```bash
   curl https://your-server/saml/metadata > sp-metadata.xml
   ```
2. Send `sp-metadata.xml` to your IdP admin
3. Or manually configure:
   - Entity ID: `https://your-server/saml/metadata`
   - ACS URL: `https://your-server/saml/acs`

### Test SAML Login
Visit: `https://your-server/saml/login`

### Verify Services
```bash
# On the target server
sudo systemctl status slurm-usage-backend
sudo systemctl status nginx
```

## Common Commands

### Update Application
```bash
ansible-playbook -i inventory.yml playbook.yml --tags deploy,service
```

### Restart Services
```bash
# On target server
sudo systemctl restart slurm-usage-backend
sudo systemctl restart nginx
```

### View Logs
```bash
# Backend logs
sudo journalctl -u slurm-usage-backend -f

# Nginx logs
sudo tail -f /var/log/nginx/slurm-usage-error.log
```

## Quick Troubleshooting

### Backend won't start
```bash
sudo journalctl -u slurm-usage-backend -n 50
```

### SAML errors
```bash
# Check SAML status
curl https://your-server/saml/status

# View SAML config
sudo cat /opt/slurm-usage-history/saml/settings.json
```

### Nginx errors
```bash
sudo nginx -t
sudo tail -f /var/log/nginx/error.log
```

## Need More Help?

See the full [README.md](README.md) for:
- Detailed configuration options
- SSL/TLS setup (Let's Encrypt, self-signed, etc.)
- Advanced troubleshooting
- Security best practices
- Architecture details
