"""Seed a demo tenant, an analyst user, emission factors, and lookup data,
then ingest the sample files so the deployed app has something to review.

Run: python manage.py shell < scripts/seed.py   (or wrap as a mgmt command)

Keep this realistic but minimal — the reviewer should be able to log in and
immediately see pending rows, a few flagged anomalies, and the audit trail.
"""
raise NotImplementedError("Implement seeding once models are migrated.")
