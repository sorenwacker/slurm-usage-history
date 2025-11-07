# Ansible Host Variables

This directory contains host-specific configuration variables for Ansible deployment.

## Setup Instructions

1. **Copy the example template:**
   ```bash
   cp ansible/host_vars/example.yml ansible/host_vars/<your-hostname>.yml
   ```

2. **Update the configuration:**
   - Edit `<your-hostname>.yml` with your actual values
   - Replace all placeholder values (those containing "your-domain", "TO_BE_EXTRACTED", etc.)
   - Fill in your SAML IdP configuration
   - Update SSL certificate paths
   - Set the correct domain name

3. **Your actual host file is automatically ignored by git:**
   - The `.gitignore` file is configured to ignore all `.yml` files in this directory except `example.yml`
   - This prevents accidentally committing sensitive configuration to the repository

4. **Update your inventory:**
   - Edit `ansible/hosts` to include your hostname
   - Ensure the hostname matches the filename (without `.yml` extension)

## Security Notes

- **Never commit sensitive configuration files to version control**
- Keep your SAML certificates secure
- Generate strong JWT secret keys
- Store backups of your configuration in a secure location
- Use environment-specific files for different deployments (dev, staging, production)

## Example

If your server is named `daic-dash`:

1. Create: `ansible/host_vars/daic-dash.yml`
2. Add to inventory: `daic-dash` in `ansible/hosts`
3. Run deployment: `ansible-playbook -i hosts playbook.yml`

The variables in `daic-dash.yml` will automatically be applied to the `daic-dash` host.
