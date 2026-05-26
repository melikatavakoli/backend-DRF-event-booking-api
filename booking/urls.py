from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()

router.register(r"show", views.ShowViewSet, basename="show")
router.register(r"booking", views.BookingViewSet, basename="booking")

app_name = "booking"

urlpatterns = [
    path("", include(router.urls)),
]
