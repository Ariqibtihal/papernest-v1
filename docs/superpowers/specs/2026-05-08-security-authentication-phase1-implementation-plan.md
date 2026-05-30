# Security & Authentication - Phase 1 Implementation Plan

**Date:** 2026-05-08  
**Design Doc:** [security-authentication-phase1-design.md](./2026-05-08-security-authentication-phase1-design.md)  
**Status:** Ready for Implementation  

## Implementation Overview

This plan breaks down Phase 1 implementation into manageable tasks with clear dependencies and verification steps.

## Task Breakdown

### Task 1: Setup Authentication Dependencies
**Priority:** Critical  
**Dependencies:** None  
**Estimated Time:** 15 minutes  

**Steps:**
1. Add authentication dependencies to `pyproject.toml`:
   ```toml
   dependencies = [
       # ... existing dependencies
       "python-jose[cryptography]>=3.3",
       "passlib[bcrypt]>=1.7",
       "python-multipart>=0.0.6",
       "slowapi>=0.1.9",
   ]
   ```

2. Install dependencies:
   ```powershell
   uv sync
   ```

**Verification:**
```powershell
uv run python -c "import jose, passlib, slowapi; print('All dependencies installed')"
```

---

### Task 2: Create User Database Models
**Priority:** Critical  
**Dependencies:** Task 1  
**Estimated Time:** 30 minutes  

**Steps:**
1. Create `models/user.py`:
   - Define User SQLAlchemy model
   - Define OAuthAccount model
   - Define UserSession model
   - Add indexes for performance

2. Update `models/__init__.py` to export new models

3. Update `app/db/session.py` to import new models in `init_db()`

**Files to Create:**
- `models/user.py` (new)

**Files to Modify:**
- `models/__init__.py`
- `app/db/session.py`

**Verification:**
```powershell
uv run python -c "from models.user import User, OAuthAccount, UserSession; print('Models imported successfully')"
```

---

### Task 3: Create Authentication Schemas
**Priority:** Critical  
**Dependencies:** Task 2  
**Estimated Time:** 20 minutes  

**Steps:**
1. Create `schemas/auth.py`:
   - UserRegister schema
   - UserLogin schema
   - Token schema
   - TokenPayload schema
   - UserOut schema

**Files to Create:**
- `schemas/auth.py` (new)

**Verification:**
```powershell
uv run python -c "from schemas.auth import UserRegister, UserLogin, Token; print('Auth schemas imported')"
```

---

### Task 4: Implement Password Hashing Utilities
**Priority:** Critical  
**Dependencies:** Task 1  
**Estimated Time:** 15 minutes  

**Steps:**
1. Create `utils/security.py`:
   - `hash_password(password: str) -> str`
   - `verify_password(plain_password: str, hashed_password: str) -> bool`

**Files to Create:**
- `utils/security.py` (new)

**Verification:**
```powershell
uv run python -c "from utils.security import hash_password, verify_password; h = hash_password('test'); print(verify_password('test', h))"
```

---

### Task 5: Implement JWT Token Management
**Priority:** Critical  
**Dependencies:** Task 3, Task 4  
**Estimated Time:** 30 minutes  

**Steps:**
1. Create `services/auth_service.py`:
   - `create_access_token(data: dict) -> str`
   - `create_refresh_token(user_id: int) -> str`
   - `verify_token(token: str) -> dict`
   - `decode_token(token: str) -> dict`

2. Update `app/config.py`:
   - Add JWT configuration settings
   - Add JWT_SECRET_KEY environment variable

**Files to Create:**
- `services/auth_service.py` (new)

**Files to Modify:**
- `app/config.py`

**Verification:**
```powershell
uv run python -c "from services.auth_service import create_access_token, verify_token; t = create_access_token({'sub': 'test'}); print(verify_token(t))"
```

---

### Task 6: Create Authentication Middleware
**Priority:** Critical  
**Dependencies:** Task 5  
**Estimated Time:** 25 minutes  

**Steps:**
1. Create `app/core/auth.py`:
   - `get_current_user` dependency
   - `get_current_active_user` dependency
   - Token extraction and validation logic

**Files to Create:**
- `app/core/auth.py` (new)

**Verification:**
```powershell
uv run python -c "from app.core.auth import get_current_user; print('Auth middleware imported')"
```

---

### Task 7: Implement Email/Password Registration
**Priority:** Critical  
**Dependencies:** Task 6  
**Estimated Time:** 30 minutes  

**Steps:**
1. Create `app/api/routes_auth.py`:
   - `POST /auth/register` endpoint
   - Email validation
   - Password validation
   - Duplicate email check
   - User creation

**Files to Create:**
- `app/api/routes_auth.py` (new)

**Verification:**
- Manual test with curl or Postman
- Check database for new user record

---

### Task 8: Implement Login Endpoint
**Priority:** Critical  
**Dependencies:** Task 7  
**Estimated Time:** 20 minutes  

**Steps:**
1. Add to `app/api/routes_auth.py`:
   - `POST /auth/login` endpoint
   - Verify credentials
   - Generate access and refresh tokens
   - Store refresh token in database
   - Return tokens

