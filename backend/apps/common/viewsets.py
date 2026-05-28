"""Tenant-scoping mixin for viewsets.

Resolving the tenant in middleware doesn't work cleanly with token/JWT auth —
DRF authenticates inside the view, so `request.user` is still anonymous when
middleware runs. Instead we resolve it here (and in the role permission) via
`apps.common.tenancy.resolve_membership`: read the `X-Organization` header,
validate it against the user's memberships, fall back to the first membership.

Every tenant-scoped viewset inherits this and filters by `self.organization`,
so cross-tenant reads are impossible by construction. Role enforcement is
layered on via OrgRolePermission (reads: any member; writes: analyst/admin,
overridable per view with `write_roles`).
"""
from rest_framework.permissions import IsAuthenticated

from apps.common.permissions import OrgRolePermission
from apps.common.tenancy import resolve_membership


class TenantViewSetMixin:
    permission_classes = [IsAuthenticated, OrgRolePermission]

    @property
    def membership(self):
        return resolve_membership(self.request)

    @property
    def organization(self):
        return self.membership.organization

    def perform_create(self, serializer):
        # Stamp the active tenant (and author, when the model supports it).
        extra = {"organization": self.organization}
        if any(f.name == "created_by" for f in serializer.Meta.model._meta.fields):
            extra["created_by"] = self.request.user
        serializer.save(**extra)
