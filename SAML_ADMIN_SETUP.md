# SAML2 Admin Authentication Setup Guide

This guide explains how to configure SAML2-based admin authentication with role-based access control.

## Overview

The system supports two admin authentication methods:
1. **Username/Password** - For development and non-SAML environments
2. **SAML2** - For production with SSO integration

Admin users have two role levels:
- **Admin** - Can ONLY access user-specific features (color by user, user analytics, export user data)
- **SuperAdmin** - Full access: cluster management + all user data features

## Configuration

### 1. Environment Variables (.env)

```env
# SAML Configuration
ENABLE_SAML=true
SAML_SETTINGS_PATH=saml/settings.json

# Admin Email Lists with Roles
# SuperAdmins - Full access (cluster management + user data)
SUPERADMIN_EMAILS=alice@example.com,bob@example.com

# Regular Admins - User data access only (no cluster management)
ADMIN_EMAILS=charlie@example.com,david@example.com

# Legacy password-based auth (for development)
ADMIN_USERS=admin:$2b$12$fNM.lMYozgq2mwON0fsJPeJw/SoA/BEX1Xt/M4Yp1sre.qUS/qn2G
ADMIN_SECRET_KEY=your-secret-key-here
```

### 2. Email Configuration Format

**Option 1: Separate lists by role** (Recommended)
```env
# SuperAdmins - Can manage clusters AND access user data
SUPERADMIN_EMAILS=it-admin@tudelft.nl,cluster-admin@tudelft.nl

# Admins - Can ONLY access user data (color by user, analytics, exports)
ADMIN_EMAILS=researcher1@tudelft.nl,researcher2@tudelft.nl
```

**Option 2: Mixed list with role specification**
```env
# All in one list with explicit roles
ADMIN_EMAILS=it-admin@tudelft.nl:superadmin,researcher1@tudelft.nl:admin
```

**Note**:
- `SUPERADMIN_EMAILS` always grants superadmin role (overrides ADMIN_EMAILS)
- SuperAdmins have ALL permissions
- Regular Admins can ONLY view user data, NOT manage clusters

## Frontend Integration

### SAML Login Flow

1. User clicks "Login with SSO" button
2. Frontend redirects to `/api/saml/login`
3. User authenticates with IdP (e.g., TU Delft SSO)
4. SAML ACS endpoint receives assertion
5. Backend checks user's email against admin lists
6. If authorized, creates session with role information
7. User is redirected back to admin interface

### Route Protection by Role

```typescript
// frontend/src/pages/AdminClusters.tsx
// Only SuperAdmins can access cluster management
useEffect(() => {
  if (!user || user.role !== 'superadmin') {
    navigate('/unauthorized');
  }
}, [user]);

// frontend/src/pages/UserAnalytics.tsx
// Both Admin and SuperAdmin can access user data features
useEffect(() => {
  if (!user || (user.role !== 'admin' && user.role !== 'superadmin')) {
    navigate('/unauthorized');
  }
}, [user]);
```

### User Data Features (Admin + SuperAdmin)

Features available to both admin levels:
- **Color by User** - Visualize usage colored by individual users
- **User Analytics** - Detailed per-user statistics
- **Export User Data** - Download user-specific reports

```typescript
// Conditional rendering - available to admin AND superadmin
{(user?.role === 'admin' || user?.role === 'superadmin') && (
  <button onClick={() => enableColorByUser()}>
    Color by User
  </button>
)}
```

### Cluster Management Features (SuperAdmin Only)

Features only available to superadmins:
- **Cluster CRUD** - Create, edit, delete clusters
- **API Key Management** - Rotate and manage cluster API keys
- **System Settings** - Configure dashboard settings

```typescript
// Only superadmins can access cluster management
{user?.role === 'superadmin' && (
  <Link to="/admin/clusters">Manage Clusters</Link>
)}
```

## Backend Implementation

### Role-Based Access Control

```python
# backend/app/core/admin_auth.py
from fastapi import Depends, HTTPException

async def require_any_admin(user: dict = Depends(get_current_admin)):
    """Require any admin role (admin or superadmin)."""
    role = user.get('role')
    if role not in ['admin', 'superadmin']:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

async def require_superadmin(user: dict = Depends(get_current_admin)):
    """Require superadmin role for cluster management."""
    role = user.get('role')
    if role != 'superadmin':
        raise HTTPException(status_code=403, detail="Superadmin access required")
    return user
```

### Protected Endpoints

```python
# SuperAdmin-only endpoints (cluster management)
@router.get("/admin/clusters", dependencies=[Depends(require_superadmin)])
async def list_clusters():
    """Only superadmins can manage clusters."""
    ...

@router.post("/admin/clusters", dependencies=[Depends(require_superadmin)])
async def create_cluster():
    """Only superadmins can create clusters."""
    ...

# Any admin can access (user data features)
@router.get("/dashboard/users", dependencies=[Depends(require_any_admin)])
async def get_user_data():
    """Both admin and superadmin can view user data."""
    ...

@router.get("/dashboard/analytics/by-user", dependencies=[Depends(require_any_admin)])
async def get_user_analytics():
    """Both admin and superadmin can view user analytics."""
    ...
```

