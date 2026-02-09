from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path, re_path
from rest_framework.renderers import JSONOpenAPIRenderer
from rest_framework.schemas import get_schema_view

from nsot import __version__

from ..api.views import NotFoundViewSet

# This is the basic API explorer for Swagger/OpenAPI 2.0
schema_view = get_schema_view(
    title="NSoT API",
    renderer_classes=[JSONOpenAPIRenderer],
)


def api_root(request):
    """JSON service info at /."""
    return JsonResponse(
        {
            "name": "Network Source of Truth (NSoT)",
            "version": __version__,
            "api": "/api/",
            "admin": "/admin/",
            "docs": "https://nsot.readthedocs.io/",
        }
    )


urlpatterns = [
    # API
    path("api/", include("nsot.api.urls")),
    # Catchall for missing endpoints
    re_path(r"^api/.*/$", NotFoundViewSet.as_view({"get": "list"})),
    # Docs
    path("schema.json", schema_view, name="swagger"),
    # Admin
    path("admin/", admin.site.urls),
    # Service info
    path("", api_root, name="index"),
]
