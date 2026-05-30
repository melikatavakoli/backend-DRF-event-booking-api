from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
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
    path("api/v1/transaction/", include("transaction.urls")),
    path("api/v1/invoice/", include("invoice.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)