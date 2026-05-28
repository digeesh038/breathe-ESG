"""Root URL config. Each app owns its own router under /api/."""
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def api_index(request):
    """Service index at `/`. Confirms the API is up and points to the routes.

    Without this, hitting the bare host returns a bare 404 that looks like the
    backend is down; this gives a 200 with a map of where things live.
    """
    base = request.build_absolute_uri("/api/v1/")
    return JsonResponse(
        {
            "service": "Breathe ESG API",
            "status": "ok",
            "admin": request.build_absolute_uri("/admin/"),
            "api_root": base,
            "endpoints": {
                "auth_login": base + "tenants/auth/login/",
                "auth_refresh": base + "tenants/auth/refresh/",
                "auth_me": base + "tenants/auth/me/",
                "organizations": base + "tenants/organizations/",
                "reference": base + "reference/",
                "ingestion": base + "ingestion/",
                "emissions": base + "emissions/",
                "activities_summary": base + "emissions/activities/summary/",
                "activities_export": base + "emissions/activities/export/?format=csv",
                "review": base + "review/",
                "audit": base + "audit/",
            },
        }
    )


def api_v1_index(request):
    """Index for the versioned API root so `/api/v1/` returns a 200 map."""
    base = request.build_absolute_uri("/api/v1/")
    return JsonResponse(
        {
            "version": "v1",
            "tenants": base + "tenants/",
            "reference": base + "reference/",
            "ingestion": base + "ingestion/",
            "emissions": base + "emissions/",
            "review": base + "review/",
            "audit": base + "audit/",
        }
    )


api_v1 = [
    path("", api_v1_index, name="api-v1-index"),
    path("tenants/", include("apps.tenants.urls")),
    path("reference/", include("apps.reference.urls")),
    path("ingestion/", include("apps.ingestion.urls")),
    path("emissions/", include("apps.emissions.urls")),
    path("review/", include("apps.review.urls")),
    path("audit/", include("apps.audit.urls")),
]

urlpatterns = [
    path("", api_index, name="api-index"),
    path("admin/", admin.site.urls),
    path("api/v1/", include(api_v1)),
]
