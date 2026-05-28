"""Cross-tenant access must be impossible, by construction."""
import pytest

from apps.tenants.models import Membership

pytestmark = pytest.mark.django_db


def test_member_cannot_use_org_they_dont_belong_to(auth_client, analyst, org_b):
    # analyst belongs to `org`, not `org_b`; passing org_b's id is rejected.
    resp = auth_client(analyst, org_b).get("/api/v1/emissions/activities/")
    assert resp.status_code == 403


def test_queryset_is_scoped_to_active_org(
    auth_client, analyst, org, org_b, sap_source, make_activity
):
    make_activity(sap_source, site_code="1010")  # belongs to `org`

    # A user in org_b must not see org's record.
    other = analyst.__class__.objects.create(username="org-b-user")
    other.set_password("testpass12345")
    other.save()
    Membership.objects.create(user=other, organization=org_b)

    mine = auth_client(analyst, org).get("/api/v1/emissions/activities/")
    assert mine.status_code == 200
    assert {r["site_code"] for r in mine.data["results"]} == {"1010"}

    theirs = auth_client(other, org_b).get("/api/v1/emissions/activities/")
    assert theirs.status_code == 200
    assert theirs.data["results"] == []
