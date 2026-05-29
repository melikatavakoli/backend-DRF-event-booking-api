from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
app_name = "transaction"

router.register("payment-receipts", views.PaymentReceiptViewSet, basename="payment-receipt",)
router.register("transactions", views.TransactionViewSet, basename="transaction",)

urlpatterns = [
    path("", include(router.urls)),
    path(
        "create/",
        views.CreateTransactionAPIView.as_view(),
        name="create-transaction",
    ),
    path(
        "verify/",
        views.VerifyTransactionAPIView.as_view(),
        name="verify-transaction",
    ),
    path(
        "callback/",
        views.VerifyTransactionAPIView.as_view(),
        name="transaction-callback",
    ),
    path(
        "upload-receipt/<int:transaction_id>/",
        views.UploadPaymentReceiptAPIView.as_view(),
        name="upload-receipt",
    ),
    path(
        "verify-card-payment/",
        views.VerifyCardToCardPaymentAPIView.as_view(),
        name="verify-card-payment",
    ),
    path(
        "apply-discount/",
        views.ApplyDiscountCodeAPIView.as_view(),
        name="apply-discount",
    ),
    path(
        "discount-codes/",
        views.DiscountCodeListAPIView.as_view(),
        name="discount-codes",
    ),
    path(
        "admin/",
        views.TransactionAdminListView.as_view(),
        name="admin-transactions",
    ),
    path(
        "my/",
        views.TransactionUserListView.as_view(),
        name="user-transactions",
    ),
    path(
        "transaction/<int:id>/",
        views.TransactionDetailAPIView.as_view(),
        name="transaction-detail",
    ),
    path(
        "admin/update-transaction/<int:transaction_id>/",
        views.AdminTransactionStatusUpdateAPIView.as_view(),
        name="admin-update-transaction",
    ),
]
