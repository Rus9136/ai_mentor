# Security Documentation — AI Mentor

**Version:** 1.0
**Last Updated:** 2026-01-07
**Classification:** Internal

---

## Table of Contents

1. [Security Overview](#1-security-overview)
2. [Authentication](#2-authentication)
3. [Authorization (RBAC)](#3-authorization-rbac)
4. [Data Isolation (RLS)](#4-data-isolation-rls)
5. [Rate Limiting](#5-rate-limiting)
6. [CORS Policy](#6-cors-policy)
7. [Password Security](#7-password-security)
8. [Input Validation](#8-input-validation)
9. [File Upload Security](#9-file-upload-security)
10. [API Security](#10-api-security)
11. [Database Security](#11-database-security)
12. [Production Configuration](#12-production-configuration)
13. [Security Checklist](#13-security-checklist)
14. [Incident Response](#14-incident-response)

---

## 1. Security Overview

### Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLIENT APPS                                  │
│         (Student App, Teacher App, Admin Panel, Mobile)             │
└─────────────────────────────┬───────────────────────────────────────┘
                              │ HTTPS Only
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         NGINX (Reverse Proxy)                        │
│                    TLS 1.2+, Certificate Pinning                    │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         FASTAPI APPLICATION                          │
├─────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐ │
│  │ Rate Limit  │→ │    CORS     │→ │  Tenancy    │→ │   Auth     │ │
│  │ Middleware  │  │ Middleware  │  │ Middleware  │  │ Dependency │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └────────────┘ │
│                              │                                       │
│                              ▼                                       │
│                    ┌─────────────────┐                              │
│                    │   API Endpoints │                              │
│                    │   (RBAC Check)  │                              │
│                    └────────┬────────┘                              │
└─────────────────────────────┼───────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    POSTGRESQL DATABASE                               │
│                Row Level Security (RLS) Enabled                      │
│                   37+ Tables with Policies                          │
└─────────────────────────────────────────────────────────────────────┘
```

### Security Layers

| Layer | Protection |
|-------|------------|
| **Network** | HTTPS, TLS 1.2+, HSTS |
| **Application** | Rate limiting, CORS, Input validation |
| **Authentication** | JWT (HS256), Google OAuth 2.0 |
| **Authorization** | RBAC (5 roles), Endpoint guards |
| **Data** | RLS policies, School isolation |
| **Storage** | bcrypt passwords, Encrypted secrets |

---

## 2. Authentication

### 2.1 JWT Tokens

**Algorithm:** HS256 (HMAC-SHA256)

| Token Type | Expiration | Purpose |
|------------|------------|---------|
| `access_token` | 30 minutes | API access |
| `refresh_token` | 7 days | Obtain new access token |

**Token Payload:**
```json
{
  "sub": "123",           // User ID
  "email": "user@school.com",
  "role": "student",
  "school_id": 7,
  "exp": 1706180000,      // Expiration timestamp
  "type": "access"        // Token type
}
```

**Security Measures:**
- Token type validation (`access` vs `refresh`)
- Expiration check on every request
- Secret key validation at startup
- No sensitive data in token (only IDs and role)

### 2.2 Token Flow

```
1. Login Request
   POST /auth/login {email, password}

2. Server validates credentials
   - bcrypt password verification
   - Check user is_active = true

3. Generate tokens
   - access_token (30 min)
   - refresh_token (7 days)

4. Client stores tokens
   - Keychain (iOS)
   - EncryptedSharedPreferences (Android)

5. API requests
   Authorization: Bearer <access_token>

6. Token refresh
   POST /auth/refresh {refresh_token}
   - Validates refresh token
   - Issues new token pair
```

### 2.3 Google OAuth

**Flow:** Authorization Code with PKCE

```
1. Client initiates OAuth
   - Redirect to Google consent screen

2. User authorizes
   - Google returns id_token

3. Server validates id_token
   POST /auth/google {id_token}
   - Verify signature with Google public keys
   - Check audience matches GOOGLE_CLIENT_ID
   - Check token not expired

4. Create/update user
   - If new user → requires onboarding
   - If existing → issue tokens
```

**Configuration:**
```env
GOOGLE_CLIENT_ID=your-web-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_ID_MOBILE=your-mobile-client-id.apps.googleusercontent.com
```

### 2.4 Secret Key Management

**Requirements:**
- Minimum 32 bytes (256 bits)
- Cryptographically random
- Never commit to repository
- Rotate periodically

**Generation:**
```bash
openssl rand -hex 32
```

**Validation:**
The application validates SECRET_KEY at startup and warns if using insecure defaults:
```python
insecure_defaults = [
    "your-secret-key-here-change-in-production",
    "secret",
    "changeme",
]
if SECRET_KEY in insecure_defaults:
    warnings.warn("SECRET_KEY is using an insecure default value!")
```

---

## 3. Authorization (RBAC)

### 3.1 Role Hierarchy

```
SUPER_ADMIN (Highest)
    │
    └── ADMIN (School Administrator)
            │
            └── TEACHER
                    │
                    └── STUDENT
                            │
                            └── PARENT (Lowest)
```

### 3.2 Role Permissions

| Role | Scope | Permissions |
|------|-------|-------------|
| **SUPER_ADMIN** | All schools | Manage schools, global content, GOSO |
| **ADMIN** | Own school | Manage users, classes, school content |
| **TEACHER** | Own classes | View analytics, create homework |
| **STUDENT** | Own data | Take tests, view progress |
| **PARENT** | Own children | View children's progress |

### 3.3 API Endpoint Guards

**Dependencies:**
```python
# Any authenticated user
current_user: User = Depends(get_current_user)

# Specific role required
current_user: User = Depends(require_student)
current_user: User = Depends(require_teacher)
current_user: User = Depends(require_admin)
current_user: User = Depends(require_super_admin)
```

**Endpoint Prefixes:**

| Prefix | Required Role |
|--------|---------------|
| `/api/v1/auth/*` | Public |
| `/api/v1/admin/global/*` | SUPER_ADMIN |
| `/api/v1/admin/school/*` | ADMIN |
| `/api/v1/teachers/*` | TEACHER |
| `/api/v1/students/*` | STUDENT |
| `/api/v1/parents/*` | PARENT |

### 3.4 School ID Enforcement

**Critical Rule:** School ID is **NEVER** accepted from client input.

```python
# CORRECT: Get school_id from authenticated user's token
@router.get("/students")
async def get_students(
    school_id: int = Depends(get_current_user_school_id),  # From JWT
    db: AsyncSession = Depends(get_db)
):
    # school_id is trusted (from token)
    ...

# WRONG: Accept school_id from query parameter
@router.get("/students")
async def get_students(
    school_id: int = Query(...),  # NEVER DO THIS!
    ...
):
    ...
```

---

## 4. Data Isolation (RLS)

### 4.1 Overview

**Row Level Security (RLS)** ensures that database queries automatically filter data based on the current user's context.

```
User from School 1 → Can only see School 1 data
User from School 2 → Can only see School 2 data
SUPER_ADMIN → Can see all data (RLS bypass)
```

### 4.2 Session Variables

Set automatically by `get_db()` dependency:

| Variable | Description |
|----------|-------------|
| `app.current_tenant_id` | User's school_id |
| `app.current_user_id` | User's ID |
| `app.is_super_admin` | 'true' or 'false' |

### 4.3 RLS Policy Pattern

```sql
-- Standard tenant isolation policy
CREATE POLICY tenant_isolation_policy ON table_name
    FOR ALL
    USING (
        -- Super admin bypasses RLS
        COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true'
        OR
        -- User sees only their school's data
        school_id = NULLIF(current_setting('app.current_tenant_id', true), '')::integer
    )
    WITH CHECK (
        COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true'
        OR
        school_id = NULLIF(current_setting('app.current_tenant_id', true), '')::integer
    );
```

### 4.4 Protected Tables (37+)

| Category | Tables |
|----------|--------|
| **Users** | users, students, teachers, parents |
| **Classes** | school_classes, class_students, class_teachers |
| **Content** | textbooks, chapters, paragraphs, tests, questions |
| **Progress** | test_attempts, paragraph_mastery, chapter_mastery |
| **Homework** | homework, homework_tasks, homework_students, submissions |
| **Chat** | chat_sessions, chat_messages |
| **GOSO** | paragraph_outcomes |

### 4.5 Hybrid Content Model

```sql
-- Global content (visible to all schools)
school_id IS NULL

-- School-specific content (visible only to that school)
school_id = specific_school_id
```

**RLS for Hybrid Tables:**
```sql
CREATE POLICY content_policy ON textbooks
    FOR SELECT
    USING (
        school_id IS NULL  -- Global content
        OR
        school_id = current_tenant_id  -- School content
        OR
        is_super_admin = 'true'  -- Super admin
    );
```

---

## 5. Rate Limiting

### 5.1 Configuration

**Library:** slowapi (wrapper around limits)

**IP Detection:**
```python
def get_client_ip(request: Request) -> str:
    # Check X-Forwarded-For (reverse proxy)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    # Check X-Real-IP (nginx)
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    # Direct connection
    return request.client.host
```

### 5.2 Rate Limits

| Endpoint | Limit | Window |
|----------|-------|--------|
| `POST /auth/login` | 5 requests | 1 minute |
| `POST /auth/refresh` | 10 requests | 1 minute |
| `POST /auth/google` | 10 requests | 1 minute |
| `POST /auth/onboarding/*` | 10 requests | 1 minute |
| `POST /chat/*/messages` | 20 requests | 1 minute |
| All other endpoints | 60 requests | 1 minute |

### 5.3 Response Headers

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1706180000
```

### 5.4 Rate Limit Exceeded Response

```json
{
  "detail": "Rate limit exceeded. Try again in 45 seconds.",
  "error_code": "RATE_001"
}
```
HTTP Status: `429 Too Many Requests`

---

## 6. CORS Policy

### 6.1 Configuration

```python
# Explicit allowed methods (not "*")
allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]

# Explicit allowed headers (not "*")
allow_headers=["Accept", "Content-Type", "Authorization", "X-Requested-With"]

# Credentials allowed
allow_credentials=True

# Allowed origins from environment
allow_origins=settings.BACKEND_CORS_ORIGINS
```

### 6.2 Allowed Origins (Production)

```env
BACKEND_CORS_ORIGINS=https://ai-mentor.kz,https://admin.ai-mentor.kz,https://teacher.ai-mentor.kz,https://api.ai-mentor.kz
```

### 6.3 Security Considerations

- **Never use `allow_origins=["*"]`** with `allow_credentials=True`
- Origins must be explicit URLs (no wildcards in production)
- Preflight requests (OPTIONS) are cached for performance

---

## 7. Password Security

### 7.1 Hashing

**Algorithm:** bcrypt

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Hash password
hashed = pwd_context.hash(plain_password)

# Verify password
is_valid = pwd_context.verify(plain_password, hashed_password)
```

**Properties:**
- Automatic salt generation
- Configurable work factor (default: 12 rounds)
- ~100ms per hash (intentionally slow)

### 7.2 Password Requirements

| Requirement | Value |
|-------------|-------|
| Minimum length | 8 characters |
| Required | At least 1 letter and 1 number |

**Validation (Pydantic):**
```python
@field_validator("password")
def validate_password(cls, v):
    if len(v) < 8:
        raise ValueError("Password must be at least 8 characters")
    if not any(c.isalpha() for c in v):
        raise ValueError("Password must contain at least one letter")
    if not any(c.isdigit() for c in v):
        raise ValueError("Password must contain at least one digit")
    return v
```

### 7.3 Password Storage

- Passwords are **never** stored in plain text
- Only bcrypt hash is stored in database
- Original password is never logged

---

## 8. Input Validation

### 8.1 Pydantic Schemas

All input is validated through Pydantic models:

```python
class StudentCreate(BaseModel):
    email: EmailStr  # Email format validation
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    grade_level: int = Field(..., ge=1, le=11)  # Grade 1-11
```

### 8.2 SQL Injection Prevention

**SQLAlchemy ORM** automatically parameterizes queries:

```python
# SAFE: Parameterized query
result = await db.execute(
    select(Student).where(Student.email == email)  # 'email' is parameterized
)

# DANGEROUS: Never do this!
result = await db.execute(
    f"SELECT * FROM students WHERE email = '{email}'"  # SQL injection risk
)
```

### 8.3 XSS Prevention

- All output is escaped by frontend frameworks (React/Next.js)
- Content-Type headers are set correctly
- Rich content (HTML) is sanitized on input

### 8.4 Path Traversal Prevention

```python
# File upload validation
if ".." in filename or filename.startswith("/"):
    raise HTTPException(400, "Invalid filename")
```

---

## 9. File Upload Security

### 9.1 Restrictions

| Type | Max Size | Allowed MIME Types |
|------|----------|-------------------|
| **Images** | 5 MB | image/jpeg, image/png, image/webp, image/gif |
| **PDFs** | 50 MB | application/pdf |
| **Audio** | 50 MB | audio/mpeg, audio/wav, audio/ogg |
| **Video** | 200 MB | video/mp4, video/webm |
| **Slides** | 50 MB | application/pdf |

### 9.2 Validation

```python
# MIME type validation
async def validate_file(file: UploadFile, allowed_types: list[str]):
    # Check MIME type
    if file.content_type not in allowed_types:
        raise HTTPException(400, f"File type {file.content_type} not allowed")

    # Check file size
    content = await file.read()
    if len(content) > max_size:
        raise HTTPException(400, "File too large")

    # Reset file pointer
    await file.seek(0)
```

### 9.3 Storage

- Files stored in `/uploads/` directory
- Organized by type: `images/`, `audio/`, `pdfs/`, etc.
- Unique filenames to prevent overwrites
- Not directly accessible (served through API)

---

## 10. API Security

### 10.1 HTTPS Only

All API endpoints require HTTPS in production:

```nginx
# Nginx configuration
server {
    listen 80;
    server_name api.ai-mentor.kz;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.ai-mentor.kz;

    ssl_certificate /etc/letsencrypt/live/ai-mentor.kz/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/ai-mentor.kz/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
}
```

### 10.2 Security Headers

```nginx
# Recommended headers
add_header X-Content-Type-Options nosniff;
add_header X-Frame-Options DENY;
add_header X-XSS-Protection "1; mode=block";
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
```

### 10.3 Error Handling

**Standardized error responses** prevent information leakage:

```json
{
  "detail": "User-friendly message",
  "error_code": "AUTH_001"
}
```

**Internal errors** are logged but not exposed to clients:
```python
@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    logger.error(f"Internal error: {exc}")  # Log full error
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error_code": "SVC_001"}
    )
```

---

## 11. Database Security

### 11.1 Connection Security

```env
# Use strong password
POSTGRES_PASSWORD=complex-password-with-special-chars!

# SSL for production (if not in Docker network)
DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require
```

### 11.2 PostgreSQL Roles

| Role | Purpose | Privileges |
|------|---------|------------|
| `ai_mentor_user` | Migrations | SUPERUSER (bypasses RLS) |
| `ai_mentor_app` | Application | SELECT, INSERT, UPDATE, DELETE (RLS applies) |

**Runtime Connection:**
```python
# Application uses ai_mentor_app role
DATABASE_URL = "postgresql://ai_mentor_app:password@postgres:5432/ai_mentor_db"
```

### 11.3 Backups

- Daily automated backups
- Encrypted backup storage
- Point-in-time recovery enabled
- Test restores periodically

---

## 12. Production Configuration

### 12.1 Environment Variables

**Required for Production:**

```env
# Security
SECRET_KEY=<generated-with-openssl-rand-hex-32>
DEBUG=false

# Database
POSTGRES_PASSWORD=<strong-password>

# OAuth
GOOGLE_CLIENT_ID=<your-client-id>

# CORS
BACKEND_CORS_ORIGINS=https://ai-mentor.kz,https://admin.ai-mentor.kz

# API Keys (if using AI features)
JINA_API_KEY=<your-api-key>
OPENROUTER_API_KEY=<your-api-key>
```

### 12.2 Docker Security

```yaml
# docker-compose.yml
services:
  backend:
    # Don't run as root
    user: "1000:1000"

    # Read-only filesystem where possible
    read_only: true
    tmpfs:
      - /tmp

    # Drop capabilities
    cap_drop:
      - ALL

    # No privileged mode
    privileged: false
```

### 12.3 Nginx Configuration

```nginx
# Rate limiting
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;

server {
    location /api {
        limit_req zone=api burst=20 nodelay;

        # Proxy to backend
        proxy_pass http://backend:8000;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## 13. Security Checklist

### Pre-Deployment

- [ ] SECRET_KEY is unique and securely generated
- [ ] DEBUG=false in production
- [ ] CORS origins are explicitly listed (no wildcards)
- [ ] HTTPS is enforced
- [ ] Database password is strong
- [ ] RLS is enabled on all tenant tables
- [ ] Rate limiting is configured
- [ ] File upload limits are set
- [ ] Error messages don't expose internals

### Ongoing

- [ ] Monitor failed login attempts
- [ ] Review access logs regularly
- [ ] Update dependencies (security patches)
- [ ] Rotate SECRET_KEY periodically
- [ ] Audit user permissions
- [ ] Test RLS isolation
- [ ] Backup verification

### Code Review

- [ ] No hardcoded credentials
- [ ] No SQL string concatenation
- [ ] School ID from token, not client
- [ ] Input validation on all endpoints
- [ ] Proper error handling

---

## 14. Incident Response

### 14.1 Security Incident Types

| Severity | Example | Response Time |
|----------|---------|---------------|
| **Critical** | Data breach, RCE | Immediate |
| **High** | Auth bypass, SQL injection | < 4 hours |
| **Medium** | Rate limit bypass, XSS | < 24 hours |
| **Low** | Info disclosure | < 1 week |

### 14.2 Response Steps

1. **Identify** — Confirm the incident
2. **Contain** — Limit damage (disable accounts, block IPs)
3. **Investigate** — Determine scope and impact
4. **Remediate** — Fix vulnerability
5. **Recover** — Restore normal operations
6. **Report** — Document and notify stakeholders

### 14.3 Contact

**Security Issues:** security@ai-mentor.kz

For responsible disclosure of vulnerabilities, please email with:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

---

## Appendix A: Error Codes Reference

| Code | Description |
|------|-------------|
| `AUTH_001` | Invalid credentials |
| `AUTH_002` | Token expired |
| `AUTH_003` | Invalid token |
| `AUTH_004` | Token revoked |
| `ACCESS_001` | Permission denied |
| `ACCESS_002` | Role not allowed |
| `ACCESS_003` | School access denied |
| `VAL_001` | Invalid format |
| `VAL_002` | Required field missing |
| `RES_001` | Resource not found |
| `RES_002` | Resource already exists |
| `SVC_001` | Internal server error |
| `RATE_001` | Rate limit exceeded |

---

## Appendix B: Security Testing

### Tools

| Tool | Purpose |
|------|---------|
| OWASP ZAP | Automated vulnerability scanning |
| Burp Suite | Manual penetration testing |
| sqlmap | SQL injection testing |
| pytest | Unit/integration tests |

### Test Commands

```bash
# Run security-focused tests
pytest backend/tests/test_content_isolation.py -v
pytest backend/tests/test_rls_type_safety.py -v
pytest backend/tests/test_homework_rls.py -v

# Check for common vulnerabilities
bandit -r backend/app/
```

---

**Document Version:** 1.0
**Last Updated:** 2026-01-07
**Author:** AI Mentor Security Team
