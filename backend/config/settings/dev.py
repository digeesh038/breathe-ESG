"""Local development settings."""
from .base import *  # noqa: F401,F403
from .base import env

DEBUG = True

CORS_ALLOWED_ORIGINS = env.list(
    "CORS_ALLOWED_ORIGINS", default=["http://localhost:5173"]
)

# Default to in-process Celery for dev so an analyst can hack on the pipeline
# without running a Redis broker. Override with CELERY_TASK_ALWAYS_EAGER=False
# (and a real broker URL) to exercise the worker path locally.
CELERY_TASK_ALWAYS_EAGER = env.bool("CELERY_TASK_ALWAYS_EAGER", default=True)
