"""Give each demo org a distinct emissions profile.

The seed ingests the same sample files into every org, so tenant switching
shows identical numbers and looks broken. This scales each org's quantities by
a per-tenant factor (from the original ingested value, so it's idempotent) and
recomputes CO2e — making the org dropdown visibly dynamic.

Run:  python manage.py vary_demo_data
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from apps.emissions.models import ActivityRecord
from apps.emissions.services.calculator import recalculate
from apps.tenants.models import Organization

# Per-tenant multiplier applied to the original ingested quantity.
SCALE = {
    "acme": Decimal("1.0"),
    "tesla": Decimal("0.45"),
    "abc": Decimal("1.85"),
}


class Command(BaseCommand):
    help = "Scale each demo org's quantities so tenant switching shows distinct data."

    def handle(self, *args, **options):
        for org in Organization.objects.all():
            factor = SCALE.get(org.slug, Decimal("1.0"))
            records = ActivityRecord.objects.filter(organization=org)
            for rec in records:
                # Always scale from the original quantity so re-running is idempotent.
                rec.quantity = (rec.original_quantity * factor).quantize(Decimal("0.0001"))
                rec.is_edited = factor != Decimal("1.0")
                recalculate(rec)
                rec.save(update_fields=["quantity", "is_edited", "co2e_kg", "emission_factor"])
            self.stdout.write(
                f"{org.name}: scaled {records.count()} records by x{factor}"
            )
        self.stdout.write(self.style.SUCCESS("Demo data differentiated per tenant."))
