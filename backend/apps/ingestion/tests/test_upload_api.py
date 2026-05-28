"""Upload endpoint: validation, RBAC, and storage persistence."""
import io

import pytest

from apps.emissions.models import ActivityRecord
from apps.reference.models import EmissionFactor

pytestmark = pytest.mark.django_db


def _csv_file(name="sap.csv"):
    content = (
        "Material;Menge;Einheit;Buchungsdatum;Werk;Kostenstelle;Belegnummer\n"
        "F-DIESEL;1.000,50;L;15.03.2025;1010;CC1;DOC1\n"
    ).encode("utf-8")
    f = io.BytesIO(content)
    f.name = name
    return f


def test_analyst_upload_runs_pipeline_and_persists_file(auth_client, analyst, org, sap_source):
    EmissionFactor.objects.create(activity_category="diesel", scope="1", unit="L",
                                  co2e_per_unit="2.68", region="", valid_year=2025, source="DEFRA 2025")
    resp = auth_client(analyst, org).post(
        "/api/v1/ingestion/batches/upload/",
        {"source": sap_source.id, "file": _csv_file()},
        format="multipart",
    )
    assert resp.status_code == 201
    assert resp.data["status"] == "normalized"
    assert ActivityRecord.objects.filter(organization=org).count() == 1


def test_upload_rejects_unsupported_extension(auth_client, analyst, org, sap_source):
    bad = io.BytesIO(b"nope")
    bad.name = "payload.exe"
    resp = auth_client(analyst, org).post(
        "/api/v1/ingestion/batches/upload/",
        {"source": sap_source.id, "file": bad},
        format="multipart",
    )
    assert resp.status_code == 400


def test_viewer_cannot_upload(auth_client, viewer, org, sap_source):
    resp = auth_client(viewer, org).post(
        "/api/v1/ingestion/batches/upload/",
        {"source": sap_source.id, "file": _csv_file()},
        format="multipart",
    )
    assert resp.status_code == 403


def test_admin_only_source_creation(auth_client, analyst, admin, org):
    payload = {"name": "New SAP", "source_type": "sap", "config": {}}
    # analyst is blocked from creating sources...
    denied = auth_client(analyst, org).post("/api/v1/ingestion/sources/", payload, format="json")
    assert denied.status_code == 403
    # ...admin is allowed.
    ok = auth_client(admin, org).post("/api/v1/ingestion/sources/", payload, format="json")
    assert ok.status_code == 201
