"""Multi-tenancy primitives.

Organization is the tenant boundary. A custom User keeps auth simple while
Membership records which orgs a user belongs to and in what role — an
analyst at a consultancy like Breathe may review data for several client
orgs, so user<->org is many-to-many, not a single FK.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.common.models import TimeStampedModel


class Organization(TimeStampedModel):
    """A client company whose emissions data we ingest (the tenant)."""

    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class User(AbstractUser):
    """Custom user so we can attach org membership and roles later."""


class Membership(TimeStampedModel):
    class Role(models.TextChoices):
        ANALYST = "analyst", "Analyst"        # reviews & approves rows
        ADMIN = "admin", "Admin"              # manages sources/users
        VIEWER = "viewer", "Viewer"           # read-only (e.g. auditor)

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="memberships")
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="memberships"
    )
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.ANALYST)

    class Meta:
        unique_together = ("user", "organization")
