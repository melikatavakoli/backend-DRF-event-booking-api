from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import (
    generics,
    viewsets,
    permissions,
    status,
    filters as drf_filters,
)
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied
from django.db.models import Value, CharField, F
from django.db.models.functions import Concat
from django.contrib.auth import get_user_model

from common.paginations import CustomLimitOffsetPagination
from invoice.serializers import (
    InvoiceListSerializer,
    InvoiceSerializer,
    InvoiceWriteSerializer,
    InvoiceStatusUpdateSerializer,
)
from invoice.choices import InvoiceStatus
from invoice.models import Invoice, InvoiceItem

User = get_user_model()


class InvoiceViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomLimitOffsetPagination
    filter_backends = [
        DjangoFilterBackend,
        drf_filters.SearchFilter,
        drf_filters.OrderingFilter,
    ]
    search_fields = ["invoice_number", "tracking_code", "description"]
    filterset_fields = ["status"]
    ordering_fields = [
        "invoice_number",
        "issue_date",
        "final_amount",
        "created_at",
    ]
    ordering = ["-created_at"]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or getattr(user, "role", None) == "admin":
            return (
                Invoice.objects.select_related(
                    "user", "booking", "transaction"
                )
                .prefetch_related("items")
                .all()
            )
        return (
            Invoice.objects.filter(user=user)
            .select_related("booking", "transaction")
            .prefetch_related("items")
        )

    def get_serializer_class(self):
        if self.action == "list":
            return InvoiceListSerializer
        elif self.action == "create":
            return InvoiceWriteSerializer
        elif self.action == "update" or self.action == "partial_update":
            return InvoiceStatusUpdateSerializer
        return InvoiceSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            invoice = serializer.save()
            return Response(
                {
                    "success": True,
                    "message": "فاکتور با موفقیت ایجاد شد",
                    "invoice_id": str(invoice.id),
                    "invoice_number": invoice.invoice_number,
                    "final_amount": invoice.final_amount,
                },
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            return Response(
                {
                    "success": False,
                    "message": f"خطا در ایجاد فاکتور: {str(e)}",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()

        if not (
            request.user.is_staff
            or getattr(request.user, "role", None) == "admin"
        ):
            return Response(
                {
                    "success": False,
                    "message": "شما دسترسی لازم برای این کار را ندارید",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = self.get_serializer(
            instance, data=request.data, partial=partial
        )
        serializer.is_valid(raise_exception=True)

        old_status = instance.status
        new_status = serializer.validated_data["status"]

        if new_status == InvoiceStatus.paid and not instance.transaction:
            return Response(
                {
                    "success": False,
                    "message": "برای پرداخت فاکتور باید تراکنش معتبر وجود داشته باشد",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if instance.transaction and instance.transaction.is_successful:
            instance.status = InvoiceStatus.paid
            instance.save()

        self.perform_update(serializer)

        return Response(
            {
                "success": True,
                "message": f"وضعیت فاکتور از {old_status} به {new_status} تغییر یافت",
                "data": InvoiceSerializer(instance).data,
            },
            status=status.HTTP_200_OK,
        )


class RetrieveInvoiceAPIView(generics.RetrieveAPIView):
    queryset = Invoice.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = InvoiceSerializer
    lookup_url_kwarg = "invoice_id"

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or getattr(user, "role", None) == "admin":
            return Invoice.objects.all()
        return Invoice.objects.filter(user=user)


class CreateInvoiceFromBookingAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        booking_id = request.data.get("booking_id")
        transaction_id = request.data.get("transaction_id")

        if not booking_id:
            return Response(
                {"success": False, "message": "شناسه رزرو الزامی است"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from booking.models import Booking
        from transaction.models import Transaction

        try:
            booking = Booking.objects.get(id=booking_id, user=request.user)
        except Booking.DoesNotExist:
            return Response(
                {"success": False, "message": "رزرو یافت نشد"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if Invoice.objects.filter(booking=booking).exists():
            existing_invoice = Invoice.objects.get(booking=booking)
            return Response(
                {
                    "success": False,
                    "message": "فاکتور برای این رزرو قبلاً ایجاد شده است",
                    "invoice_id": str(existing_invoice.id),
                    "invoice_number": existing_invoice.invoice_number,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        transaction = None
        if transaction_id:
            try:
                transaction = Transaction.objects.get(
                    id=transaction_id, user=request.user
                )
            except Transaction.DoesNotExist:
                pass

        invoice = Invoice.objects.create(
            user=request.user,
            booking=booking,
            transaction=transaction,
            status=(
                InvoiceStatus.paid
                if transaction and transaction.is_successful
                else InvoiceStatus.unpaid
            ),
            issue_date=booking.created_at,
        )

        for ticket in booking.tickets.all():
            unit_price = ticket.category.price if ticket.category else 0
            InvoiceItem.objects.create(
                invoice=invoice,
                ticket=ticket,
                quantity=1,
                unit_price=unit_price,
                tax_percent=9,
                discount_percent=0,
            )

        invoice.update_totals()

        return Response(
            {
                "success": True,
                "message": "فاکتور با موفقیت ایجاد شد",
                "invoice": InvoiceSerializer(invoice).data,
            },
            status=status.HTTP_201_CREATED,
        )


class UserInvoiceListView(generics.ListAPIView):
    serializer_class = InvoiceListSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomLimitOffsetPagination
    filter_backends = [
        DjangoFilterBackend,
        drf_filters.SearchFilter,
        drf_filters.OrderingFilter,
    ]
    search_fields = ["invoice_number", "tracking_code"]
    filterset_fields = ["status"]
    ordering_fields = [
        "invoice_number",
        "issue_date",
        "final_amount",
        "created_at",
    ]
    ordering = ["-created_at"]

    def get_queryset(self):
        return Invoice.objects.filter(user=self.request.user).select_related(
            "booking"
        )


class AdminInvoiceListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = InvoiceListSerializer
    pagination_class = CustomLimitOffsetPagination
    filter_backends = [
        DjangoFilterBackend,
        drf_filters.SearchFilter,
        drf_filters.OrderingFilter,
    ]
    search_fields = [
        "invoice_number",
        "tracking_code",
        "user__first_name",
        "user__last_name",
    ]
    filterset_fields = ["status"]
    ordering_fields = [
        "invoice_number",
        "issue_date",
        "final_amount",
        "created_at",
    ]
    ordering = ["-created_at"]

    def get_queryset(self):
        user = self.request.user
        if not (user.is_staff or getattr(user, "role", None) == "admin"):
            raise PermissionDenied("شما دسترسی لازم برای این بخش را ندارید")

        return (
            Invoice.objects.select_related("user", "booking")
            .all()
            .annotate(
                full_name_annotated=Concat(
                    F("user__first_name"),
                    Value(" "),
                    F("user__last_name"),
                    output_field=CharField(),
                )
            )
        )


class CancelInvoiceAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, invoice_id):
        try:
            invoice = Invoice.objects.get(pk=invoice_id)
        except Invoice.DoesNotExist:
            return Response(
                {"success": False, "message": "فاکتور یافت نشد"},
                status=status.HTTP_404_NOT_FOUND,
            )

        user = request.user
        is_admin = user.is_staff or getattr(user, "role", None) == "admin"
        if not (is_admin or invoice.user == user):
            return Response(
                {
                    "success": False,
                    "message": "شما دسترسی لازم برای لغو این فاکتور را ندارید",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        if invoice.status in [InvoiceStatus.paid, InvoiceStatus.refunded]:
            return Response(
                {
                    "success": False,
                    "message": "فاکتور قبلاً پرداخت یا برگشت داده شده است",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if invoice.status == InvoiceStatus.cancelled:
            return Response(
                {"success": False, "message": "فاکتور قبلاً لغو شده است"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        invoice.status = InvoiceStatus.cancelled
        invoice.save(update_fields=["status"])

        return Response(
            {
                "success": True,
                "message": f"فاکتور {invoice.invoice_number} با موفقیت لغو شد",
                "invoice_id": str(invoice.id),
            },
            status=status.HTTP_200_OK,
        )
