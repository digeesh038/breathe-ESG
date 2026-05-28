"""Abstract base models reused across apps.

These encode three cross-cutting concerns that the assignment calls out:
multi-tenancy, timestamps, and soft source-of-truth tracking. Keeping them
abstract (no table of their own) means every concrete model opts in by
inheritance rather than copy-pasting fields.
"""
from django.conf import settings
from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class TenantScopedModel(TimeStampedModel):
    """Every row belongs to exactly one Organization (tenant).

    Multi-tenancy here is row-level (a tenant FK + filtered querysets via
    middleware), not schema- or database-per-tenant. See MODEL.md for why
    that tradeoff fits a prototype with shared analysts.
    """

    organization = models.ForeignKey(
        "tenants.Organization",
        on_delete=models.CASCADE,
        related_name="%(class)s_set",
    )

    class Meta:
        abstract = True


class AuthoredModel(models.Model):
    """Tracks who last touched a row — feeds the audit trail."""

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )

    class Meta:
        abstract = True
