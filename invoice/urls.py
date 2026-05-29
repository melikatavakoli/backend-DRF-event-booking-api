from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
app_name = "invoice"

router.register("invoices", views.InvoiceViewSet)

urlpatterns = [
    path("api/", include(router.urls)),
    path(
        "create-from-booking/",
        views.CreateInvoiceFromBookingAPIView.as_view(),
        name="create-invoice-from-booking",
    ),
    path("user/", views.UserInvoiceListView.as_view(), name="user-invoices"),
    path(
        "admin/", views.AdminInvoiceListView.as_view(), name="admin-invoices"
    ),
    path(
        "<int:invoice_id>/",
        views.RetrieveInvoiceAPIView.as_view(),
        name="invoice-detail",
    ),
    path(
        "views/<int:invoice_id>/",
        views.CancelInvoiceAPIView.as_view(),
        name="cancel-invoice",
    ),
]
