# Admin Setup Guide - Quick Start

Complete guide to set up the admin interface and start managing clusters.

## Prerequisites

- Backend running
- Frontend running
- Python 3.8+
- Node.js 18+

## Step 1: Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
```

New dependencies added:
- `python-jose[cryptography]` - JWT token handling
- `passlib[bcrypt]` - Password hashing

## Step 2: Create Admin User

```bash
cd backend
python3 create_admin.py
```

Example session:
```
==========================================
SLURM Usage History - Admin User Creation
==========================================

Enter admin username: admin
Enter admin password: ********
Confirm password: ********

==========================================
Admin User Created Successfully!
==========================================

Add the following to your backend/.env file:

ADMIN_USERS=admin:$2b$12$N9qo8uLOickgQ2ZWhWZgk.Bvdvs9bTv7/hFr8Pvm2Hqa8YqBgK0.2
ADMIN_SECRET_KEY=xK9mP4vL2nQ8rW6hS1jF7dC3gT5yU0zA9bN2xM4kL8pR6vH3fJ1yT4
```

## Step 3: Update .env File

```bash
nano backend/.env
```

Add the generated lines:

```bash
# Admin Authentication
ADMIN_USERS=admin:$2b$12$N9qo8uLOickgQ2ZWhWZgk.Bvdvs9bTv7/hFr8Pvm2Hqa8YqBgK0.2
ADMIN_SECRET_KEY=xK9mP4vL2nQ8rW6hS1jF7dC3gT5yU0zA9bN2xM4kL8pR6vH3fJ1yT4

# Existing settings
API_KEYS=  # Now optional - use admin interface instead!
DATA_PATH=../data
AUTO_REFRESH_INTERVAL=600
CORS_ORIGINS=http://localhost:3100
```

## Step 4: Restart Backend

```bash
cd backend
uvicorn app.main:app --reload --port 8100
```

Verify admin endpoints are available:
```bash
curl http://localhost:8100/docs
# Look for "Admin" tag in Swagger UI
```

## Step 5: Install Frontend Dependencies

```bash
cd frontend
npm install
```

This installs `react-router-dom` for admin routing.

## Step 6: Start Frontend

```bash
npm run dev
```

Open browser: `http://localhost:3100`

## Step 7: Access Admin Interface

### Option A: Via Dashboard

1. Open `http://localhost:3100`
2. Click **"Admin"** button in top-right header
3. Login with credentials

### Option B: Direct URL

1. Go to `http://localhost:3100/admin/login`
2. Enter username and password
3. Click "Sign in"

## Step 8: Create Your First Cluster

After logging in:

1. Click **"+ Add Cluster"** button
2. Fill in the form:
   - **Cluster Name** (required): `hpc-cluster-01`
   - **Description** (optional): `Main HPC cluster`
   - **Contact Email** (optional): `admin@example.com`
   - **Location** (optional): `Building A`
3. Click **"Create Cluster"**
4. **IMPORTANT**: A modal will appear with the generated API key
5. **Copy the API key** - this is the only time it's shown in full!
6. Click **"Copy to Clipboard"**

Example API key:
```
xK9mP4vL2nQ8rW6hS1jF7dC3gT5yU0zA9bN2xM4kL8pR6vH3
```

## Step 9: Configure Cluster Agent

On your SLURM cluster:

```bash
# Create or edit config
sudo nano /etc/slurm-usage-history-exporter/config.json
```

```json
{
  "api_url": "http://localhost:8100",
  "api_key": "xK9mP4vL2nQ8rW6hS1jF7dC3gT5yU0zA9bN2xM4kL8pR6vH3"
}
```

## Step 10: Test Data Submission

```bash
# Test from cluster
slurm-usage-history-exporter --dry-run --verbose

# Submit real data
slurm-usage-history-exporter
```

## Step 11: Verify in Admin Interface

Back in the admin interface (`http://localhost:3100/admin/clusters`):

You should see:
- **Status**: Active (green badge)
- **Statistics**: Updated job count
- **Last submission**: Recent timestamp

## Features Overview

### Cluster List

View all clusters with:
- Name, description, contact
- Active/Inactive status
- Total jobs submitted
- Last submission time
- API key (partial, with copy button)

### Actions Available

For each cluster:
- **Activate/Deactivate** - Enable or disable cluster
- **Rotate Key** - Generate new API key (old one is invalidated)
- **Delete** - Remove cluster (confirmation required)

