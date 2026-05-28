"""Boot Celery alongside the Django app so @shared_task decorators register."""
from .celery import app as celery_app

__all__ = ["celery_app"]
