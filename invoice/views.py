from decimal import Decimal
from django_filters.rest_framework import DjangoFilterBackend
from requests import Response
from rest_framework import generics
from rest_framework import viewsets, permissions
from common.paginations import CustomLimitOffsetPagination
from invoice.serializers import InvoiceListSerializer, InvoiceSerializer, InvoiceWriteSerializer
from invoice.types import InvoiceStatus
from .models import Invoice
from rest_framework import filters as drf_filters
from django.db.models import Value, CharField,  F
from django.db.models.functions import Concat
from django.contrib.auth import get_user_model
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.exceptions import PermissionDenied

User = get_user_model()


class RetrieveInvoiceAPIView(generics.RetrieveAPIView):
    queryset = Invoice.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class=InvoiceSerializer
    lookup_url_kwarg = "invoice_id"
    

class InvoiceAPIView(generics.CreateAPIView):
    queryset = Invoice.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class=InvoiceWriteSerializer
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user, created_by=self.request.user)
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            invoice = serializer.save()
            return Response({
                "detail": "فاکتور با موفقیت ایجاد شد",
                "invoice_id": str(invoice.id),
                "invoice_number": invoice.invoice_number,
                "final_amount": invoice.final_amount
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({
                "detail": f"خطا در ایجاد فاکتور: {str(e)}"
            }, status=status.HTTP_400_BAD_REQUEST)
    
    
class UserInvoiceAPIView(generics.ListAPIView):
    serializer_class=InvoiceListSerializer
    queryset = Invoice.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomLimitOffsetPagination
    filter_backends = [DjangoFilterBackend, drf_filters.SearchFilter, drf_filters.OrderingFilter]
    search_fields = ['invoice_number', 'created_at']
    ordering_fields = [
        "invoice_number",
        "status",
        "total_amount", 
        "issue_date",
        "invoice_date",
    ]
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Invoice.objects.none()
        if getattr(user, "role", None) == "user":
            return Invoice.objects.filter(user=user).order_by("-created_at")
        return Invoice.objects.none()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context
    
    
class AdminInvoiceAPIView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Invoice.objects.all()
    pagination_class = CustomLimitOffsetPagination
    serializer_class=InvoiceListSerializer
    filter_backends = [DjangoFilterBackend, drf_filters.SearchFilter, drf_filters.OrderingFilter]
    ordering_fields = [
        'invoice_number',
        'issue_date',
        'invoice_date',
        'final_amount',
        'created_by__first_name',
        'created_by__last_name',
        'full_name_annotated'
    ]
    search_fields = [
        "invoice_number",
        'full_name_annotated',
        "created_by__first_name",
        'created_by__last_name'
    ]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Invoice.objects.none()
        if getattr(user, "role", None) != "admin":
            raise PermissionDenied("You do not have permission to access this resource.")

        return (
            Invoice.objects
            .select_related("created_by", "user")
            .annotate(
                full_name_annotated=Concat(
                    F("user__first_name"),
                    Value(" "),
                    F("user__last_name"),
                    output_field=CharField(),
                ),
            )
            .order_by("-issue_date")
        )
        
        
class CancelInvoiceAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, invoice_id):
        try:
            invoice = Invoice.objects.get(pk=invoice_id)
        except Invoice.DoesNotExist:
            return Response({"detail": "صورت حساب یافت نشد"}, status=status.HTTP_404_NOT_FOUND)

        if invoice.status in [InvoiceStatus.paid, InvoiceStatus.refunded]:
            return Response({"detail": "صورت حساب قبلا پرداخت/رفاند شده است"}, status=status.HTTP_400_BAD_REQUEST)
        if invoice.status == InvoiceStatus.cancelled:
            return Response({"detail": "صورت حساب قبلا لغو شده است"}, status=status.HTTP_400_BAD_REQUEST)

        invoice.status = InvoiceStatus.cancelled
        invoice.save(update_fields=["status"])
        return Response({"detail": f"صورت حساب {invoice.invoice_number} لغو شد"}, status=status.HTTP_200_OK)
    
    