### Create Cluster

Generates:
- Unique cluster ID (UUID)
- Secure API key (32+ characters)
- Timestamp tracking

## Security Features

✅ **Password Protection**
- Bcrypt hashing (cannot be reversed)
- Passwords never stored in plain text

✅ **Session Management**
- JWT tokens with 24-hour expiration
- Auto-redirect on expiration

✅ **API Key Security**
- Cryptographically secure random generation
- One-time display of full key
- Instant rotation capability

## Common Tasks

### Add Multiple Admins

Run `create_admin.py` for each user:

```bash
python3 create_admin.py  # Admin 1
python3 create_admin.py  # Admin 2
```

Then combine in `.env`:
```bash
ADMIN_USERS=admin1:$hash1,admin2:$hash2
```

### Rotate Compromised API Key

1. Go to admin clusters page
2. Find the cluster
3. Click **"Rotate Key"**
4. Confirm the action
5. Copy new API key from modal
6. Update cluster configuration immediately

### Disable Cluster Temporarily

1. Find cluster in list
2. Click **"Deactivate"**
3. Status changes to "Inactive" (red badge)
4. API key stops working immediately
5. Click **"Activate"** to re-enable

## Troubleshooting

### Cannot Login

**Check:**
```bash
# Verify admin user in .env
cat backend/.env | grep ADMIN_USERS

# Restart backend
pkill -f uvicorn
uvicorn app.main:app --reload --port 8100
```

### "Not authenticated" Error

Your token expired (24 hours). Just login again.

### Frontend Shows Login Page in Loop

Check browser console (F12) for errors. Ensure:
- Backend is running
- CORS is configured correctly
- API URL is correct

### API Key Not Working

**Debug:**
1. Check cluster is **Active** in admin interface
2. Verify API key copied correctly (no spaces)
3. Test with curl:
   ```bash
   curl -X POST http://localhost:8100/api/data/ingest \
     -H "X-API-Key: YOUR-KEY" \
     -H "Content-Type: application/json" \
     -d '{"hostname":"test","jobs":[]}'
   ```

## Production Deployment

### Backend

1. **Use strong passwords** for admin accounts
2. **Change ADMIN_SECRET_KEY** to a random value
3. **Use HTTPS** for API URL
4. **Restrict CORS_ORIGINS** to production domain
5. **Backup** `data/clusters.json` regularly

### Frontend

1. **Set API URL** via environment variable:
   ```bash
   VITE_API_URL=https://your-production-api.com npm run build
   ```
2. **Deploy** built files from `dist/` directory
3. **Configure** web server for SPA routing

### Security Checklist

- [ ] Strong admin passwords (12+ characters)
- [ ] Unique ADMIN_SECRET_KEY generated
- [ ] HTTPS enabled for backend
- [ ] CORS restricted to production domain
- [ ] Firewall rules configured
- [ ] Regular backups of clusters.json
- [ ] API keys rotated quarterly

## Quick Reference

### URLs

- **Dashboard**: `http://localhost:3100`
- **Admin Login**: `http://localhost:3100/admin/login`
- **Admin Panel**: `http://localhost:3100/admin/clusters`
- **API Docs**: `http://localhost:8100/docs`

### Files

- **Admin user script**: `backend/create_admin.py`
- **Backend config**: `backend/.env`
- **Cluster database**: `data/clusters.json`
- **Frontend routes**: `frontend/src/App.tsx`

### Commands

```bash
# Create admin
cd backend && python3 create_admin.py

# Start backend
cd backend && uvicorn app.main:app --reload --port 8100

# Start frontend
cd frontend && npm run dev

# Test API
curl http://localhost:8100/api/admin/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"your-pass"}'
```

## Next Steps

1. ✅ Set up admin account
2. ✅ Create first cluster
3. ✅ Configure cluster agent
4. ✅ Test data submission
5. 📝 Add more clusters as needed
6. 🔄 Set up periodic API key rotation
7. 📊 Monitor cluster statistics

## Support

For issues:
1. Check browser console (F12)
2. Check backend logs
3. Review `ADMIN_GUIDE.md` for detailed API reference
4. Check `SECURITY.md` for security best practices

---

**You're all set!** You now have a complete admin interface for managing clusters and API keys without editing configuration files manually. 🎉
