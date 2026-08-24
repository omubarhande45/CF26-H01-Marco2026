"""Service-to-service authentication abstraction (HMAC tokens now; mTLS/OIDC later)."""
from __future__ import annotations

import hashlib
import hmac
import os
import time
from abc import ABC, abstractmethod


class ServiceAuthenticator(ABC):
    @abstractmethod
    def issue(self, audience: str, extra: dict | None = None) -> dict[str, str]:
        ...

    @abstractmethod
    def verify(self, headers: dict, expected_audience: str | None = None) -> bool:
        ...


class SharedTokenAuthenticator(ServiceAuthenticator):
    """HMAC of (audience:timestamp) with SERVICE_TOKEN. Not mTLS — documented as a stand-in."""

    def __init__(self):
        self.secret = os.environ.get("SERVICE_TOKEN", "")
        self.required = os.environ.get("FCQF_ENV", "development") == "production" or os.environ.get(
            "REQUIRE_SERVICE_AUTH", "0"
        ) == "1"

    def issue(self, audience: str, extra: dict | None = None) -> dict[str, str]:
        ts = str(int(time.time()))
        if not self.secret:
            return {}
        mac = hmac.new(self.secret.encode(), f"{audience}:{ts}".encode(), hashlib.sha256).hexdigest()
        return {"X-FCQF-Service-Token": mac, "X-FCQF-Service-Ts": ts, "X-FCQF-Service-Aud": audience}

    def verify(self, headers: dict, expected_audience: str | None = None) -> bool:
        if not self.secret:
            return not self.required
        token = headers.get("x-fcqf-service-token") or headers.get("X-FCQF-Service-Token")
        ts = headers.get("x-fcqf-service-ts") or headers.get("X-FCQF-Service-Ts")
        aud = headers.get("x-fcqf-service-aud") or headers.get("X-FCQF-Service-Aud")
        if not token or not ts:
            return False
        try:
            if abs(time.time() - int(ts)) > 300:
                return False
        except ValueError:
            return False
        if expected_audience and aud and aud != expected_audience:
            return False
        expect = hmac.new(self.secret.encode(), f"{aud or expected_audience or ''}:{ts}".encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(expect, token)


class MTLSAuthenticator(ServiceAuthenticator):
    """Future production path — not implemented in this simulation."""

    def issue(self, audience: str, extra: dict | None = None) -> dict[str, str]:
        raise NotImplementedError("mTLS is a production deployment concern")

    def verify(self, headers: dict, expected_audience: str | None = None) -> bool:
        raise NotImplementedError("mTLS is a production deployment concern")


def build_service_auth() -> ServiceAuthenticator:
    kind = os.environ.get("SERVICE_AUTH", "token").lower()
    if kind == "mtls":
        return MTLSAuthenticator()
    return SharedTokenAuthenticator()
