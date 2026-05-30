from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = "ticket"
router = DefaultRouter()

router.register(r"ticket", views.TicketViewSet, basename="ticket")

urlpatterns = [
    path("", include(router.urls)),
]
