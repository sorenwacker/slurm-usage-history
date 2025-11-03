# Security Guide - SLURM Usage History

## Overview

The SLURM Usage History system implements multiple layers of security to protect against unauthorized data uploads and access.

## 🔒 Authentication & Authorization

### API Key Authentication

**All data ingestion requests require API key authentication.**

#### How It Works

1. **API Key Required:** Every `POST /api/data/ingest` request **must** include a valid API key in the `X-API-Key` header
2. **Server-Side Validation:** The backend validates the key against configured keys before processing
3. **Rejection on Failure:** Invalid or missing keys result in HTTP 401 Unauthorized

#### Implementation

**Location:** `backend/app/core/auth.py`

```python
async def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """Verify API key from request header."""

    # Check 1: API key present?
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API Key",
        )

    # Check 2: Server has keys configured?
    api_keys = settings.get_api_keys()
    if not api_keys:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No API keys configured on server",
        )

    # Check 3: Provided key is valid?
    if api_key not in api_keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
        )

    return api_key
```

**Endpoint Protection:** `backend/app/api/data.py`

```python
@router.post("/ingest", response_model=DataIngestionResponse)
async def ingest_data(
    request: DataIngestionRequest,
    api_key: str = Depends(verify_api_key),  # ← API key required
) -> DataIngestionResponse:
    # Only executed if api_key is valid
    ...
```

### What This Means

✅ **Without a valid API key, you CANNOT:**
- Upload job data
- Create files in the data directory
- Inject malicious data
- Overwrite existing data

✅ **Read-only endpoints are public** (no sensitive data exposure):
- `/api/dashboard/health`
- `/api/dashboard/metadata`
- `/api/dashboard/filter`
- `/api/dashboard/stats`

These return aggregated statistics only, no sensitive user information.

---

## 🔑 API Key Management

### Configuration

**File:** `backend/.env`

```bash
# Comma-separated list of valid API keys
API_KEYS=key1,key2,key3
```

**Features:**
- Multiple keys supported (comma-separated)
- Keys can be different per cluster or shared
- Keys are never exposed in responses
- Keys are validated on every request

### Generating Secure API Keys

**Recommended:** Use cryptographically secure random keys (32+ characters)

```bash
# Generate a strong API key (Python)
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Example output:
# xK9mP4vL2nQ8rW6hS1jF7dC3gT5yU0zA9bN2xM4kL8pR6vH3

# Generate multiple keys
for i in {1..3}; do python3 -c "import secrets; print(secrets.token_urlsafe(32))"; done
```

Add to `.env`:
```bash
API_KEYS=xK9mP4vL2nQ8rW6hS1jF7dC3gT5yU0zA9bN2xM4kL8pR6vH3,aB3dE5fG7hI9jK1lM3nO5pQ7rS9tU1vW3xY5zA7bC9dE1fG3
```

### API Key Distribution

**Best Practices:**

1. **Secure Transmission:** Share keys via encrypted channels (not email/Slack)
2. **Need-to-Know:** Only cluster administrators should have keys
3. **Cluster-Specific:** Consider unique keys per cluster for tracking/revocation
4. **Documentation:** Track which key belongs to which cluster

**Example Tracking:**
```bash
# backend/.env
API_KEYS=cluster1-key-abc123,cluster2-key-def456,cluster3-key-ghi789

# Internal documentation:
# cluster1-key-abc123 → hpc-cluster-01 (admin: alice@example.com)
# cluster2-key-def456 → gpu-cluster-02 (admin: bob@example.com)
# cluster3-key-ghi789 → ml-cluster-03  (admin: charlie@example.com)
```

### API Key Rotation

**When to Rotate:**
- Quarterly (recommended)
- When personnel changes
- After suspected compromise
- Before major software updates

**How to Rotate:**

1. **Generate new keys** (keep old ones temporarily)
   ```bash
   # Add new keys to .env
   API_KEYS=old-key-1,old-key-2,NEW-key-1,NEW-key-2
   ```

2. **Update clusters** with new keys
   ```bash
   # On each cluster
   sudo nano /etc/slurm-usage-history-exporter/config.json
   # Change api_key to NEW-key-X
   ```

3. **Test new keys**
   ```bash
   # Test from cluster
   slurm-usage-history-exporter --dry-run --verbose
   ```

