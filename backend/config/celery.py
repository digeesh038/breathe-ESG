"""Celery app bootstrap.

Imported from `config/__init__.py` so `@shared_task` is registered before any
app modules try to enqueue work. Settings (broker URL, eager mode) come from
Django settings; the worker is launched with:

    celery -A config worker -l info
"""
import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

app = Celery("breathe_esg")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
