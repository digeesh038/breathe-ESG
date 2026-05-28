"""End-to-end ingestion: SAP CSV bytes -> ActivityRecords + ReviewItems + flags."""
import pytest

from apps.emissions.models import ActivityRecord
from apps.ingestion.models import IngestionBatch, RawRecord
from apps.ingestion.services.pipeline import run_batch
from apps.reference.models import EmissionFactor, PlantCode
from apps.review.models import AnomalyFlag, ReviewItem

pytestmark = pytest.mark.django_db

SAP_CSV = (
    "Material;Menge;Einheit;Buchungsdatum;Werk;Kostenstelle;Belegnummer\n"
    "F-DIESEL;1.000,50;L;15.03.2025;1010;CC1;DOC1\n"
    "F-DIESEL;-5,00;L;16.03.2025;1010;CC1;DOC2\n"  # invalid (negative) -> flagged
).encode("utf-8")


@pytest.fixture
def factor(db):
    return EmissionFactor.objects.create(
        activity_category="diesel", scope="1", unit="L",
        co2e_per_unit="2.68", region="", valid_year=2025, source="DEFRA 2025",
    )


def test_run_batch_creates_records_review_and_flags(org, sap_source, factor):
    PlantCode.objects.create(organization=org, code="1010", site_name="Plant A")
    batch = IngestionBatch.objects.create(organization=org, source=sap_source)

    run_batch(batch, SAP_CSV)
    batch.refresh_from_db()

    assert batch.status == IngestionBatch.Status.NORMALIZED
    assert RawRecord.objects.filter(batch=batch).count() == 2
    assert ActivityRecord.objects.filter(batch=batch).count() == 2
    assert ReviewItem.objects.filter(organization=org).count() == 2

    # First row computed CO2e from the factor (1000.50 L * 2.68).
    good = ActivityRecord.objects.get(batch=batch, activity_date="2025-03-15")
    assert good.activity_category == "diesel"
    assert float(good.co2e_kg) == pytest.approx(1000.50 * 2.68)

    # Second row (negative qty) is flagged invalid, not dropped.
    bad = ActivityRecord.objects.get(batch=batch, activity_date="2025-03-16")
    flags = AnomalyFlag.objects.filter(review_item__activity=bad).values_list("kind", flat=True)
    assert AnomalyFlag.Kind.INVALID_VALUE in set(flags)


def test_malformed_file_fails_batch_without_crashing(org, sap_source):
    batch = IngestionBatch.objects.create(organization=org, source=sap_source)
    run_batch(batch, b"\xff\xfe not a valid csv for this adapter")
    batch.refresh_from_db()
    # A parse failure marks the batch FAILED; it never raises.
    assert batch.status == IngestionBatch.Status.FAILED


def test_row_cap_rejects_oversized_file(org, sap_source, settings):
    settings.MAX_UPLOAD_ROWS = 1
    rows = "Material;Menge;Einheit;Buchungsdatum;Werk;Kostenstelle;Belegnummer\n"
    rows += "F-DIESEL;1,00;L;15.03.2025;1010;CC1;DOC1\n" * 5
    batch = IngestionBatch.objects.create(organization=org, source=sap_source)
    run_batch(batch, rows.encode("utf-8"))
    batch.refresh_from_db()
    assert batch.status == IngestionBatch.Status.FAILED
    assert "limit is 1" in batch.notes