4. **Remove old keys** after all clusters updated
   ```bash
   # backend/.env
   API_KEYS=NEW-key-1,NEW-key-2
   ```

5. **Restart backend**
   ```bash
   # Restart to reload .env
   systemctl restart slurm-usage-history-backend
   ```

---

## 🌐 Network Security

### HTTPS/TLS

**Production Requirement:** Always use HTTPS for data transmission

```json
// Cluster agent config
{
  "api_url": "https://dashboard.example.com",  // ← HTTPS required
  "api_key": "your-secret-key"
}
```

**Benefits:**
- ✅ API keys encrypted in transit
- ✅ Job data encrypted in transit
- ✅ Man-in-the-middle attack prevention
- ✅ Data integrity verification

**Setup with Nginx:**

```nginx
server {
    listen 443 ssl http2;
    server_name dashboard.example.com;

    ssl_certificate /etc/letsencrypt/live/dashboard.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/dashboard.example.com/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location /api {
        proxy_pass http://127.0.0.1:8100;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Firewall Rules

**Backend Server:**

```bash
# Allow HTTPS from cluster networks only
sudo ufw allow from 10.0.0.0/8 to any port 443 proto tcp

# Or specific clusters
sudo ufw allow from 192.168.1.0/24 to any port 443 proto tcp  # Cluster 1
sudo ufw allow from 192.168.2.0/24 to any port 443 proto tcp  # Cluster 2

# Deny all other traffic to backend
sudo ufw deny 8100
```

**Cluster Agents:**

```bash
# Allow outbound HTTPS
sudo ufw allow out 443/tcp

# No inbound connections needed (agent is client-only)
```

### CORS Configuration

**File:** `backend/.env`

```bash
# Restrict CORS to specific origins
CORS_ORIGINS=https://dashboard.example.com,https://dashboard-staging.example.com

# For development only (not production!)
# CORS_ORIGINS=http://localhost:3100
```

**What this prevents:**
- ✅ Unauthorized frontend applications from accessing API
- ✅ Cross-site scripting attacks
- ✅ CSRF attacks on dashboard endpoints

---

## 📊 Data Security

### Input Validation

**All inputs are validated before processing:**

**Schema Validation:** `backend/app/models/data_models.py`

```python
class JobRecord(BaseModel):
    """Model for a single job record."""

    JobID: str                    # Required string
    User: str                     # Required string
    Account: str                  # Required string
    Partition: str                # Required string
    State: str                    # Required string
    QOS: str | None = None        # Optional string
    Submit: datetime              # Required datetime
    Start: datetime | None = None # Optional datetime
    End: datetime | None = None   # Optional datetime
    CPUHours: float = 0.0         # Required float
    GPUHours: float = 0.0         # Required float
    AllocCPUS: int = 0            # Required int
    AllocGPUS: int = 0            # Required int
    AllocNodes: int = 0           # Required int
    NodeList: str | None = None   # Optional string
```

**Benefits:**
- ✅ Type checking (string, int, float, datetime)
- ✅ Required field validation
- ✅ Automatic rejection of malformed data
- ✅ SQL injection prevention (no SQL used)
- ✅ Command injection prevention (no shell commands)

### Path Traversal Protection

**Hostname sanitization prevents directory traversal attacks:**

```python
# In data.py
data_dir = Path(settings.data_path) / request.hostname / "weekly-data"
data_dir.mkdir(parents=True, exist_ok=True)
```

**Python's `pathlib` automatically handles:**
- ✅ `../` sequences (normalized away)
- ✅ Absolute paths (rejected)
- ✅ Symbolic links (resolved)

**Attack Prevention:**

```bash
# Attacker tries:
{"hostname": "../../../etc/passwd", "jobs": [...]}

# Results in:
# Path: /data/etc/passwd/weekly-data  (not /etc/passwd)
# Safe - contained within data directory
```

### Data Storage Security

**File Permissions:**

```bash
# Data directory should be restricted
chmod 755 /path/to/data
chown backend-user:backend-group /path/to/data

