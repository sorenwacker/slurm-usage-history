# Admin Guide - Cluster Management

This guide explains how to use the new admin interface to manage clusters and API keys.

## Overview

The admin system allows you to:
- ✅ Create new clusters from a web interface
- ✅ Auto-generate secure API keys for each cluster
- ✅ View cluster statistics (submissions, job counts)
- ✅ Rotate API keys when needed
- ✅ Enable/disable clusters
- ✅ Track which clusters are active

## Setup

### Step 1: Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

New dependencies added:
- `python-jose[cryptography]` - JWT token generation
- `passlib[bcrypt]` - Password hashing
- `python-multipart` - Form data handling

### Step 2: Create Admin User

Run the admin creation script:

```bash
cd backend
python3 create_admin.py
```

You'll be prompted for:
- Username
- Password (hidden input)
- Password confirmation

The script will output something like:

```
Add the following to your backend/.env file:

ADMIN_USERS=admin:$2b$12$xK9mP4vL2nQ8rW6hS1jF7.dC3gT5yU0zA9bN2xM4kL8pR6vH3
ADMIN_SECRET_KEY=xK9mP4vL2nQ8rW6hS1jF7dC3gT5yU0zA9bN2xM4kL8pR6vH3
```

### Step 3: Update .env File

Add the generated lines to `backend/.env`:

```bash
# Admin authentication
ADMIN_USERS=admin:$2b$12$xK9mP4vL2nQ8rW6hS1jF7.dC3gT5yU0zA9bN2xM4kL8pR6vH3
ADMIN_SECRET_KEY=xK9mP4vL2nQ8rW6hS1jF7dC3gT5yU0zA9bN2xM4kL8pR6vH3

# Existing settings
API_KEYS=  # Can be empty now - use cluster management instead
DATA_PATH=../data
AUTO_REFRESH_INTERVAL=600
CORS_ORIGINS=http://localhost:3100
```

### Step 4: Restart Backend

```bash
# Restart to load new configuration
uvicorn app.main:app --reload --port 8100
```

## Using the Admin API

### Authentication

All admin endpoints require JWT token authentication.

#### 1. Login

```bash
curl -X POST http://localhost:8100/api/admin/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "your-password"
  }'
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

Save the `access_token` - you'll need it for all other admin requests.

#### 2. Use Token in Requests

Include the token in the `Authorization` header:

```bash
TOKEN="your-access-token-here"

curl http://localhost:8100/api/admin/clusters \
  -H "Authorization: Bearer $TOKEN"
```

### Cluster Management

#### Create a New Cluster

```bash
curl -X POST http://localhost:8100/api/admin/clusters \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "hpc-cluster-01",
    "description": "Main HPC cluster for physics dept",
    "contact_email": "admin@physics.university.edu",
    "location": "Building A, Room 101"
  }'
```

Response:
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "name": "hpc-cluster-01",
  "description": "Main HPC cluster for physics dept",
  "contact_email": "admin@physics.university.edu",
  "location": "Building A, Room 101",
  "api_key": "xK9mP4vL2nQ8rW6hS1jF7dC3gT5yU0zA9bN2xM4kL8pR6vH3",
  "api_key_created": "2024-10-31T15:30:00",
  "active": true,
  "created_at": "2024-10-31T15:30:00",
  "updated_at": "2024-10-31T15:30:00",
  "last_submission": null,
  "total_jobs_submitted": 0
}
```

**IMPORTANT:** Copy the `api_key` - this is the only time it will be shown in full. You'll configure the cluster agent with this key.

#### List All Clusters

```bash
curl http://localhost:8100/api/admin/clusters \
  -H "Authorization: Bearer $TOKEN"
```

Response:
```json
{
  "clusters": [
    {
      "id": "...",
      "name": "hpc-cluster-01",
      "description": "...",
      "api_key": "xK9mP4vL...",
      "last_submission": "2024-10-31T14:22:15",
      "total_jobs_submitted": 15234,
      ...
    },
    {
      "id": "...",
      "name": "gpu-cluster-02",
      ...
    }
  ],
  "total": 2
}
```

#### Get Single Cluster

