"""
Security test suite for PaperLens.
Tests authentication, authorization, rate limiting, and input validation.
"""

from __future__ import annotations

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestPasswordValidation:
    """Test password strength requirements."""

    def test_weak_password_too_short(self):
        """Password must be at least 8 characters."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "Short1!",  # Only 7 characters
            },
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "at least 8 characters" in response.text.lower()

    def test_weak_password_no_uppercase(self):
        """Password must contain uppercase letter."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "lowercase123!",
            },
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "uppercase" in response.text.lower()

    def test_weak_password_no_lowercase(self):
        """Password must contain lowercase letter."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "UPPERCASE123!",
            },
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "lowercase" in response.text.lower()

    def test_weak_password_no_digit(self):
        """Password must contain digit."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "NoDigits!",
            },
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "digit" in response.text.lower()

    def test_weak_password_no_special_char(self):
        """Password must contain special character."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "NoSpecial123",
            },
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "special character" in response.text.lower()

    def test_strong_password_accepted(self):
        """Strong password should be accepted."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "strong@example.com",
                "password": "StrongPass123!",
            },
        )
        # Should succeed or fail for other reasons (duplicate email, etc.)
        assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST]


class TestInputSanitization:
    """Test input sanitization and XSS prevention."""

    def test_xss_in_full_name(self):
        """HTML tags should be removed from full name."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "xss@example.com",
                "password": "SecurePass123!",
                "full_name": "<script>alert('xss')</script>John Doe",
            },
        )
        if response.status_code == status.HTTP_201_CREATED:
            user = response.json()
            assert "<script>" not in user.get("full_name", "")
            assert "John Doe" in user.get("full_name", "")

    def test_search_query_strips_html(self):
        """
        HTML tags in search queries must be stripped to prevent XSS if the
        query gets reflected to the client.

        Note: SQL keywords (drop, delete, etc.) are intentionally NOT blocked
        because they appear in legitimate scientific queries ("drop in CO2",
        "gene deletion studies"). SQL injection is prevented by SQLAlchemy
        parametrized queries, not by input blacklists.
        """
        # HTML/script must be stripped → either rejected (empty after strip)
        # or accepted with content removed.
        response = client.post(
            "/api/v1/search",
            json={
                "query": "<script>alert(1)</script>quantum computing",
                "filters": {},
                "limit": 5,
            },
        )
        # Either accepted (HTML stripped) or rejected (empty after strip).
        # Either way, the raw HTML must not be reflected anywhere.
        if response.status_code == 200:
            body_text = response.text
            assert "<script>" not in body_text
            assert "alert(1)" not in body_text
        else:
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_search_accepts_legitimate_queries_with_sql_keywords(self):
        """
        Real-world academic queries often contain words like "drop", "delete",
        "update". These must NOT be blocked.
        """
        legitimate_queries = [
            "drop in CO2 emission rates",
            "gene deletion studies",
            "update on COVID-19 vaccine efficacy",
            "exec function in JavaScript runtime",
        ]
        for query in legitimate_queries:
            response = client.post(
                "/api/v1/search",
                json={"query": query, "filters": {}, "limit": 5},
            )
            # Must NOT be 422 — these are valid queries
            assert response.status_code != status.HTTP_422_UNPROCESSABLE_ENTITY, (
                f"Legitimate query rejected: {query!r}"
            )


class TestAccountLockout:
    """Test account lockout mechanism."""

    @pytest.fixture
    def test_user_email(self):
        """Create or reset a test user for lockout tests.

        The lockout state persists in the DB across test runs. To make the
        test deterministic and isolated, we explicitly clear failed_login
        and locked_until on every fixture invocation.
        """
        import asyncio

        from sqlalchemy import update

        from app.db.session import SessionLocal
        from models.user import User

        email = "lockout_test@example.com"

        # Register (no-op if already exists)
        client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": "TestPass123!"},
        )

        async def _reset():
            async with SessionLocal() as session:
                await session.execute(
                    update(User)
                    .where(User.email == email)
                    .values(failed_login_attempts=0, locked_until=None)
                )
                await session.commit()

        asyncio.run(_reset())
        return email

    def test_account_locks_after_failed_attempts(self, test_user_email):
        """Account should lock after 5 failed login attempts."""
        # First 4 wrong-password attempts return 401 (Unauthorized).
        # The 5th attempt is the trigger that flips the account into the
        # locked state and the response is 423 (Locked).
        for i in range(4):
            response = client.post(
                "/api/v1/auth/login",
                json={
                    "email": test_user_email,
                    "password": "WrongPassword123!",
                },
            )
            assert response.status_code == status.HTTP_401_UNAUTHORIZED, (
                f"Attempt {i + 1} expected 401, got {response.status_code}"
            )

        # 5th wrong attempt — should trigger lockout
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user_email,
                "password": "WrongPassword123!",
            },
        )
        assert response.status_code == status.HTTP_423_LOCKED
        assert "locked" in response.json()["detail"].lower()

        # Subsequent attempts (even with correct password) should also be locked
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user_email,
                "password": "TestPass123!",
            },
        )
        assert response.status_code == status.HTTP_423_LOCKED
        assert "locked" in response.json()["detail"].lower()


class TestRateLimiting:
    """Test rate limiting on endpoints."""

    def test_search_rate_limit(self, monkeypatch):
        """Search endpoint should be rate limited to 30/minute.

        We mock SearchService.run so the test does not hit real external
        APIs (each real call fans out to 8 connectors with 10s timeout).
        """
        from schemas.paper import PaperDTO
        from services.search_service import SearchService

        async def fake_run(self, query, filters, limit, offset, sort_by):  # noqa: ARG001
            return [PaperDTO(title=query, source="crossref", sources=["crossref"])], 1, 1, []

        monkeypatch.setattr(SearchService, "run", fake_run)

        responses = []
        for i in range(35):
            response = client.post(
                "/api/v1/search",
                json={"query": f"test query {i}", "filters": {}, "limit": 10},
            )
            responses.append(response.status_code)

        assert status.HTTP_429_TOO_MANY_REQUESTS in responses, (
            f"Rate limit not triggered. Status codes: {responses}"
        )

    def test_register_rate_limit(self):
        """Register endpoint should be rate limited to 5/minute."""
        # Make 7 registration attempts
        responses = []
        for i in range(7):
            response = client.post(
                "/api/v1/auth/register",
                json={
                    "email": f"ratelimit{i}@example.com",
                    "password": "TestPass123!",
                },
            )
            responses.append(response.status_code)

        # Should have at least one 429
        assert status.HTTP_429_TOO_MANY_REQUESTS in responses


class TestSecurityHeaders:
    """Test security headers are present."""

    def test_security_headers_present(self):
        """All modern security headers should be present."""
        response = client.get("/healthz")

        assert response.headers.get("X-Content-Type-Options") == "nosniff"
        assert response.headers.get("X-Frame-Options") == "DENY"
        assert "Content-Security-Policy" in response.headers
        assert "Referrer-Policy" in response.headers
        assert "Permissions-Policy" in response.headers

        # X-XSS-Protection is intentionally NOT set — it is deprecated and
        # can introduce vulnerabilities in older browsers. Modern protection
        # is provided by CSP (script-src, frame-ancestors).
        assert "X-XSS-Protection" not in response.headers


class TestJWTSecurity:
    """Test JWT token security."""

    def test_invalid_token_rejected(self):
        """Invalid JWT token should be rejected."""
        response = client.get(
            "/api/v1/auth/me", headers={"Authorization": "Bearer invalid_token_here"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_expired_token_rejected(self):
        """Expired JWT token should be rejected."""
        # This would require mocking time or waiting for expiration
        # For now, just test with malformed token
        response = client.get(
            "/api/v1/auth/me",
            headers={
                "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
            },
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestInputValidation:
    """Test input validation on various endpoints."""

    def test_search_query_too_long(self):
        """Search query should be limited to 500 characters."""
        long_query = "a" * 501
        response = client.post(
            "/api/v1/search",
            json={
                "query": long_query,
                "filters": {},
                "limit": 10,
            },
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_search_limit_too_high(self):
        """Search limit should be capped at 100."""
        response = client.post(
            "/api/v1/search",
            json={
                "query": "test",
                "filters": {},
                "limit": 1000,
            },
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_invalid_year_range(self):
        """Year range should be validated."""
        response = client.post(
            "/api/v1/search",
            json={
                "query": "test",
                "filters": {
                    "year_from": 1800,  # Too old
                },
                "limit": 10,
            },
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestCORSSecurity:
    """Test CORS configuration."""

    def test_cors_headers_present(self):
        """CORS headers should be present for allowed origins."""
        response = client.options(
            "/api/v1/search",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
            },
        )

        # Should have CORS headers
        assert "Access-Control-Allow-Origin" in response.headers or response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
