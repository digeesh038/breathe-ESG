"""pytest fixtures shared across app test packages.

Factory-boy factories + helpers so each test starts from a clean, explicit
baseline and tenant isolation / RBAC can be asserted directly. `auth_client`
returns a DRF APIClient authenticated as a given user with the active-org
header set, which is exactly how the SPA talks to the API.
"""
from datetime import date

import factory
import pytest
from rest_framework.test import APIClient

from apps.emissions.models import ActivityRecord
from apps.ingestion.models import IngestionBatch, RawRecord, SourceConnection
from apps.reference.models import EmissionFactor
from apps.review.models import ReviewItem
from apps.tenants.models import Membership, Organization, User


class OrganizationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Organization

    name = factory.Sequence(lambda n: f"Org {n}")
    slug = factory.Sequence(lambda n: f"org-{n}")


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        skip_postgeneration_save = True

    username = factory.Sequence(lambda n: f"user{n}")

    @factory.post_generation
    def password(obj, create, extracted, **kwargs):
        obj.set_password(extracted or "testpass12345")
        if create:
            obj.save()


@pytest.fixture
def org(db):
    return OrganizationFactory()


@pytest.fixture
def org_b(db):
    return OrganizationFactory()


def _member(org, role):
    user = UserFactory()
    Membership.objects.create(user=user, organization=org, role=role)
    return user


@pytest.fixture
def analyst(org):
    return _member(org, Membership.Role.ANALYST)


@pytest.fixture
def admin(org):
    return _member(org, Membership.Role.ADMIN)


@pytest.fixture
def viewer(org):
    return _member(org, Membership.Role.VIEWER)


@pytest.fixture
def auth_client():
    """Factory: auth_client(user, org) -> APIClient with JWT + org header."""
    def _make(user, organization=None):
        from rest_framework_simplejwt.tokens import RefreshToken

        client = APIClient()
        access = str(RefreshToken.for_user(user).access_token)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        if organization is not None:
            client.credentials(
                HTTP_AUTHORIZATION=f"Bearer {access}",
                HTTP_X_ORGANIZATION=str(organization.id),
            )
        return client

    return _make


@pytest.fixture
def diesel_factor(db):
    return EmissionFactor.objects.create(
        activity_category="diesel", scope="1", unit="L",
        co2e_per_unit="2.68", region="", valid_year=2025, source="DEFRA 2025",
    )


@pytest.fixture
def sap_source(org):
    return SourceConnection.objects.create(
        organization=org, name="Acme SAP", source_type="sap", config={},
    )


@pytest.fixture
def make_activity(org):
    """Factory for a normalized ActivityRecord (+ its raw/batch chain)."""
    def _make(source, *, category="diesel", scope="1", quantity="100",
              site_code="1010", activity_date=date(2025, 3, 15), factor=None):
        batch = IngestionBatch.objects.create(organization=org, source=source)
        raw = RawRecord.objects.create(
            organization=org, batch=batch, row_number=1, payload={}
        )
        record = ActivityRecord.objects.create(
            organization=org, raw_record=raw, batch=batch,
            activity_category=category, scope=scope, site_code=site_code,
            activity_date=activity_date, unit="L",
            original_quantity=quantity, quantity=quantity,
            emission_factor=factor,
        )
        # Re-read so field types match what the DB/serializers see (Decimal, etc.)
        record.refresh_from_db()
        return record

    return _make


@pytest.fixture
def review_for():
    def _make(activity):
        return ReviewItem.objects.create(
            organization=activity.organization, activity=activity
        )

    return _make
