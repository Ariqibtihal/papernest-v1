# Security & Authentication - Phase 1 Design

**Date:** 2026-05-08  
**Status:** Approved  
**Priority:** Critical - High Priority  

## Overview

Implementasi sistem autentikasi sederhana untuk PaperLens dengan email/password dan JWT tokens. Single user tier dengan akses penuh ke semua fitur.

## Goals

- Secure user authentication dengan email/password
- JWT-based session management
- Basic security hardening (CORS, rate limiting, input validation)
- Foundation untuk future security enhancements

## Architecture

### Components

**1. Authentication System**
- JWT-based authentication dengan access & refresh tokens
- Email/password registration & login
- Password hashing dengan bcrypt
- Token management dan refresh mechanism

**2. Security Middleware**
- CORS configuration yang proper
- Rate limiting per IP/user (100 requests/minute default)
- Input validation dan sanitization
- SQL injection prevention via parameterized queries
- XSS protection headers

**3. Database Models**
- User model (id, email, password_hash, full_name, is_active, created_at, updated_at, last_login)
- UserSession model (untuk refresh tokens)

**4. API Endpoints**
```
POST /api/v1/auth/register - Email registration
POST /api/v1/auth/login - Email login
POST /api/v1/auth/refresh - Refresh access token
POST /api/v1/auth/logout - Invalidate session
GET /api/v1/auth/me - Get current user profile
```

**5. Security Configuration**
- JWT secret key (environment variable)
- Token expiration: Access (15 min), Refresh (7 days)
- Rate limiting: 100 req/min per user, 1000 req/min per IP
- CORS: Allowlist specific origins
- Password requirements: min 8 chars

## Technical Decisions

### Dependencies
- `python-jose[cryptography]` - JWT token handling
- `passlib[bcrypt]` - Password hashing
- `python-multipart` - OAuth form data handling
- `httpx` - OAuth HTTP requests (already installed)
- `slowapi` - Rate limiting for FastAPI

### Database Schema

**users table:**
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
```

**user_sessions table:**
```sql
CREATE TABLE user_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    refresh_token_hash VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    revoked BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_sessions_user ON user_sessions(user_id);
CREATE INDEX idx_sessions_token ON user_sessions(refresh_token_hash);
```

### Authentication Flow

**Registration:**
1. User submits email, password, full_name
2. System validates input (email format, password strength)
3. System checks email uniqueness
4. System hashes password with bcrypt
5. System creates user record
6. System returns success message

**Login:**
1. User submits email and password
2. System validates credentials
3. System generates access token (15 min expiry)
4. System generates refresh token (7 days expiry)
5. System stores refresh token hash in database
6. System returns both tokens

**Token Refresh:**
1. Client sends refresh token
2. System validates refresh token
3. System generates new access token
4. Optionally rotate refresh token

**Logout:**
1. Client sends refresh token
2. System revokes refresh token in database

### Rate Limiting Strategy
- Use `slowapi` (FastAPI wrapper around `limits`)
- Storage: In-memory (Redis later for production)
- Limits:
  - Global: 1000 requests/minute per IP
  - User: 100 requests/minute per authenticated user
  - Auth endpoints: 10 requests/minute per IP (login, register)

### Security Headers
```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000; includeSubDomains
Content-Security-Policy: default-src 'self'
```

## Implementation Plan

### Phase 1.1: Core Authentication Setup
1. Install authentication dependencies
2. Create User models (SQLAlchemy)
3. Setup password hashing utilities
4. Implement JWT token generation/validation
5. Create authentication configuration

### Phase 1.2: Email/Password Authentication
1. Create registration endpoint
2. Create login endpoint
3. Implement refresh token mechanism
4. Create logout endpoint
5. Add authentication middleware/dependency

### Phase 1.3: Security Hardening
1. Configure CORS middleware
2. Implement rate limiting
3. Add security headers middleware
4. Input validation enhancement
5. Error handling improvement

### Phase 1.4: Testing & Documentation
1. Write unit tests for authentication
2. Test rate limiting
3. Update API documentation
4. Create user guide

### Phase 1.5: Testing & Documentation
1. Write unit tests for authentication
2. Test OAuth flows
3. Test rate limiting
4. Update API documentation
5. Create user guide

## Success Criteria

- [ ] Users can register with email/password
- [ ] Users can login and receive JWT tokens
- [ ] Token refresh works correctly
- [ ] Logout revokes refresh token
- [ ] Rate limiting prevents abuse
- [ ] CORS configured properly
- [ ] Security headers present
- [ ] All tests pass
- [ ] Documentation updated

## Security Considerations

### Data Protection
- Passwords hashed with bcrypt (cost factor 12)
- JWT secrets stored in environment variables
- Refresh tokens hashed before storage
- HTTPS required for production

### Threat Mitigation
- Rate limiting prevents brute force
- Input validation prevents injection
- CORS prevents unauthorized origins
- Secure headers prevent XSS/Clickjacking
- Token expiration limits exposure window

### Known Limitations (Phase 1)
- No email verification required
- No password reset functionality (Phase 2)
- No two-factor authentication (Phase 2)
- No audit logging (Phase 2)
- No account deletion (Phase 2)

## Dependencies

### Required Environment Variables
```
JWT_SECRET_KEY=<random-256-bit-key>
```

## Rollback Plan

If authentication causes issues:
1. Revert to current state (no auth required)
2. Disable OAuth endpoints
3. Remove authentication middleware
4. Database migrations can be rolled back via Alembic

## Future Enhancements (Phase 2+)

- Email verification
- Password reset functionality
- OAuth 2.0 providers (ORCID, Google)
- Two-factor authentication
- API key generation for power users
- Advanced rate limiting with Redis
- Audit logging
- Account management (delete, export data)
- Session management UI
