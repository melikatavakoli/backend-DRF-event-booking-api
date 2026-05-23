from django.urls import include, path
from rest_framework.routers import DefaultRouter

from address import views

router = DefaultRouter()

router.register("country", views.CountryViewSet, basename="country")
router.register("state", views.StateViewSet, basename="state")
router.register("city", views.CityViewSet, basename="city")

app_name = "address"

urlpatterns = [
    path("", include(router.urls)),
]
