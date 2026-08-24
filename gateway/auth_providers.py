"""Authentication provider abstraction (local JWT now, OIDC later)."""
from __future__ import annotations

import os
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from fastapi import HTTPException


class AuthenticationProvider(ABC):
    @abstractmethod
    def login(self, username: str, password: str) -> dict[str, Any]:
        ...

    @abstractmethod
    def authenticate(self, token: str) -> dict[str, Any]:
        ...


class LocalJWTProvider(AuthenticationProvider):
    def __init__(self):
        env = os.environ.get("FCQF_ENV", "development")
        secret = os.environ.get("JWT_SECRET", "")
        weak = secret in {"", "fcqf-dev-secret-change-me", "replace-with-long-random-string"}
        demo = os.environ.get("ALLOW_DEMO_USERS", "1") == "1"
        if env == "production" and weak and not demo:
            raise RuntimeError("JWT_SECRET must be set to a strong value in production")
        self.secret = secret or "fcqf-dev-secret-change-me"
        self.alg = os.environ.get("JWT_ALG", "HS256")
        if env == "production" and os.environ.get("ALLOW_DEMO_USERS", "0") != "1":
            # Production must supply real user store; demo passwords disabled.
            self.users = {}
        else:
            self.users = {
            "researcher": {"password": os.environ.get("USER_RESEARCHER_PASSWORD", "research123"), "role": "researcher", "purpose": "clinical_research"},
            "clinician": {"password": os.environ.get("USER_CLINICIAN_PASSWORD", "clinic123"), "role": "clinician", "purpose": "care_quality"},
            "auditor": {"password": os.environ.get("USER_AUDITOR_PASSWORD", "audit123"), "role": "auditor", "purpose": "compliance"},
            "steward": {"password": os.environ.get("USER_STEWARD_PASSWORD", "steward123"), "role": "data_steward", "purpose": "operations"},
            "admin": {"password": os.environ.get("USER_ADMIN_PASSWORD", "admin123"), "role": "admin", "purpose": "administration"},
        }

    def login(self, username: str, password: str) -> dict[str, Any]:
        rec = self.users.get(username)
        if not rec or rec["password"] != password:
            raise HTTPException(401, "invalid credentials")
        token = jwt.encode(
            {
                "sub": username,
                "role": rec["role"],
                "purpose": rec["purpose"],
                "iss": "fcqf-local",
                "exp": datetime.now(timezone.utc) + timedelta(hours=8),
            },
            self.secret,
            algorithm=self.alg,
        )
        return {"access_token": token, "token_type": "bearer", "role": rec["role"], "username": username, "provider": "local"}

    def authenticate(self, token: str) -> dict[str, Any]:
        try:
            return jwt.decode(token, self.secret, algorithms=[self.alg])
        except jwt.PyJWTError:
            raise HTTPException(401, "invalid token")


class OIDCProvider(AuthenticationProvider):
    """Placeholder for future OIDC/OAuth2 (authorization-code + JWKS validation)."""

    def __init__(self):
        self.issuer = os.environ.get("OIDC_ISSUER", "")
        self.audience = os.environ.get("OIDC_AUDIENCE", "")
        self.jwks_url = os.environ.get("OIDC_JWKS_URL", "")

    def login(self, username: str, password: str) -> dict[str, Any]:
        raise HTTPException(
            501,
            "OIDC login is not enabled. Set AUTH_PROVIDER=local or complete OIDC configuration.",
        )

    def authenticate(self, token: str) -> dict[str, Any]:
        if not self.jwks_url:
            raise HTTPException(501, "OIDC JWKS is not configured")
        raise HTTPException(501, "OIDC token validation is not implemented in this MVP")


def build_provider() -> AuthenticationProvider:
    kind = os.environ.get("AUTH_PROVIDER", "local").lower()
    if kind == "oidc":
        return OIDCProvider()
    return LocalJWTProvider()
