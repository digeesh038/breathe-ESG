"""RBAC + review workflow: who can approve/reject/edit, and locking."""
import pytest

from apps.audit.models import AuditEvent
from apps.review.models import ReviewItem

pytestmark = pytest.mark.django_db


def test_analyst_can_approve_and_it_locks(auth_client, analyst, org, sap_source, make_activity, review_for):
    activity = make_activity(sap_source)
    item = review_for(activity)

    resp = auth_client(analyst, org).post(f"/api/v1/review/items/{item.id}/approve/")
    assert resp.status_code == 200
    item.refresh_from_db()
    assert item.status == ReviewItem.Status.LOCKED
    assert item.reviewed_by_id == analyst.id
    # Approval writes an audit event.
    assert AuditEvent.objects.filter(organization=org, action="locked").exists()


def test_viewer_cannot_approve(auth_client, viewer, org, sap_source, make_activity, review_for):
    activity = make_activity(sap_source)
    item = review_for(activity)

    resp = auth_client(viewer, org).post(f"/api/v1/review/items/{item.id}/approve/")
    assert resp.status_code == 403
    item.refresh_from_db()
    assert item.status == ReviewItem.Status.PENDING


def test_viewer_can_read_review_queue(auth_client, viewer, org, sap_source, make_activity, review_for):
    review_for(make_activity(sap_source))
    resp = auth_client(viewer, org).get("/api/v1/review/items/")
    assert resp.status_code == 200
    assert resp.data["count"] == 1


def test_locked_record_cannot_be_edited(auth_client, analyst, org, sap_source, make_activity, review_for):
    activity = make_activity(sap_source, quantity="100")
    item = review_for(activity)
    auth_client(analyst, org).post(f"/api/v1/review/items/{item.id}/approve/")

    resp = auth_client(analyst, org).patch(
        f"/api/v1/emissions/activities/{activity.id}/", {"quantity": "200"}, format="json"
    )
    assert resp.status_code == 403


def test_analyst_edit_recomputes_co2e(auth_client, analyst, org, sap_source, make_activity, diesel_factor):
    activity = make_activity(sap_source, quantity="100", factor=diesel_factor)
    resp = auth_client(analyst, org).patch(
        f"/api/v1/emissions/activities/{activity.id}/", {"quantity": "200"}, format="json"
    )
    assert resp.status_code == 200
    activity.refresh_from_db()
    assert activity.is_edited is True
    assert float(activity.co2e_kg) == pytest.approx(200 * 2.68)
