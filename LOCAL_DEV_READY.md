# Local Development Environment - Ready to Use!

Your Docker-based local development environment with SAML authentication is now running.

## Access Points

| Service | URL | Description |
|---------|-----|-------------|
| **Dashboard** | http://localhost:8100 | Main application (will redirect to SAML login) |
| **Frontend Dev** | http://localhost:5173 | Vite dev server with hot reload |
| **SAML IdP** | http://localhost:8080 | SimpleSAMLphp test Identity Provider |
| **API Docs** | http://localhost:8100/docs | Interactive API documentation |
| **SAML Metadata** | http://localhost:8100/saml/metadata | Service Provider SAML metadata |
| **SAML Status** | http://localhost:8100/saml/status | SAML configuration status |

## Test Users

Login at http://localhost:8080/simplesaml when redirected:

| Username | Password | Role | NetID |
|----------|----------|------|-------|
| admin | admin | Admin/Staff | admin |
| user | user | Staff/Member | user |
| testuser | testuser | Student/Member | testuser |

## Quick Commands

```bash
# View logs from all services
docker-compose -f docker-compose.dev.yml logs -f

# View logs from specific service
docker-compose -f docker-compose.dev.yml logs -f backend
docker-compose -f docker-compose.dev.yml logs -f frontend
docker-compose -f docker-compose.dev.yml logs -f saml-idp

# Restart a service
docker-compose -f docker-compose.dev.yml restart backend

# Stop all services
docker-compose -f docker-compose.dev.yml down

# Stop and remove volumes (clean slate)
docker-compose -f docker-compose.dev.yml down -v

# Rebuild a specific service
docker-compose -f docker-compose.dev.yml up --build backend

# Access a container shell
docker-compose -f docker-compose.dev.yml exec backend /bin/bash
docker-compose -f docker-compose.dev.yml exec frontend /bin/sh
docker-compose -f docker-compose.dev.yml exec saml-idp /bin/bash
```

## Testing SAML Login Flow

1. **Visit Dashboard**: http://localhost:8100
2. **Automatic Redirect**: You'll be redirected to SimpleSAMLphp login
3. **Login**: Use credentials above (e.g., admin/admin)
4. **Return to Dashboard**: After successful auth, you'll be redirected back
5. **Check Session**: Visit http://localhost:8100/saml/me to see your user info

## Development Workflow

### Backend Development
- Edit files in `backend/` directory
- Changes auto-reload (uvicorn --reload is enabled)
- Check logs: `docker-compose -f docker-compose.dev.yml logs -f backend`

### Frontend Development
- Edit files in `frontend/` directory
- Vite dev server hot reloads automatically
- Access at: http://localhost:5173

### SAML Configuration
- Edit: `docker/saml-config/settings.json`
- Restart backend: `docker-compose -f docker-compose.dev.yml restart backend`

### Adding Test Users
- Edit: `docker/saml-idp/authsources.php`
- Restart IdP: `docker-compose -f docker-compose.dev.yml restart saml-idp`

## Container Status

Check running containers:
```bash
docker-compose -f docker-compose.dev.yml ps
```

Expected output:
```
NAME                 STATUS              PORTS
slurm-backend-dev    Up X minutes        0.0.0.0:8100->8100/tcp
slurm-frontend-dev   Up X minutes        0.0.0.0:5173->3100/tcp
slurm-saml-idp       Up X minutes        0.0.0.0:8080->8080/tcp
```

## Troubleshooting

### Backend Issues
```bash
# Check logs
docker-compose -f docker-compose.dev.yml logs backend

# Restart
docker-compose -f docker-compose.dev.yml restart backend

# Rebuild
docker-compose -f docker-compose.dev.yml up --build -d backend
```

### SAML Login Not Working
```bash
# Check SAML status
curl http://localhost:8100/saml/status

# Check IdP is accessible from backend
docker-compose -f docker-compose.dev.yml exec backend curl -v http://saml-idp:8080

# View backend logs for SAML errors
docker-compose -f docker-compose.dev.yml logs backend | grep -i saml
```

### Frontend Not Loading
```bash
# Check frontend logs
docker-compose -f docker-compose.dev.yml logs frontend

# Restart frontend
docker-compose -f docker-compose.dev.yml restart frontend
```

### Port Conflicts
If ports are already in use, edit `docker-compose.dev.yml`:
```yaml
ports:
  - "9100:8100"  # Change first number to any free port
```

## Current Status

✅ All services running
✅ SAML authentication enabled
✅ Backend API accessible
✅ Frontend dev server running
✅ SAML IdP configured with test users
✅ Hot reload enabled for development

## Next Steps

1. Open http://localhost:8100 in your browser
2. You'll be redirected to SAML login
3. Log in with admin/admin
4. Start developing!

## Additional Resources

- Full documentation: [DEVELOPMENT.md](DEVELOPMENT.md)
- API documentation: http://localhost:8100/docs
- SimpleSAMLphp docs: https://simplesamlphp.org/docs/stable/
