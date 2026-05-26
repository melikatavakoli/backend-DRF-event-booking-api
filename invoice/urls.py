from django.urls import path, include
from rest_framework.routers import DefaultRouter
from invoice.views import *

router = DefaultRouter()
app_name = 'invoice'

urlpatterns = [
    path('', include(router.urls)),
    path("admin-invoice/", AdminInvoiceAPIView.as_view(), name="admin_list_invoice"),
    path("cancel-invoice/<uuid:invoice_id>/", CancelInvoiceAPIView.as_view(), name="admin_cancel_invoice"),
    path("invoice/", InvoiceAPIView.as_view(), name="invoice-create"),
    path("invoice/<uuid:invoice_id>/", RetrieveInvoiceAPIView.as_view(), name="get_invoice_by_id"),
    path("user-invoice/", UserInvoiceAPIView.as_view(), name="user_list_invoice"),
]
