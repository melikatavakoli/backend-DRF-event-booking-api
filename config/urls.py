from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)


urlpatterns = [
    path("adminpanel/", admin.site.urls),
    path(
        "api/v1/schema/",
        SpectacularAPIView.as_view(authentication_classes=[], permission_classes=[]),
        name="schema",
    ),
    path(
        "api/v1/docs/",
        SpectacularSwaggerView.as_view(
            url_name="schema",
            authentication_classes=[],
            permission_classes=[],
        ),
        name="swagger-ui",
    ),
    path(
        "api/v1/redoc/",
        SpectacularRedocView.as_view(
            url_name="schema",
            authentication_classes=[],
            permission_classes=[],
        ),
        name="redoc",
    ),
    path("api/v1/address/", include("address.urls")),
    path("api/v1/core/", include("core.urls")),
    path("api/v1/booking/", include("booking.urls")),
    path("api/v1/seat/", include("seat.urls")),
    path("api/v1/ticket/", include("ticket.urls")),
]