```bash
curl http://localhost:8100/api/admin/clusters/a1b2c3d4-e5f6-7890-abcd-ef1234567890 \
  -H "Authorization: Bearer $TOKEN"
```

#### Update Cluster

```bash
curl -X PATCH http://localhost:8100/api/admin/clusters/CLUSTER_ID \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Updated description",
    "contact_email": "new-admin@university.edu",
    "active": false
  }'
```

#### Delete Cluster

```bash
curl -X DELETE http://localhost:8100/api/admin/clusters/CLUSTER_ID \
  -H "Authorization: Bearer $TOKEN"
```

⚠️ **Warning:** This will permanently delete the cluster configuration (but not the data files).

#### Rotate API Key

If an API key is compromised or you need to rotate it:

```bash
curl -X POST http://localhost:8100/api/admin/clusters/rotate-key \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "cluster_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
  }'
```

Response:
```json
{
  "cluster_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "new_api_key": "newKey123...",
  "message": "API key rotated successfully. Update cluster configuration with new key."
}
```

**IMPORTANT:** The old API key is immediately invalidated. Update the cluster agent configuration with the new key.

## Complete Workflow: Adding a New Cluster

### 1. Create Cluster in Admin Interface

```bash
# Login
TOKEN=$(curl -X POST http://localhost:8100/api/admin/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"your-password"}' \
  | jq -r '.access_token')

# Create cluster
CLUSTER=$(curl -X POST http://localhost:8100/api/admin/clusters \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "new-cluster",
    "description": "New HPC cluster",
    "contact_email": "admin@example.com"
  }')

# Extract API key
API_KEY=$(echo $CLUSTER | jq -r '.api_key')

echo "Cluster created!"
echo "API Key: $API_KEY"
```

### 2. Configure Cluster Agent

On the cluster, create/update the configuration:

```bash
# On the cluster
sudo nano /etc/slurm-usage-history-exporter/config.json
```

Set:
```json
{
  "api_url": "https://dashboard.example.com",
  "api_key": "YOUR-API-KEY-FROM-STEP-1",
  "cluster_name": "new-cluster"
}
```

### 3. Test Submission

```bash
# On the cluster
sudo slurm-usage-history-exporter --dry-run --verbose
```

If successful:
```bash
sudo slurm-usage-history-exporter
```

### 4. Verify in Admin Interface

```bash
# Check cluster stats
curl http://localhost:8100/api/admin/clusters \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.clusters[] | select(.name=="new-cluster") | {name, total_jobs_submitted, last_submission}'
```

You should see:
- `total_jobs_submitted` > 0
- `last_submission` with recent timestamp

## Data Storage

Cluster information is stored in:
- **Location:** `data/clusters.json`
- **Format:** JSON
- **Backup:** Recommended to backup this file regularly

Example structure:
```json
{
  "clusters": {
    "cluster-id-1": {
      "id": "cluster-id-1",
      "name": "hpc-cluster-01",
      "api_key": "...",
      "created_at": "...",
      ...
    }
  },
  "stats": {
    "cluster-id-1": {
      "last_submission": "2024-10-31T14:22:15",
      "total_jobs_submitted": 15234
    }
  }
}
```

## Security Considerations

### Admin Password

- ✅ Passwords are hashed with bcrypt
- ✅ Original passwords are never stored
- ✅ Password hashes cannot be reversed
- ⚠️ Use strong passwords (12+ characters)

### JWT Tokens

- ✅ Tokens expire after 24 hours
- ✅ Tokens are signed with secret key
- ✅ Tokens cannot be modified without secret
- ⚠️ Keep `ADMIN_SECRET_KEY` secure
- ⚠️ Change secret key if compromised

### API Keys

- ✅ Generated with cryptographically secure random
- ✅ 32+ character length
- ✅ Per-cluster isolation
- ✅ Can be rotated instantly
- ⚠️ Treat like passwords - keep secure
- ⚠️ Rotate periodically

### Best Practices

1. **Access Control**
   - Only give admin credentials to trusted personnel
   - Use unique passwords for each admin
   - Don't share admin credentials

2. **API Key Management**
   - Rotate keys quarterly
   - Rotate immediately if compromised
   - Document which key belongs to which cluster

3. **Monitoring**
   - Monitor admin login attempts
   - Track API key usage
   - Alert on unusual activity

