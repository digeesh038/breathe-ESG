"""Domain-level exceptions raised by ingestion and normalization.

Distinguishing these lets the pipeline record *why* a row failed (bad unit
vs unknown plant code vs malformed date) instead of a generic 500, which is
what the review dashboard surfaces to the analyst.
"""
import logging

from rest_framework.views import exception_handler as drf_default_handler

logger = logging.getLogger("apps.errors")


class IngestionError(Exception):
    """Base class for recoverable, row-level ingestion problems."""


class UnknownUnitError(IngestionError):
    pass


class UnmappedCodeError(IngestionError):
    """Plant code / cost center / airport code not found in reference tables."""


class MissingEmissionFactorError(IngestionError):
    pass


def drf_exception_handler(exc, context):
    """Consistent JSON error envelope across the API.

    DRF's default handler covers known API exceptions (validation, auth, perms)
    and returns their normal body. For anything it doesn't handle (an unexpected
    500), we log it and return a clean `{"detail": ...}` instead of leaking a
    stack trace / HTML error page to API clients.
    """
    response = drf_default_handler(exc, context)
    if response is not None:
        # Normalize to always carry a top-level "detail" for the SPA.
        if isinstance(response.data, dict) and "detail" not in response.data:
            response.data = {"detail": response.data}
        return response

    view = context.get("view")
    logger.exception("Unhandled API error in %s: %s", getattr(view, "__class__", view), exc)
    from rest_framework.response import Response

    return Response({"detail": "Internal server error."}, status=500)