**Verification:**
- Test login with registered user
- Verify JWT token returned
- Check refresh token in database

---

### Task 9: Implement Token Refresh
**Priority:** High  
**Dependencies:** Task 8  
**Estimated Time:** 20 minutes  

**Steps:**
1. Add to `app/api/routes_auth.py`:
   - `POST /auth/refresh` endpoint
   - Validate refresh token
   - Generate new access token
   - Optionally rotate refresh token

**Verification:**
- Test token refresh flow
- Verify new access token works

---

### Task 10: Implement Logout
**Priority:** High  
**Dependencies:** Task 9  
**Estimated Time:** 15 minutes  

**Steps:**
1. Add to `app/api/routes_auth.py`:
   - `POST /auth/logout` endpoint
   - Revoke refresh token
   - Clear session

**Verification:**
- Test logout
- Verify refresh token revoked
- Verify token no longer works

---

### Task 11: Setup ORCID OAuth Integration
**Priority:** High  
**Dependencies:** Task 6  
**Estimated Time:** 45 minutes  

**Steps:**
1. Create `services/oauth_service.py`:
   - ORCID OAuth flow implementation
   - Token exchange
   - User info retrieval

2. Add to `app/api/routes_auth.py`:
   - `GET /auth/orcid` - Initiate OAuth
   - `GET /auth/orcid/callback` - Handle callback

3. Update `app/config.py`:
   - Add ORCID_CLIENT_ID, ORCID_CLIENT_SECRET
   - Add ORCID_REDIRECT_URI

**Files to Create:**
- `services/oauth_service.py` (new)

**Files to Modify:**
- `app/api/routes_auth.py`
- `app/config.py`

**Verification:**
- Test ORCID OAuth flow
- Verify user created/updated
- Check tokens returned

---

### Task 12: Setup Google OAuth Integration
**Priority:** High  
**Dependencies:** Task 11  
**Estimated Time:** 30 minutes  

**Steps:**
1. Add to `services/oauth_service.py`:
   - Google OAuth flow implementation
   - Token exchange
   - User info retrieval

2. Add to `app/api/routes_auth.py`:
   - `GET /auth/google` - Initiate OAuth
   - `GET /auth/google/callback` - Handle callback

3. Update `app/config.py`:
   - Add GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
   - Add GOOGLE_REDIRECT_URI

**Verification:**
- Test Google OAuth flow
- Verify user created/updated
- Check tokens returned

---

### Task 13: Implement User Profile Endpoint
**Priority:** Medium  
**Dependencies:** Task 6  
**Estimated Time:** 15 minutes  

**Steps:**
1. Add to `app/api/routes_auth.py`:
   - `GET /auth/me` endpoint
   - Return current user profile

**Verification:**
- Test with authenticated request
- Verify user data returned

---

### Task 14: Configure CORS Middleware
**Priority:** Critical  
**Dependencies:** None  
**Estimated Time:** 20 minutes  

**Steps:**
1. Update `app/main.py`:
   - Configure CORSMiddleware
   - Set allowed origins
   - Set allowed methods and headers

**Verification:**
- Test CORS preflight requests
- Verify headers returned

---

### Task 15: Implement Rate Limiting
**Priority:** High  
**Dependencies:** Task 1  
**Estimated Time:** 30 minutes  

**Steps:**
1. Create `app/core/rate_limit.py`:
   - Configure slowapi
   - Define rate limits
   - Create rate limit dependency

2. Apply rate limiting to auth endpoints:
   - Login: 10 req/min per IP
   - Register: 5 req/min per IP
   - General API: 100 req/min per user

**Files to Create:**
- `app/core/rate_limit.py` (new)

**Files to Modify:**
- `app/api/routes_auth.py`

**Verification:**
- Test rate limiting
- Verify 429 response when exceeded
- Verify limit resets

---

### Task 16: Add Security Headers
**Priority:** High  
**Dependencies:** None  
**Estimated Time:** 20 minutes  

**Steps:**
1. Create `app/core/security_headers.py`:
   - SecurityHeadersMiddleware
   - Add headers to all responses

2. Register middleware in `app/main.py`

**Files to Create:**
- `app/core/security_headers.py` (new)

**Files to Modify:**
- `app/main.py`

**Verification:**
- Test any endpoint
- Verify security headers present

---

### Task 17: Update Existing Routes for Authentication
**Priority:** Critical  
**Dependencies:** Task 6  
**Estimated Time:** 40 minutes  

**Steps:**
1. Update all existing routes to require authentication:
   - `routes_search.py` - Require auth for search
   - `routes_saved.py` - Require auth for saved papers
   - `routes_alert.py` - Require auth for alerts
   - `routes_export.py` - Require auth for export

2. Add user context to operations (e.g., saved papers linked to user)

**Files to Modify:**
- `app/api/routes_search.py`
- `app/api/routes_saved.py`
- `app/api/routes_alert.py`
- `app/api/routes_export.py`

