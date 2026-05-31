from __future__ import annotations

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import get_settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        settings = get_settings()

        # Basic security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        # X-XSS-Protection is deprecated and can introduce vulnerabilities in
        # older browsers (https://owasp.org/www-project-secure-headers/).
        # CSP frame-ancestors + script-src is the modern replacement.
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"

        # HSTS (only in production with HTTPS)
        if settings.app_env == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        # Content Security Policy (adjusted for external APIs and development)
        if settings.app_env == "production":
            # Frontend tidak panggil external API langsung — semua via /api/v1/*.
            # Karena itu connect-src strict 'self' aja. Kalau nantinya butuh
            # CDN/analytics, tambahkan di sini eksplisit.
            csp_directives = [
                "default-src 'self'",
                "script-src 'self'",
                "style-src 'self' 'unsafe-inline'",  # Tailwind butuh unsafe-inline
                "img-src 'self' data: blob:",
                "font-src 'self' data:",
                "connect-src 'self'",
                "frame-ancestors 'none'",
                "base-uri 'self'",
                "form-action 'self'",
                "object-src 'none'",
                "upgrade-insecure-requests",
            ]
        else:
            # Development: Vite HMR butuh ws:, eval untuk module loader
            csp_directives = [
                "default-src 'self'",
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
                "style-src 'self' 'unsafe-inline'",
                "img-src 'self' data: blob: https:",
                "font-src 'self' data:",
                "connect-src 'self' ws: wss: http://localhost:* https:",
                "frame-ancestors 'none'",
                "object-src 'none'",
            ]

        response.headers["Content-Security-Policy"] = "; ".join(csp_directives)

        # Permissions Policy (formerly Feature-Policy)
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=(), payment=(), usb=(), magnetometer=(), gyroscope=(), accelerometer=()"
        )

        return response
