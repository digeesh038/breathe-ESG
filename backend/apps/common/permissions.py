"""Shared DRF permissions.

Two rules, enforced together on every tenant-scoped viewset:
  1. A user may only see/act on rows in an organization they belong to.
  2. Writes require a role that's allowed to write (analyst/admin by default);
     `viewer` is read-only. A viewset can tighten this via `write_roles`
     (e.g. source management is admin-only).
"""
from rest_framework.permissions import SAFE_METHODS, BasePermission

from apps.common.tenancy import resolve_membership

# Roles permitted to perform write operations by default.
DEFAULT_WRITE_ROLES = frozenset({"analyst", "admin"})


class OrgRolePermission(BasePermission):
    """Membership + role gate. Reads: any member. Writes: `view.write_roles`."""

    message = "Your role does not permit this action."

    def has_permission(self, request, view) -> bool:
        # Raises if the user isn't an authenticated member of the active org.
        membership = resolve_membership(request)
        request._membership = membership  # cache for the view / object check

        if request.method in SAFE_METHODS:
            return True

        write_roles = getattr(view, "write_roles", DEFAULT_WRITE_ROLES)
        return membership.role in write_roles

    def has_object_permission(self, request, view, obj) -> bool:
        # Defense in depth: querysets are already org-filtered, but double-check
        # the object belongs to the active org before any write.
        membership = getattr(request, "_membership", None) or resolve_membership(request)
        obj_org_id = getattr(obj, "organization_id", None)
        if obj_org_id is not None and obj_org_id != membership.organization_id:
            return False
        if request.method in SAFE_METHODS:
            return True
        write_roles = getattr(view, "write_roles", DEFAULT_WRITE_ROLES)
        return membership.role in write_roles


class IsOrganizationMember(BasePermission):
    """Object-level: the user must belong to the object's organization."""

    def has_object_permission(self, request, view, obj) -> bool:
        membership = resolve_membership(request)
        obj_org_id = getattr(obj, "organization_id", None)
        return obj_org_id is None or obj_org_id == membership.organization_id