**Verification:**
- Test endpoints without auth (should fail)
- Test endpoints with auth (should succeed)
- Verify user-specific data

---

### Task 18: Write Unit Tests
**Priority:** High  
**Dependencies:** All previous tasks  
**Estimated Time:** 60 minutes  

**Steps:**
1. Create test files:
   - `tests/test_auth_routes.py`
   - `tests/test_auth_service.py`
   - `tests/test_oauth_service.py`

2. Write tests for:
   - Registration
   - Login
   - Token refresh
   - Logout
   - OAuth flows (mocked)
   - Rate limiting
   - Authentication middleware

**Files to Create:**
- `tests/test_auth_routes.py` (new)
- `tests/test_auth_service.py` (new)
- `tests/test_oauth_service.py` (new)

**Verification:**
```powershell
uv run pytest tests/test_auth* -v
```

---

### Task 19: Update API Documentation
**Priority:** Medium  
**Dependencies:** All previous tasks  
**Estimated Time:** 30 minutes  

**Steps:**
1. Update FastAPI app metadata
2. Add authentication documentation to endpoints
3. Update README with auth setup instructions

**Files to Modify:**
- `app/main.py`
- `README.md`

**Verification:**
- Check Swagger UI at `/docs`
- Verify auth endpoints documented
- Verify "Authorize" button works

---

### Task 20: Create Alembic Migration
**Priority:** Critical  
**Dependencies:** Task 2  
**Estimated Time:** 20 minutes  

**Steps:**
1. Initialize Alembic if not already:
   ```powershell
   uv run alembic init alembic
   ```

2. Configure `alembic/env.py` for async

3. Create migration:
   ```powershell
   uv run alembic revision --autogenerate -m "Add authentication tables"
   uv run alembic upgrade head
   ```

**Verification:**
```powershell
uv run alembic current
# Check tables exist in database
```

---

## Implementation Order

Execute tasks in this order:

```
Phase 1.1: Core Setup (Tasks 1-6)
├── Task 1: Dependencies
├── Task 2: Database Models
├── Task 3: Schemas
├── Task 4: Password Utilities
├── Task 5: JWT Management
└── Task 6: Authentication Middleware

Phase 1.2: Email/Password Auth (Tasks 7-10, 13)
├── Task 7: Registration
├── Task 8: Login
├── Task 9: Token Refresh
├── Task 10: Logout
└── Task 13: User Profile

Phase 1.3: OAuth Integration (Tasks 11-12)
├── Task 11: ORCID OAuth
└── Task 12: Google OAuth

Phase 1.4: Security Hardening (Tasks 14-16)
├── Task 14: CORS
├── Task 15: Rate Limiting
└── Task 16: Security Headers

Phase 1.5: Integration & Testing (Tasks 17-20)
├── Task 20: Database Migration
├── Task 17: Update Existing Routes
├── Task 18: Unit Tests
└── Task 19: Documentation
```

## Environment Setup Requirements

Before starting, ensure you have:

1. **ORCID Sandbox Account**
   - Register at: https://sandbox.orcid.org/
   - Create public API client at: https://sandbox.orcid.org/developer-tools

2. **Google OAuth Credentials**
   - Go to: https://console.cloud.google.com/
   - Create OAuth 2.0 client ID
   - Add authorized redirect URI: `http://localhost:8000/api/v1/auth/google/callback`

3. **Environment Variables**
   Create `.env` entries:
   ```
   JWT_SECRET_KEY=your-256-bit-secret-here
   ORCID_CLIENT_ID=your-orcid-client-id
   ORCID_CLIENT_SECRET=your-orcid-client-secret
   ORCID_REDIRECT_URI=http://localhost:8000/api/v1/auth/orcid/callback
   GOOGLE_CLIENT_ID=your-google-client-id
   GOOGLE_CLIENT_SECRET=your-google-client-secret
   GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/google/callback
   ```

## Success Verification Checklist

After completing all tasks:

- [ ] Can register with email/password
- [ ] Can login and receive JWT tokens
- [ ] Can refresh tokens
- [ ] Can logout
- [ ] Can login with ORCID OAuth
- [ ] Can login with Google OAuth
- [ ] Rate limiting works (429 after limit)
- [ ] Security headers present in responses
- [ ] CORS configured correctly
- [ ] Existing routes require authentication
- [ ] All tests pass
- [ ] Swagger UI shows auth endpoints
- [ ] README updated with auth setup

## Rollback Procedures

If critical issues arise:

1. **Revert Database Changes:**
   ```powershell
   uv run alembic downgrade -1
   ```

2. **Disable Authentication:**
   - Comment out auth dependencies in route files
   - Remove auth middleware from main.py
   - Restart server

3. **Disable OAuth:**
   - Comment out OAuth routes
   - Remove OAuth dependencies

## Next Steps After Phase 1

Once Phase 1 is complete and verified, proceed to:
- **Phase 2:** Database migration to PostgreSQL
- **Phase 2:** Advanced security (CSRF, email verification, password reset)
- **Phase 2:** API key generation for power users
