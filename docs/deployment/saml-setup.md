# SAML Authentication Setup

This guide covers setting up SAML authentication for the SLURM Usage History Dashboard in production environments.

## Overview

The dashboard supports SAML 2.0 single sign-on (SSO) authentication, allowing integration with institutional identity providers like Shibboleth, SimpleSAMLphp, Okta, Azure AD, and others.

## Security Requirements

!!! danger "Production Security"
    SAML authentication in production environments has strict security requirements that are enforced by the application:

    - **HTTPS is mandatory** - HTTP connections will be rejected
    - **Secure cookies** - Session cookies use `SameSite=Lax` and `Secure` flags
    - **Environment variable required** - `ENVIRONMENT=production` must be set

## Environment Configuration

The application uses the `ENVIRONMENT` variable to determine security settings:

| Environment | HTTPS Required | Cookie Settings | Use Case |
|-------------|---------------|-----------------|----------|
| `production` | ✅ Yes | `SameSite=Lax`, `Secure=True` | Production deployments |
| `development` | ❌ No | `SameSite=None`, `Secure=False` | Local development |
| `staging` | ⚠️ Recommended | Follows production rules | Pre-production testing |

### Production Environment Variables

```bash
ENVIRONMENT=production
ENABLE_SAML=true
SAML_SETTINGS_PATH=/path/to/saml/settings.json
SECRET_KEY=<strong-random-secret-key>
```

## HTTPS Setup

### Nginx Configuration

Create an Nginx configuration for the dashboard with TLS:

```nginx
server {
    listen 443 ssl http2;
    server_name dashboard.example.com;

    ssl_certificate /etc/ssl/certs/dashboard.example.com.crt;
    ssl_certificate_key /etc/ssl/private/dashboard.example.com.key;

    # Modern SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers off;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;

    location / {
        proxy_pass http://localhost:8100;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name dashboard.example.com;
    return 301 https://$server_name$request_uri;
}
```

### Caddy Configuration

Alternatively, use Caddy which handles TLS automatically:

```caddyfile
dashboard.example.com {
    reverse_proxy localhost:8100

    header {
        Strict-Transport-Security "max-age=31536000; includeSubDomains"
        X-Frame-Options "SAMEORIGIN"
        X-Content-Type-Options "nosniff"
    }
}
```

## SAML Configuration

### IdP Metadata

Obtain your Identity Provider's metadata:

1. **Shibboleth**: Usually at `https://idp.example.com/idp/shibboleth`
2. **SimpleSAMLphp**: At `https://idp.example.com/simplesaml/saml2/idp/metadata.php`
3. **Azure AD**: Download from Azure portal
4. **Okta**: Available in the Okta admin console

### Service Provider Settings

Create `saml/settings.json` with your configuration:

```json
{
  "strict": true,
  "debug": false,
  "sp": {
    "entityId": "https://dashboard.example.com/saml/metadata",
    "assertionConsumerService": {
      "url": "https://dashboard.example.com/saml/acs",
      "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
    },
    "singleLogoutService": {
      "url": "https://dashboard.example.com/saml/sls",
      "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
    },
    "NameIDFormat": "urn:oasis:names:tc:SAML:1.1:nameid-format:unspecified"
  },
  "idp": {
    "entityId": "https://idp.example.com/idp/shibboleth",
    "singleSignOnService": {
      "url": "https://idp.example.com/idp/profile/SAML2/Redirect/SSO",
      "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
    },
    "singleLogoutService": {
      "url": "https://idp.example.com/idp/profile/SAML2/Redirect/SLO",
      "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
    },
    "x509cert": "MII... (base64 encoded certificate)"
  },
  "security": {
    "nameIdEncrypted": false,
    "authnRequestsSigned": false,
    "logoutRequestSigned": false,
    "logoutResponseSigned": false,
    "signMetadata": false,
    "wantMessagesSigned": false,
    "wantAssertionsSigned": true,
    "wantAssertionsEncrypted": false,
    "wantNameIdEncrypted": false,
    "requestedAuthnContext": true
  }
}
```

### Attribute Mapping

The dashboard expects these SAML attributes:

| Attribute | Description | Required |
|-----------|-------------|----------|
| `uid` or `username` | User identifier | ✅ Yes |
| `email` | User email address | ⚠️ Recommended |
| `displayName` | Full name | ⚠️ Recommended |
| `netid` | Institution ID (for admin checks) | For admin features |

Configure your IdP to release these attributes to the Service Provider.

## Admin User Configuration

Set admin users via environment variables:

```bash
# Method 1: Email-based (for SAML users)
ADMIN_EMAILS=admin@example.com:superadmin,user@example.com:admin

# Method 2: Email list (all get admin role)
SUPERADMIN_EMAILS=admin1@example.com,admin2@example.com
```

## Register with Identity Provider

Register your Service Provider with the IdP:

1. **Provide SP metadata**: Access `https://dashboard.example.com/saml/metadata`
2. **Configure attribute release**: Ensure required attributes are sent
3. **Test authentication**: Try logging in before going live

## Testing

### Pre-Production Checklist

- [ ] HTTPS configured and working
- [ ] SAML settings.json configured correctly
- [ ] `ENVIRONMENT=production` set
- [ ] SP registered with IdP
- [ ] Attributes being released
- [ ] Admin users configured
- [ ] Test login successful
- [ ] Test logout working

### Common Errors

#### "SAML authentication requires HTTPS in production environments"

**Cause**: Application is accessed via HTTP with `ENVIRONMENT=production`

**Solution**:
- Configure HTTPS reverse proxy
- Ensure `X-Forwarded-Proto` header is set
- Verify certificate is valid

#### "Signature validation failed"

**Cause**: IdP certificate mismatch in configuration

**Solution**:
- Extract current IdP certificate: `openssl x509 -in idp.crt -noout -fingerprint`
- Update `x509cert` in settings.json
- Remove whitespace and headers from certificate

#### Session not persisting

**Cause**: Cookie not being set or sent

**Solution**:
- Verify HTTPS is used (required for secure cookies)
- Check browser developer tools for cookie
- Ensure `SameSite=Lax` allows your use case

## Security Best Practices

!!! warning "Security Checklist"
    - ✅ Use strong TLS configuration (TLS 1.2+)
    - ✅ Enable HSTS header
    - ✅ Rotate SECRET_KEY regularly
    - ✅ Keep SAML library updated
    - ✅ Monitor authentication logs
    - ✅ Require assertion signatures
    - ✅ Use short session timeouts (24 hours default)
    - ✅ Implement audit logging

## Troubleshooting

Enable debug mode temporarily for troubleshooting:

```bash
# In settings.json
"debug": true
```

Check application logs:

```bash
docker logs slurm-backend
```

Review SAML requests/responses in browser developer tools (Network tab).

## Further Reading

- [SAML 2.0 Specification](https://docs.oasis-open.org/security/saml/v2.0/)
- [python3-saml Documentation](https://github.com/SAML-Toolkits/python3-saml)
- [SAML Security Considerations](https://www.oasis-open.org/committees/download.php/56776/sstc-saml-core-errata-2.0-wd-07.pdf)
