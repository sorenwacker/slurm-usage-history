# SAML Certificates

This directory should contain the SAML certificates that Ansible will deploy to the server.

## Required Files

Place your SAML Service Provider certificates here:

- `sp.crt` - Service Provider certificate (public key)
- `sp.key` - Service Provider private key

## Security Warning

**IMPORTANT:** These files contain sensitive cryptographic keys and are automatically ignored by git. NEVER commit these files to version control.

## Copying Certificates from Old Deployment

### Option 1: Copy from daic-dash server

If you have existing certificates on daic-dash, copy them to this location:

```bash
# From your local machine
scp sdrwacker@daic-dash:/home/sdrwacker/workspace/slurm-usage-history/saml/certs/sp.crt ansible/files/saml/certs/
scp sdrwacker@daic-dash:/home/sdrwacker/workspace/slurm-usage-history/saml/certs/sp.key ansible/files/saml/certs/

# Or if they're in a different location:
scp sdrwacker@daic-dash:/home/sdrwacker/workspace/slurm-usage-history/backend/saml/certs/sp.crt ansible/files/saml/certs/
scp sdrwacker@daic-dash:/home/sdrwacker/workspace/slurm-usage-history/backend/saml/certs/sp.key ansible/files/saml/certs/
```

### Option 2: Generate new certificates

If you want to generate new certificates (requires updating IdP metadata afterward):

```bash
# Generate new self-signed certificate (valid for 10 years)
openssl req -new -x509 -days 3650 -nodes \
  -out ansible/files/saml/certs/sp.crt \
  -keyout ansible/files/saml/certs/sp.key \
  -subj "/CN=your-domain.edu/O=Your Organization/C=US"

# Set proper permissions
chmod 600 ansible/files/saml/certs/sp.key
chmod 644 ansible/files/saml/certs/sp.crt
```

**Note:** If you generate new certificates, you MUST update your Identity Provider with the new SP metadata.

## How Ansible Uses These Certificates

When you run the Ansible playbook:

1. Ansible checks if these files exist in `ansible/files/saml/certs/`
2. If found, they are copied to the target server at:
   - `/opt/slurm-usage-history/backend/saml/certs/sp.crt`
   - `/opt/slurm-usage-history/backend/saml/certs/sp.key`
3. Proper permissions are set (600 for .key, 644 for .crt)
4. Files are owned by the service user (slurmusage)

If certificates are not found, Ansible will generate new ones automatically, but you'll need to update your IdP configuration.

## Verification

After deployment, verify the certificates on the server:

```bash
# SSH to the server
ssh sdrwacker@daic-dash

# Check certificates exist and have correct permissions
ls -la /opt/slurm-usage-history/backend/saml/certs/

# View certificate details
openssl x509 -in /opt/slurm-usage-history/backend/saml/certs/sp.crt -text -noout

# Verify private key matches certificate
openssl x509 -noout -modulus -in /opt/slurm-usage-history/backend/saml/certs/sp.crt | openssl md5
openssl rsa -noout -modulus -in /opt/slurm-usage-history/backend/saml/certs/sp.key | openssl md5
# The MD5 hashes should match
```

## Backup

Always backup your certificates before migration:

```bash
# On daic-dash server
mkdir -p ~/migration-backups/$(date +%Y%m%d)/saml-certs
cp -r /home/sdrwacker/workspace/slurm-usage-history/saml/certs/* \
  ~/migration-backups/$(date +%Y%m%d)/saml-certs/
```