## SAML Integration Steps

### 1. Update SAML ACS Endpoint

Modify `backend/app/api/saml.py` to check admin status after authentication:

```python
@router.post("/acs")
async def saml_acs(request: Request):
    # ... existing SAML processing ...

    # Get user email from SAML attributes
    attributes = auth.get_attributes()
    email = attributes.get('email', [nameid])[0] if 'email' in attributes else nameid

    # Check if user is admin
    settings = get_settings()
    if not settings.is_admin_email(email):
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to access the admin panel"
        )

    # Get user's admin role
    role = settings.get_email_role(email)

    # Create user data with role for session
    user_data = {
        "email": email,
        "role": role,
        "username": nameid,
        "attributes": attributes,
    }

    # Create JWT session token
    session_token = create_session_token(user_data)
    ...
```

### 2. Frontend SAML Login

```typescript
// frontend/src/api/adminClient.ts
class AdminClient {
  async loginWithSAML(): Promise<void> {
    // Redirect to SAML login endpoint
    const redirectUrl = encodeURIComponent('/admin/clusters');
    window.location.href = `${API_BASE_URL}/api/saml/login?redirect_to=${redirectUrl}`;
  }

  async checkSAMLSession(): Promise<{email: string; role: string} | null> {
    // Check if user has valid SAML session
    const response = await fetch(`${API_BASE_URL}/api/saml/me`, {
      credentials: 'include'
    });

    if (response.ok) {
      return response.json();
    }
    return null;
  }
}
```

### 3. Add SAML "Me" Endpoint

```python
# backend/app/api/saml.py
@router.get("/me")
async def get_current_user_saml_info(user: dict = Depends(get_current_user_saml)):
    """Get current SAML user information."""
    return {
        "email": user.get("email"),
        "role": user.get("role"),
        "username": user.get("username"),
        "authenticated": True
    }
```

## Testing

### Test Admin Access

```bash
# Check if email is admin
curl http://localhost:8100/api/admin/check-email \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@tudelft.nl"}'

# Expected response:
# {"is_admin": true, "role": "superadmin"}
```

### Test SAML Flow

1. Enable SAML: `ENABLE_SAML=true`
2. Configure admin emails in `.env`
3. Visit `/api/saml/login`
4. Authenticate with IdP
5. Verify session cookie is set
6. Access admin panel

## Deployment Checklist

- [ ] Configure SAML settings in `saml/settings.json`
- [ ] Set `ENABLE_SAML=true` in production `.env`
- [ ] Add production admin emails to `SUPERADMIN_EMAILS` and `ADMIN_EMAILS`
- [ ] Test SAML login flow with both admin and superadmin accounts
- [ ] Verify unauthorized users are rejected
- [ ] Test role-based feature access (e.g., "Color by User" for superadmins only)
- [ ] Update frontend to show SAML login button
- [ ] Hide password login in production

## Example Production Configuration

```env
# Production .env
ENABLE_SAML=true
SAML_SETTINGS_PATH=/etc/slurm-dashboard/saml/settings.json

# SuperAdmins - Full access (cluster management + user data)
SUPERADMIN_EMAILS=admin@tudelft.nl,it-manager@tudelft.nl,cluster-admin@tudelft.nl

# Regular Admins - User data access ONLY (color by user, analytics, exports)
ADMIN_EMAILS=researcher1@tudelft.nl,researcher2@tudelft.nl,analyst@tudelft.nl

# Disable password login in production
ADMIN_USERS=

# JWT secret
ADMIN_SECRET_KEY=<generate-random-key>
```

## Security Considerations

1. **Email Verification**: SAML IdP must return verified email addresses
2. **Role Separation**: Keep superadmin list minimal (principle of least privilege)
3. **Audit Logging**: Log all admin actions with email and role
4. **Session Expiry**: SAML sessions expire after 24 hours
5. **HTTPS Only**: Always use HTTPS in production for SAML
6. **IdP Trust**: Only trust your organization's SAML IdP

## Troubleshooting

**User can't access admin panel after SAML login**
- Check if email is in `ADMIN_EMAILS` or `SUPERADMIN_EMAILS`
- Verify email format matches exactly (case-insensitive)
- Check SAML attributes are correctly mapped

**Role not showing correctly**
- Verify `.env` configuration
- Check precedence: `SUPERADMIN_EMAILS` overrides `ADMIN_EMAILS`
- Restart backend after changing `.env`

**SAML login fails**
- Verify `ENABLE_SAML=true`
- Check `saml/settings.json` configuration
- Verify IdP metadata is current
- Check IdP and SP URLs are accessible

## API Reference

### Check Email Authorization

```
GET /api/admin/check-email
Content-Type: application/json

{
  "email": "user@example.com"
}

Response:
{
  "is_admin": true,
  "role": "admin" | "superadmin"
}
```

### Get Current User

```
GET /api/saml/me
Cookie: session_token=...

Response:
{
  "email": "user@example.com",
  "role": "superadmin",
  "username": "user",
  "authenticated": true
}
```
