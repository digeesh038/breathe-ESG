"""Seed a demo tenant and ingest the sample files through the real pipeline.

Run:  python manage.py seed_demo

Idempotent for reference data (get_or_create). Ingestion runs only if the org
has no batches yet, so re-running won't duplicate records. After ingesting it
locks a few clean rows and rejects a flagged one so the review dashboard shows
a realistic spread across Pending / Locked / Rejected.
"""
from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.audit.services import record_event
from apps.ingestion.models import IngestionBatch, SourceConnection
from apps.ingestion.services.pipeline import run_batch
from apps.reference.models import AirportCode, EmissionFactor, PlantCode
from apps.review.models import ReviewItem
from apps.tenants.models import Membership, Organization

User = get_user_model()

SAMPLE_DIR = settings.BASE_DIR / "sample_data"

# kg CO2e per canonical unit (illustrative DEFRA/IEA-style values — see SOURCES.md).
FACTORS = [
    ("diesel", "1", "L", "2.68", ""),
    ("petrol", "1", "L", "2.31", ""),
    ("natural_gas", "1", "m3", "2.04", ""),
    ("grid_electricity", "2", "kWh", "0.207", ""),
    ("grid_electricity", "2", "kWh", "0.380", "DE"),
    ("flight_short_haul", "3", "km", "0.158", ""),
    ("flight_long_haul", "3", "km", "0.195", ""),
    ("rail", "3", "km", "0.035", ""),
    ("ground_taxi", "3", "km", "0.170", ""),
    ("hotel_night", "3", "night", "10.40", ""),
    # NB: 'purchased_paper' has NO factor on purpose -> demonstrates missing_factor flag.
]

PLANT_CODES = [("1010", "Hamburg Plant", ""), ("1020", "Munich Plant", "DE")]
# NB: SAP code "2001" is intentionally left unmapped -> demonstrates unmapped_code flag.

AIRPORTS = [
    ("LHR", "London Heathrow", "51.4700", "-0.4543"),
    ("JFK", "New York JFK", "40.6413", "-73.7781"),
    ("MUC", "Munich", "48.3538", "11.7861"),
]

SOURCES = [
    ("Acme SAP export", "sap", {"delimiter": ";", "encoding": "utf-8-sig"}, "sap_fuel_procurement.csv"),
    ("Acme utility portal", "utility", {}, "utility_electricity.csv"),
    ("Acme corporate travel", "travel", {}, "travel_concur.json"),
]


class Command(BaseCommand):
    help = "Seed demo organizations and ingest the sample data."

    def handle(self, *args, **options):
        admin = User.objects.filter(is_superuser=True).first()
        if not admin:
            self.stdout.write(self.style.WARNING("No superuser found. Please run createsuperuser first or make sure one exists."))
            return

        # Seed global reference data first
        for cat, scope, unit, val, region in FACTORS:
            EmissionFactor.objects.get_or_create(
                activity_category=cat, region=region, valid_year=2025, source="DEFRA 2024",
                defaults={"scope": scope, "unit": unit, "co2e_per_unit": Decimal(val)},
            )
        for iata, name, lat, lon in AIRPORTS:
            AirportCode.objects.get_or_create(
                iata=iata, defaults={"name": name, "latitude": Decimal(lat), "longitude": Decimal(lon)}
            )
        self.stdout.write("Global reference data ready.")

        # Seed organizations
        orgs_data = [
            ("acme", "Acme Manufacturing"),
            ("tesla", "Tesla Manufacturing"),
            ("abc", "ABC Logistics"),
        ]

        for slug, org_name in orgs_data:
            org, _ = Organization.objects.get_or_create(
                slug=slug, defaults={"name": org_name}
            )
            self.stdout.write(f"Organization: {org.name}")

            # Make every existing user a member so anyone can log in and review.
            for user in User.objects.all():
                Membership.objects.get_or_create(
                    user=user, organization=org, defaults={"role": Membership.Role.ANALYST}
                )

            # Plant codes for this org
            for code, name, region in PLANT_CODES:
                PlantCode.objects.get_or_create(
                    organization=org, code=code, defaults={"site_name": name, "region": region}
                )

            if IngestionBatch.objects.filter(organization=org).exists():
                self.stdout.write(self.style.WARNING(f"  Batches already exist for {org.name} — skipping ingestion."))
                continue

            for name, stype, config, filename in SOURCES:
                source, _ = SourceConnection.objects.get_or_create(
                    organization=org, name=f"{org_name} {name.split(' ', 1)[1]}", defaults={"source_type": stype, "config": config}
                )
                path = SAMPLE_DIR / filename
                batch = IngestionBatch.objects.create(
                    organization=org, source=source, created_by=admin, original_filename=filename
                )
                run_batch(batch, path.read_bytes())
                batch.refresh_from_db()
                self.stdout.write(
                    f"  {filename}: {batch.status}, {batch.row_count} rows, {batch.error_count} errors"
                )

            self._simulate_review(org, admin)

        self.stdout.write(self.style.SUCCESS("Seed complete."))

    def _simulate_review(self, org, admin):
        items = list(
            ReviewItem.objects.filter(organization=org).prefetch_related("flags").order_by("id")
        )
        clean = [i for i in items if not i.flags.exists()]
        flagged = [i for i in items if i.flags.exists()]

        for item in clean[:3]:
            item.status = ReviewItem.Status.LOCKED
            item.reviewed_by = admin
            item.reviewed_at = timezone.now()
            item.save(update_fields=["status", "reviewed_by", "reviewed_at"])
            record_event(organization=org, actor=admin, action="locked",
                         target=item.activity, changes={"review_status": "locked"})

        if flagged:
            item = flagged[0]
            item.status = ReviewItem.Status.REJECTED
            item.reviewed_by = admin
            item.reviewed_at = timezone.now()
            item.comment = "Rejected pending source correction."
            item.save(update_fields=["status", "reviewed_by", "reviewed_at", "comment"])
            record_event(organization=org, actor=admin, action="rejected",
                         target=item.activity, changes={"review_status": "rejected"})
