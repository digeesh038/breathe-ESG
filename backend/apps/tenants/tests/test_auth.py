"""Auth flow: JWT login, refresh, logout/blacklist, and me."""
import pytest
from rest_framework.test import APIClient

from apps.tenants.models import Membership

pytestmark = pytest.mark.django_db


def test_login_returns_jwt_pair_and_orgs(analyst, org):
    client = APIClient()
    resp = client.post(
        "/api/v1/tenants/auth/login/",
        {"username": analyst.username, "password": "testpass12345"},
        format="json",
    )
    assert resp.status_code == 200
    assert "access" in resp.data and "refresh" in resp.data
    assert resp.data["organizations"][0]["id"] == org.id
    assert resp.data["organizations"][0]["role"] == Membership.Role.ANALYST


def test_login_rejects_bad_credentials(analyst):
    client = APIClient()
    resp = client.post(
        "/api/v1/tenants/auth/login/",
        {"username": analyst.username, "password": "wrong"},
        format="json",
    )
    assert resp.status_code == 400


def test_me_requires_auth():
    assert APIClient().get("/api/v1/tenants/auth/me/").status_code == 401


def test_me_returns_user_and_orgs(auth_client, analyst, org):
    resp = auth_client(analyst, org).get("/api/v1/tenants/auth/me/")
    assert resp.status_code == 200
    assert resp.data["user"]["username"] == analyst.username


def test_logout_blacklists_refresh_token(analyst):
    client = APIClient()
    login = client.post(
        "/api/v1/tenants/auth/login/",
        {"username": analyst.username, "password": "testpass12345"},
        format="json",
    )
    refresh = login.data["refresh"]
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

    out = client.post("/api/v1/tenants/auth/logout/", {"refresh": refresh}, format="json")
    assert out.status_code == 205

    # The blacklisted refresh can no longer be exchanged for a new access token.
    again = APIClient().post("/api/v1/tenants/auth/refresh/", {"refresh": refresh}, format="json")
    assert again.status_code == 401
