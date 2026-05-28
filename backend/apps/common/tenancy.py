"""Single source of truth for resolving the active tenant + role per request.

Auth happens inside the view (JWT/Token), so `request.user` is anonymous when
middleware runs — we resolve the tenant here, after authentication. Both the
viewset mixin and the role permission use this so the rules can't drift apart.
"""
from rest_framework.exceptions import NotAuthenticated, PermissionDenied


def resolve_membership(request):
    """Return the Membership for the active org, validated against the user.

    Reads the `X-Organization` header and checks the user actually belongs to
    that org; falls back to the user's first membership when the header is
    absent. Raises NotAuthenticated / PermissionDenied (never returns None).
    """
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        raise NotAuthenticated()

    memberships = user.memberships.select_related("organization")
    org_id = request.headers.get("X-Organization")
    if org_id:
        membership = memberships.filter(organization_id=org_id).first()
        if membership is None:
            raise PermissionDenied("Not a member of the requested organization.")
        return membership

    membership = memberships.first()
    if membership is None:
        raise PermissionDenied("User has no organization membership.")
    return membership
