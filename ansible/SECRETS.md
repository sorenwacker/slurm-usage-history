# Secrets Management Guide

This guide explains how to securely manage secrets for the Ansible deployment.

## Quick Start with Ansible Vault (Recommended)

### 1. Create Encrypted Secrets File

```bash
cd ansible

# Create encrypted secrets file
ansible-vault create group_vars/secrets.yml
```

Enter a strong vault password when prompted. Then add your secrets:

```yaml
---
# API Keys for data ingestion
api_keys: "abc123xyz,def456uvw,ghi789rst"

# Secret key for JWT tokens (generate with: openssl rand -hex 32)
secret_key: "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2"

# SAML IdP Certificate
saml_idp_cert: |
  MIIDXTCCAkWgAwIBAgIJAKHdGN8QF...
  (your actual IdP certificate content)
```

### 2. Generate Secrets

```bash
# Generate API keys
openssl rand -base64 32  # Run this 3 times for 3 keys

# Generate secret key
openssl rand -hex 32

# Get SAML IdP certificate from your IdP admin or metadata XML
```

### 3. Deploy with Vault

```bash
# Run playbook (you'll be prompted for vault password)
ansible-playbook -i inventory.yml playbook.yml --ask-vault-pass

# Or use a password file
echo "your-vault-password" > .vault_pass
chmod 600 .vault_pass
ansible-playbook -i inventory.yml playbook.yml --vault-password-file .vault_pass
```

### 4. Edit Encrypted Secrets Later

```bash
# Edit secrets
ansible-vault edit group_vars/secrets.yml

# View secrets (without editing)
ansible-vault view group_vars/secrets.yml

# Change vault password
ansible-vault rekey group_vars/secrets.yml
```

## Alternative: Environment Variables

Pass secrets directly without storing them:

```bash
# Generate secrets
API_KEYS=$(openssl rand -base64 32),$(openssl rand -base64 32)
SECRET_KEY=$(openssl rand -hex 32)

# Run with environment variables
ansible-playbook -i inventory.yml playbook.yml \
  -e "api_keys=$API_KEYS" \
  -e "secret_key=$SECRET_KEY" \
  -e "saml_idp_cert='$(cat /path/to/idp-cert.pem)'"
```

## Alternative: Separate Encrypted Variables

Create multiple encrypted files for different purposes:

```bash
# Secrets for API
ansible-vault create group_vars/api_secrets.yml

# Secrets for SAML
ansible-vault create group_vars/saml_secrets.yml

# All use the same vault password
ansible-playbook -i inventory.yml playbook.yml --ask-vault-pass
```

## Vault Password Management

### Option 1: Password File (Most Common)

```bash
# Create password file
echo "MyVerySecureVaultPassword123!" > .vault_pass
chmod 600 .vault_pass

# Add to ansible.cfg
cat >> ansible.cfg <<EOF
[defaults]
vault_password_file = .vault_pass
EOF

# Now you can run without --ask-vault-pass
ansible-playbook -i inventory.yml playbook.yml
```

### Option 2: Environment Variable

```bash
export ANSIBLE_VAULT_PASSWORD_FILE=.vault_pass
ansible-playbook -i inventory.yml playbook.yml
```

### Option 3: Script (for integration with password managers)

Create `vault-pass.sh`:
```bash
#!/bin/bash
# Get password from your password manager
# Example with macOS Keychain:
security find-generic-password -w -s ansible-vault -a $(whoami)
```

Make executable and use:
```bash
chmod +x vault-pass.sh
ansible-playbook -i inventory.yml playbook.yml --vault-password-file ./vault-pass.sh
```

## Security Best Practices

### 1. Generate Strong Secrets

```bash
# API keys (use 3+ different keys)
openssl rand -base64 32
openssl rand -base64 32
openssl rand -base64 32

# Secret key (for JWT - must be strong)
openssl rand -hex 32

# Or use a password generator
pwgen -s 64 1
```

### 2. Never Commit Secrets

The `.gitignore` already excludes:
- `group_vars/all.yml`
- `group_vars/secrets.yml`
- `.vault_pass`
- `vault_pass.txt`

