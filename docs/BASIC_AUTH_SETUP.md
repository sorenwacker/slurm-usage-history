# HTTP Basic Authentication Setup for Testing

This guide shows how to create the password file for protecting the testing deployment at `/v2-preview/`.

## Quick Setup

### On the daic-dash Server

After Ansible deploys the application, you need to create the `.htpasswd` file:

```bash
# SSH to the server
ssh sdrwacker@daic-dash

# Install apache2-utils (if not already installed)
# On Ubuntu/Debian:
sudo apt-get install apache2-utils

# On RHEL/CentOS:
# sudo yum install httpd-tools

# Create password file for the first user
sudo htpasswd -c /opt/slurm-usage-history/.htpasswd testuser

# You'll be prompted to enter a password
# Enter password:
# Re-type password:

# Add additional users (without -c flag!)
sudo htpasswd /opt/slurm-usage-history/.htpasswd admin
sudo htpasswd /opt/slurm-usage-history/.htpasswd developer

# Set correct permissions
sudo chmod 640 /opt/slurm-usage-history/.htpasswd
sudo chown root:nginx /opt/slurm-usage-history/.htpasswd
# Or if nginx runs as www-data:
# sudo chown root:www-data /opt/slurm-usage-history/.htpasswd

# Reload nginx to apply
sudo nginx -t && sudo systemctl reload nginx
```

## Testing

```bash
# Test with curl (should get 401 Unauthorized)
curl -I https://daic-dash.example.edu/v2-preview/

# Test with credentials (should work)
curl -u testuser:password https://daic-dash.example.edu/v2-preview/
```

In browser:
1. Visit `https://daic-dash.example.edu/v2-preview/`
2. You'll see a login prompt: "Internal Testing - New Dashboard"
3. Enter username and password
4. Dashboard loads

## Managing Users

```bash
# Add a new user
sudo htpasswd /opt/slurm-usage-history/.htpasswd newuser

# Change a user's password
sudo htpasswd /opt/slurm-usage-history/.htpasswd existinguser

# Delete a user
sudo htpasswd -D /opt/slurm-usage-history/.htpasswd username

# List users
sudo cat /opt/slurm-usage-history/.htpasswd | cut -d: -f1
```

## Security Notes

1. **Password file location**: `/opt/slurm-usage-history/.htpasswd`
   - Not in the web root
   - Not accessible via web browser
   - Proper permissions (640)

2. **HTTPS required**: The nginx config requires HTTPS, so credentials are encrypted in transit

3. **Temporary protection**: This is only for Phase 1 testing. Once SAML is enabled in Phase 2, you can remove the basic auth directives from nginx config.

## Removing Basic Auth (Phase 2 - When SAML is Ready)

When you're ready to switch to SAML authentication, just remove these lines from the nginx config:

```nginx
# Remove these lines:
auth_basic "Internal Testing - New Dashboard";
auth_basic_user_file {{ app_base_dir }}/.htpasswd;
```

Then reload nginx:
```bash
sudo nginx -t && sudo systemctl reload nginx
```

## Alternative: Generate Password File Locally

If you want to create the password file on your local machine first:

```bash
# On your local machine
htpasswd -c htpasswd_testing testuser
htpasswd htpasswd_testing admin

# Copy to server
scp htpasswd_testing sdrwacker@daic-dash:/tmp/

# On server
sudo mv /tmp/htpasswd_testing /opt/slurm-usage-history/.htpasswd
sudo chmod 640 /opt/slurm-usage-history/.htpasswd
sudo chown root:nginx /opt/slurm-usage-history/.htpasswd
```

## Password Strength

For production testing, use strong passwords:

```bash
# Generate a strong random password
openssl rand -base64 20

# Or
pwgen 20 1
```

Then use `htpasswd` as shown above.