4. **Backups**
   - Backup `data/clusters.json` regularly
   - Keep backups secure
   - Test restore procedures

## Migration from Legacy API Keys

If you have existing clusters using API keys from `.env`:

### Option 1: Create Cluster Entries

For each existing cluster, create an entry:

```bash
# For each cluster
curl -X POST http://localhost:8100/api/admin/clusters \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "existing-cluster-name",
    "description": "Migrated from legacy system"
  }'

# Get the generated API key and update cluster configuration
```

### Option 2: Keep Legacy Keys

The system supports both:
- Managed clusters (in database) - **Recommended**
- Legacy API keys (in `.env`) - For backward compatibility

**Recommended:** Migrate all clusters to managed system for better tracking and management.

## Troubleshooting

### Cannot Login

**Check:**
1. Admin user configured in `.env`
2. Password hash format correct
3. Backend restarted after `.env` changes

**Test:**
```bash
# Check if admin endpoint responds
curl http://localhost:8100/api/admin/login

# Should return 422 (validation error), not 404
```

### Token Expired

**Solution:** Login again to get a new token

```bash
# Tokens expire after 24 hours
curl -X POST http://localhost:8100/api/admin/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"your-password"}'
```

### Cluster Name Already Exists

**Error:** `{"detail": "Cluster with name 'xxx' already exists"}`

**Solution:**
- Choose a different name
- Or delete the existing cluster first
- Or update the existing cluster instead

### API Key Not Working

**Check:**
1. Cluster is active (`"active": true`)
2. API key copied correctly (no spaces/newlines)
3. Cluster name matches hostname in submission

**Debug:**
```bash
# List all clusters and their status
curl http://localhost:8100/api/admin/clusters \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.clusters[] | {name, active, api_key}'
```

## Advanced Usage

### Multiple Admins

To create multiple admin users:

```bash
# Run create_admin.py for each user
python3 create_admin.py  # User 1
python3 create_admin.py  # User 2
```

Then combine in `.env`:
```bash
ADMIN_USERS=admin1:$2b$12$hash1,admin2:$2b$12$hash2,admin3:$2b$12$hash3
```

### Automated Cluster Creation

You can automate cluster creation with scripts:

```bash
#!/bin/bash
# create_cluster.sh

TOKEN=$(curl -s -X POST http://localhost:8100/api/admin/login \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"admin\",\"password\":\"$ADMIN_PASSWORD\"}" \
  | jq -r '.access_token')

CLUSTER_NAME=$1
DESCRIPTION=$2

curl -X POST http://localhost:8100/api/admin/clusters \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"$CLUSTER_NAME\",
    \"description\": \"$DESCRIPTION\"
  }" | jq .
```

Usage:
```bash
./create_cluster.sh "new-cluster" "Auto-created cluster"
```

### Monitoring Script

Monitor all clusters:

```bash
#!/bin/bash
# monitor_clusters.sh

TOKEN=$(curl -s -X POST http://localhost:8100/api/admin/login \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"admin\",\"password\":\"$ADMIN_PASSWORD\"}" \
  | jq -r '.access_token')

curl -s http://localhost:8100/api/admin/clusters \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.clusters[] | {
      name,
      active,
      last_submission,
      total_jobs: .total_jobs_submitted
    }'
```

## API Reference

Complete API documentation available at:
- **Swagger UI:** http://localhost:8100/docs
- **ReDoc:** http://localhost:8100/redoc

Filter by "Admin" tag to see all admin endpoints.

## Summary

The admin system provides:
- ✅ **Easy cluster management** - No manual `.env` editing
- ✅ **Secure API keys** - Auto-generated, per-cluster
- ✅ **Usage tracking** - See submission stats
- ✅ **Quick rotation** - Invalidate compromised keys instantly
- ✅ **Audit trail** - Track when clusters were created/modified
- ✅ **Web UI ready** - API designed for frontend integration

**Next Steps:**
1. Create admin user with `create_admin.py`
2. Add credentials to `.env`
3. Restart backend
4. Login and create your first cluster
5. Configure cluster agent with generated API key
6. Monitor submissions in admin interface

For frontend integration, see the API endpoints at `/docs`.
