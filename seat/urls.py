from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
app_name = 'seats'

router.register(r"prefix", views.PrefixViewSet, basename="prefix")
router.register(r"suffix", views.SuffixViewSet, basename="suffix")
router.register(r"seat", views.SeatViewSet, basename="seat")

urlpatterns = [
    path('', include(router.urls)),
]
