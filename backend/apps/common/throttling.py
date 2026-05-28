"""Dedicated throttle scopes for sensitive endpoints.

Login is rate-limited by client IP (brute-force guard); upload by user when
authenticated (ingestion spam guard). Rates live in
settings.REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'].
"""
from rest_framework.throttling import SimpleRateThrottle


class AuthThrottle(SimpleRateThrottle):
    scope = "auth"

    def get_cache_key(self, request, view):
        return self.cache_format % {"scope": self.scope, "ident": self.get_ident(request)}


class UploadThrottle(SimpleRateThrottle):
    scope = "upload"

    def get_cache_key(self, request, view):
        user = getattr(request, "user", None)
        ident = user.pk if user and user.is_authenticated else self.get_ident(request)
        return self.cache_format % {"scope": self.scope, "ident": ident}
