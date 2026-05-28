"""Append-only audit trail.

Every state change auditors care about (row created, value edited, approved,
locked, rejected) is recorded as an immutable AuditEvent. We store a generic
reference (model + object id) plus a before/after diff so the trail survives
even if the target row is later deleted. Rows here are never updated or
deleted — that's the whole point.
"""
from django.conf import settings
from django.db import models

from apps.common.models import TenantScopedModel


class AuditEvent(TenantScopedModel):
    class Action(models.TextChoices):
        CREATED = "created", "Created"
        EDITED = "edited", "Edited"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        LOCKED = "locked", "Locked"

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="+"
    )
    action = models.CharField(max_length=16, choices=Action.choices)
    target_model = models.CharField(max_length=64)   # e.g. "emissions.ActivityRecord"
    target_id = models.CharField(max_length=64)
    changes = models.JSONField(default=dict, blank=True)  # {field: [before, after]}
    occurred_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-occurred_at"]
