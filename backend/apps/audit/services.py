"""Helper to record audit events from anywhere in the codebase.

Call record_event() from the review approve/reject actions, the activity
edit path, and the ingestion pipeline so the trail is complete without
scattering AuditEvent.objects.create everywhere.
"""
from .models import AuditEvent


def record_event(*, organization, actor, action, target, changes=None) -> AuditEvent:
    return AuditEvent.objects.create(
        organization=organization,
        actor=actor,
        action=action,
        target_model=f"{target._meta.app_label}.{target.__class__.__name__}",
        target_id=str(target.pk),
        changes=changes or {},
    )