**Always check before committing:**
```bash
git status
git diff --cached
```

### 3. Encrypt SAML Certificates

Even though IdP certificates are semi-public, it's good practice to encrypt them:

```bash
# Create encrypted SAML config
ansible-vault create group_vars/saml_secrets.yml
```

Add to `saml_secrets.yml`:
```yaml
---
saml_idp_cert: |
  MIIDXTCCAkWgAwIBAgIJAKHd...
  (full certificate)

# Optional: If your SP cert is pre-generated
saml_sp_cert_file: "/local/path/to/sp.crt"
saml_sp_key_file: "/local/path/to/sp.key"
```

### 4. Separate Environments

For multiple environments (dev/staging/prod):

```
ansible/
├── inventories/
│   ├── dev/
│   │   ├── inventory.yml
│   │   └── group_vars/
│   │       ├── all.yml
│   │       └── secrets.yml (encrypted)
│   ├── staging/
│   │   ├── inventory.yml
│   │   └── group_vars/
│   └── prod/
│       ├── inventory.yml
│       └── group_vars/
```

Deploy to specific environment:
```bash
ansible-playbook -i inventories/prod/inventory.yml playbook.yml --ask-vault-pass
```

## Troubleshooting

### Forgot Vault Password

Unfortunately, if you lose the vault password, the encrypted file cannot be recovered. Always:
- Store vault password securely (password manager)
- Keep a backup of unencrypted secrets in a secure location
- Document the recovery process

### Vault Decryption Failed

```bash
# Wrong password
ERROR! Decryption failed

# Fix: Use correct password or
ansible-vault rekey group_vars/secrets.yml  # Change password
```

### Check What's Encrypted

```bash
# View encrypted file content
ansible-vault view group_vars/secrets.yml

# Test vault password
ansible-vault view group_vars/secrets.yml --vault-password-file .vault_pass
```

## Example: Complete Setup

```bash
cd ansible

# 1. Copy example files
cp inventory.yml.example inventory.yml
cp group_vars/all.yml.example group_vars/all.yml

# 2. Edit non-sensitive config
nano inventory.yml
nano group_vars/all.yml

# 3. Create vault password
openssl rand -base64 32 > .vault_pass
chmod 600 .vault_pass

# 4. Generate secrets
API_KEY1=$(openssl rand -base64 32)
API_KEY2=$(openssl rand -base64 32)
API_KEY3=$(openssl rand -base64 32)
SECRET_KEY=$(openssl rand -hex 32)

# 5. Create encrypted secrets file
ansible-vault create group_vars/secrets.yml --vault-password-file .vault_pass

# In the editor, add:
cat > /tmp/secrets.yml <<EOF
---
api_keys: "$API_KEY1,$API_KEY2,$API_KEY3"
secret_key: "$SECRET_KEY"
saml_idp_cert: |
  $(cat /path/to/idp-cert.pem)
EOF

# 6. Deploy
ansible-playbook -i inventory.yml playbook.yml --vault-password-file .vault_pass

# 7. Store .vault_pass securely (password manager, encrypted backup)
```

## Quick Reference

```bash
# Create encrypted file
ansible-vault create group_vars/secrets.yml

# Edit encrypted file
ansible-vault edit group_vars/secrets.yml

# View encrypted file
ansible-vault view group_vars/secrets.yml

# Encrypt existing file
ansible-vault encrypt group_vars/all.yml

# Decrypt file (temporarily)
ansible-vault decrypt group_vars/secrets.yml
# (edit as plain text)
ansible-vault encrypt group_vars/secrets.yml

# Change vault password
ansible-vault rekey group_vars/secrets.yml

# Run playbook with vault
ansible-playbook playbook.yml --ask-vault-pass
ansible-playbook playbook.yml --vault-password-file .vault_pass
```

## Summary

**Recommended approach:**
1. Use `ansible-vault` to encrypt `group_vars/secrets.yml`
2. Store vault password in `.vault_pass` (gitignored)
3. Keep non-sensitive config in `group_vars/all.yml` (also gitignored but less critical)
4. Keep example files for reference
5. Never commit actual secrets or vault passwords

This gives you the best balance of security and usability!
