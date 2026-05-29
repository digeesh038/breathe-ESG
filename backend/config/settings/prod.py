"""Production settings for the deployed prototype (Render/Railway/Fly)."""
from .base import *  # noqa: F401,F403
from .base import BASE_DIR, INSTALLED_APPS, env

DEBUG = False

# Fail fast if the signing key wasn't provided — never run prod on the insecure
# dev default (which would compromise JWT/session signing).
SECRET_KEY = env("SECRET_KEY")
if not SECRET_KEY or SECRET_KEY == "dev-insecure-key":
    raise RuntimeError("SECRET_KEY must be set to a strong value in production.")

# Hosting platforms set this; e.g. esg-api.onrender.com
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")

# The Vercel frontend talks to this API cross-origin. Default to the known
# deployment origin so the app works out of the box; override via env to add
# more origins. Preview deploys (esg-*.vercel.app) are matched by regex.
_DEFAULT_FRONTEND_ORIGIN = "https://breathe-esg-eight-indol.vercel.app"
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[_DEFAULT_FRONTEND_ORIGIN])
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[_DEFAULT_FRONTEND_ORIGIN])
CORS_ALLOWED_ORIGIN_REGEXES = [r"^https://breathe-esg.*\.vercel\.app$"]

# Reuse DB connections across requests (managed Postgres). 0 = new conn per
# request, which is wasteful under load.
DATABASES["default"]["CONN_MAX_AGE"] = env.int("CONN_MAX_AGE", default=600)  # noqa: F405

# --- HTTPS / transport security ---
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=60 * 60 * 24 * 365)  # 1yr
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"

# --- Object storage for uploads (S3) ---
# Render/Railway filesystems are ephemeral, so uploaded files must go to object
# storage in prod. Enable by setting USE_S3=True + the AWS_* vars. Falls back to
# local MEDIA_ROOT (fine for a single-box deploy with a persistent volume).
USE_S3 = env.bool("USE_S3", default=False)
if USE_S3:
    INSTALLED_APPS = [*INSTALLED_APPS, "storages"]
    STORAGES = {
        "default": {"BACKEND": "storages.backends.s3.S3Storage"},
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"
        },
    }
    AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME")
    AWS_S3_REGION_NAME = env("AWS_S3_REGION_NAME", default="us-east-1")
    AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID", default=None)
    AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY", default=None)
    AWS_S3_ENDPOINT_URL = env("AWS_S3_ENDPOINT_URL", default=None)
    AWS_DEFAULT_ACL = None
    AWS_QUERYSTRING_AUTH = True  # signed URLs — uploads aren't public
else:
    MEDIA_ROOT = env("MEDIA_ROOT", default=str(BASE_DIR / "media"))

# --- Optional error tracking (Sentry) ---
SENTRY_DSN = env("SENTRY_DSN", default="")
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()],
        traces_sample_rate=env.float("SENTRY_TRACES_SAMPLE_RATE", default=0.0),
        send_default_pii=False,
        environment=env("SENTRY_ENVIRONMENT", default="production"),
    )