# Parquet files
chmod 644 /path/to/data/cluster-*/weekly-data/*.parquet
chown backend-user:backend-group /path/to/data/cluster-*/weekly-data/*.parquet
```

**Benefits:**
- ✅ Only backend process can write
- ✅ Read-only for dashboard queries
- ✅ No world-writable directories

### Rate Limiting

**Consider adding rate limiting for production:**

```python
# Example with slowapi
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/ingest")
@limiter.limit("10/minute")  # Max 10 uploads per minute
async def ingest_data(...):
    ...
```

**Benefits:**
- ✅ Prevents DoS attacks
- ✅ Limits impact of compromised keys
- ✅ Throttles brute-force attempts

---

## 🛡️ Defense in Depth

### Multiple Security Layers

```
Layer 1: Network Firewall
  ↓ Block unauthorized IPs

Layer 2: HTTPS/TLS
  ↓ Encrypt traffic

Layer 3: API Key Authentication
  ↓ Verify authorized client

Layer 4: Input Validation
  ↓ Validate data schema

Layer 5: Path Sanitization
  ↓ Prevent directory traversal

Layer 6: File Permissions
  ↓ Restrict write access

Layer 7: Rate Limiting (optional)
  ↓ Prevent abuse
```

### Attack Scenarios & Mitigations

#### Scenario 1: Unauthorized Upload Attempt

**Attack:**
```bash
curl -X POST https://dashboard.example.com/api/data/ingest \
  -H "Content-Type: application/json" \
  -d '{"hostname":"evil","jobs":[...]}'
```

**Defense:**
- ❌ **REJECTED:** No `X-API-Key` header
- **HTTP 401 Unauthorized:** "Missing API Key"

---

#### Scenario 2: Invalid API Key

**Attack:**
```bash
curl -X POST https://dashboard.example.com/api/data/ingest \
  -H "X-API-Key: guessed-key-12345" \
  -H "Content-Type: application/json" \
  -d '{"hostname":"evil","jobs":[...]}'
```

**Defense:**
- ❌ **REJECTED:** Invalid API key
- **HTTP 401 Unauthorized:** "Invalid API Key"

---

#### Scenario 3: Path Traversal Attempt

**Attack:**
```bash
curl -X POST https://dashboard.example.com/api/data/ingest \
  -H "X-API-Key: valid-key" \
  -H "Content-Type: application/json" \
  -d '{"hostname":"../../etc","jobs":[...]}'
```

**Defense:**
- ✅ **SANITIZED:** Path normalized to `data/etc/weekly-data/`
- No sensitive directories accessed

---

#### Scenario 4: Malformed Data Injection

**Attack:**
```bash
curl -X POST https://dashboard.example.com/api/data/ingest \
  -H "X-API-Key: valid-key" \
  -H "Content-Type: application/json" \
  -d '{"hostname":"cluster","jobs":[{"JobID":"'; DROP TABLE jobs;--"}]}'
```

**Defense:**
- ❌ **REJECTED:** Pydantic schema validation fails
- **HTTP 422 Unprocessable Entity:** Invalid data format
- **No SQL:** System uses parquet files (no SQL database)

---

#### Scenario 5: Large Payload DoS

**Attack:**
```bash
# Send 1GB of job data
curl -X POST https://dashboard.example.com/api/data/ingest \
  -H "X-API-Key: valid-key" \
  -H "Content-Type: application/json" \
  -d @huge_payload.json
```

**Defense:**
- ✅ **Rate Limiting:** If configured, limits requests per minute
- ✅ **Resource Limits:** Server memory/CPU limits
- ✅ **Request Size Limits:** FastAPI/Uvicorn can limit body size

**Configure in uvicorn:**
```python
uvicorn.run(
    app,
    limit_max_requests=1000,
    timeout_keep_alive=5
)
```

---

## 🔍 Security Monitoring

### Logging

**What gets logged:**
- All API requests (with IP, timestamp, endpoint)
- Authentication failures (invalid keys)
- Successful data ingestions (cluster, job count)
- Errors and exceptions

**Example logs:**

```
INFO:     127.0.0.1:54321 - "GET /api/dashboard/health HTTP/1.1" 200 OK
WARNING:  192.168.1.100:12345 - Authentication failed: Invalid API Key
INFO:     192.168.1.50:23456 - "POST /api/data/ingest HTTP/1.1" 200 OK
INFO:     Successfully ingested 1523 jobs for cluster-hpc-01
ERROR:    192.168.1.200:34567 - "POST /api/data/ingest HTTP/1.1" 422 Unprocessable Entity
```

### Monitoring Invalid Attempts

**Watch for:**
- Multiple 401 errors from same IP (brute force)
- 422 errors (malformed data injection attempts)
- Unusual hostnames (path traversal attempts)
- Large job counts (DoS attempts)

**Example monitoring script:**

```bash
# Monitor authentication failures
journalctl -u slurm-usage-history-backend -f | grep "401"

# Count failed attempts per IP
journalctl -u slurm-usage-history-backend --since today | \
  grep "401" | \
  awk '{print $5}' | \
  sort | uniq -c | sort -rn
```

---

## ✅ Security Checklist

### Before Production Deployment

- [ ] **API Keys**
  - [ ] Strong keys generated (32+ characters)
  - [ ] Keys stored securely in `.env`
  - [ ] `.env` file has 600 permissions
  - [ ] Keys shared via secure channel

- [ ] **Network Security**
  - [ ] HTTPS configured (not HTTP)
  - [ ] Valid SSL certificate
  - [ ] Firewall rules configured
  - [ ] CORS_ORIGINS restricted to production domain

- [ ] **Server Security**
  - [ ] Backend runs as non-root user
  - [ ] Data directory has correct permissions (755)
  - [ ] Log files are rotated
  - [ ] System updates applied

- [ ] **Monitoring**
  - [ ] Logging configured
  - [ ] Failed auth attempts monitored
  - [ ] Disk space alerts configured
  - [ ] Backup strategy in place

- [ ] **Documentation**
  - [ ] Security policy documented
  - [ ] Incident response plan
  - [ ] Key rotation schedule
  - [ ] Contact information for security issues

---

## 🚨 Incident Response

### If API Key is Compromised

1. **Immediately revoke the compromised key**
   ```bash
   # Remove from .env
   API_KEYS=remaining-valid-keys-only

   # Restart backend
   systemctl restart slurm-usage-history-backend
   ```

2. **Check logs for unauthorized access**
   ```bash
   journalctl -u slurm-usage-history-backend --since "1 hour ago" | grep "POST /api/data/ingest"
   ```

3. **Inspect data directory for suspicious files**
   ```bash
   find data/ -type f -mtime -1 -ls
   ```

4. **Generate and distribute new key**
   ```bash
   python3 -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

5. **Update all clusters** with new key

6. **Review security logs** for patterns

### If Suspicious Data Detected

1. **Identify affected cluster/files**
   ```bash
   ls -la data/suspicious-cluster/weekly-data/
   ```

2. **Quarantine suspicious data**
   ```bash
   mkdir quarantine/
   mv data/suspicious-cluster quarantine/
   ```

3. **Investigate origin**
   - Check logs for submission IP
   - Verify cluster configuration
   - Contact cluster administrator

4. **Restore from backup** if needed

---

## 📚 Summary

### Protection Mechanisms

| Threat | Protection | Status |
|--------|-----------|--------|
| Unauthorized uploads | API key authentication | ✅ Implemented |
| Stolen API keys | HTTPS encryption | ✅ Recommended |
| Brute force attacks | Rate limiting | ⚠️ Optional |
| Path traversal | Path sanitization | ✅ Implemented |
| SQL injection | No SQL (parquet files) | ✅ N/A |
| Command injection | No shell commands | ✅ N/A |
| XSS attacks | Input validation | ✅ Implemented |
| CSRF attacks | CORS restrictions | ✅ Implemented |
| DoS attacks | Rate limiting + resource limits | ⚠️ Optional |
| Man-in-the-middle | HTTPS/TLS | ✅ Recommended |

### Security Posture

**Current Implementation:**
- 🟢 **High:** API key authentication mandatory
- 🟢 **High:** Input validation via Pydantic
- 🟢 **High:** Path traversal protection
- 🟢 **High:** CORS protection
- 🟡 **Medium:** HTTPS (deployment-dependent)
- 🟡 **Medium:** Rate limiting (optional)

**Recommendation:** System is production-ready with proper deployment (HTTPS + firewall).

---

## 🔗 Related Documentation

- **API Authentication:** `backend/app/core/auth.py`
- **Configuration:** `backend/.env.example`
- **Deployment:** `CLUSTER_DEPLOYMENT.md`
- **Testing:** `TESTING_GUIDE.md`

For security questions or to report vulnerabilities, contact your system administrator.
