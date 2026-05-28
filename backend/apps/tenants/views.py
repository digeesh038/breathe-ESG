from django.contrib.auth import authenticate
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.common.throttling import AuthThrottle

from .models import Organization
from .serializers import OrganizationSerializer


def _org_payload(user):
    """The orgs a user can act in, with their role — drives the SPA's org switcher."""
    return [
        {
            "id": m.organization_id,
            "name": m.organization.name,
            "slug": m.organization.slug,
            "role": m.role,
        }
        for m in user.memberships.select_related("organization")
    ]


def _issue_tokens(user):
    """Mint an access+refresh pair. Refresh is rotated by SimpleJWT settings."""
    refresh = RefreshToken.for_user(user)
    return {"access": str(refresh.access_token), "refresh": str(refresh)}


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([AuthThrottle])
def login_view(request):
    """Exchange username/password for a JWT pair + the user's organizations."""
    username = request.data.get("username")
    password = request.data.get("password")
    user = authenticate(username=username, password=password)
    if user is None:
        return Response(
            {"detail": "Invalid credentials."}, status=status.HTTP_400_BAD_REQUEST
        )
    tokens = _issue_tokens(user)
    return Response(
        {
            **tokens,
            "user": {"id": user.id, "username": user.username},
            "organizations": _org_payload(user),
        }
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """Blacklist the supplied refresh token so it can't be used again.

    Requires `rest_framework_simplejwt.token_blacklist`. Access tokens remain
    valid until they expire (short-lived by design); the refresh token is the
    long-lived credential we revoke here.
    """
    refresh = request.data.get("refresh")
    if not refresh:
        return Response(
            {"detail": "A refresh token is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        RefreshToken(refresh).blacklist()
    except TokenError:
        return Response(
            {"detail": "Token is invalid or already blacklisted."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    return Response(status=status.HTTP_205_RESET_CONTENT)


@api_view(["GET"])
def me_view(request):
    """Current user + organizations (used on app load to restore session)."""
    return Response(
        {
            "user": {"id": request.user.id, "username": request.user.username},
            "organizations": _org_payload(request.user),
        }
    )


class OrganizationViewSet(viewsets.ReadOnlyModelViewSet):
    """Orgs the current user belongs to."""

    serializer_class = OrganizationSerializer

    def get_queryset(self):
        return Organization.objects.filter(memberships__user=self.request.user)
