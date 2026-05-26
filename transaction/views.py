import requests
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, filters, viewsets
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from django.conf import settings

from common.paginations import CustomLimitOffsetPagination
from .models import Transaction, PaymentReceipt, DiscountCode
from .serializers import (
    TransactionSerializer,
    TransactionCreateSerializer,
    PaymentReceiptSerializer,
    TransactionAdminListSerializer,
    TransactionUserListSerializer,
    TransactionStatusUpdateSerializer,
    TransactionDetailSerializer,
    VerifyCardToCardPaymentSerializer,
    ApplyDiscountSerializer,
    DiscountCodeSerializer,
)
from .choices import TransactionStatus
from booking.models import Booking

User = get_user_model()


class PaymentReceiptViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentReceiptSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or getattr(user, "role", None) == "admin":
            return PaymentReceipt.objects.all()
        return PaymentReceipt.objects.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    pagination_class = CustomLimitOffsetPagination
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    search_fields = ["transaction_no", "description"]
    ordering_fields = ["created_at", "amount", "status"]
    ordering = ["-created_at"]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or getattr(user, "role", None) == "admin":
            return Transaction.objects.select_related("user", "booking").all()
        return Transaction.objects.filter(user=user).select_related("booking")

    def get_serializer_class(self):
        if self.action == "retrieve":
            return TransactionDetailSerializer
        return TransactionSerializer


class CreateTransactionAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = TransactionCreateSerializer(
            data=request.data, context={"request": request}
        )

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        booking = serializer.validated_data["booking_id"]
        payment_method = serializer.validated_data["payment_method"]
        discount = serializer.validated_data.get("discount")

        final_amount = booking.total_amount
        discount_amount = 0

        if discount:
            final_amount = discount.apply_discount(booking.total_amount)
            discount_amount = booking.total_amount - final_amount

        if Transaction.objects.filter(
            booking=booking, status=TransactionStatus.pending
        ).exists():
            return Response(
                {"message": "تراکنش در انتظار پرداخت برای این رزرو وجود دارد"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        transaction = Transaction.objects.create(
            user=request.user,
            booking=booking,
            amount=final_amount,
            final_amount=final_amount,
            discount_amount=discount_amount,
            payment_method=payment_method,
            status=TransactionStatus.pending,
        )

        if discount:
            discount.use()

        if payment_method == "online":
            return self.request_online_payment(transaction, request)

        return Response(
            {
                "message": "تراکنش با موفقیت ایجاد شد. لطفاً رسید پرداخت را آپلود کنید.",
                "transaction": TransactionSerializer(transaction).data,
            },
            status=status.HTTP_201_CREATED,
        )

    def request_online_payment(self, transaction, request):
        data = {
            "merchant": settings.ZIBAL_MERCHANT,
            "amount": int(transaction.amount * 10),
            "callbackUrl": request.build_absolute_uri("/api/v1/transaction/callback/"),
            "description": f"پرداخت بلیط کنسرت - شماره تراکنش {transaction.transaction_no}",
        }

        try:
            response = requests.post(
                "https://gateway.zibal.ir/v1/request", json=data, timeout=30
            )
            result = response.json()

            if result.get("result") == 100:
                track_id = result.get("trackId")
                transaction.track_id = track_id
                transaction.save(update_fields=["track_id"])

                payment_url = f"https://gateway.zibal.ir/start/{track_id}"

                return Response(
                    {
                        "payment_url": payment_url,
                        "track_id": track_id,
                        "transaction": TransactionSerializer(transaction).data,
                    },
                    status=status.HTTP_200_OK,
                )
            else:
                transaction.status = TransactionStatus.failed
                transaction.save()
                return Response(
                    {
                        "message": "خطا در ارتباط با درگاه پرداخت",
                        "result": result,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        except Exception as e:
            transaction.status = TransactionStatus.failed
            transaction.save()
            return Response(
                {"message": f"خطا: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class VerifyTransactionAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        track_id = request.query_params.get("trackId")

        if not track_id:
            return Response({"message": "پارامتر trackId ارسال نشده است"}, status=400)

        try:
            transaction = Transaction.objects.get(track_id=track_id)
        except Transaction.DoesNotExist:
            return Response({"message": "تراکنش یافت نشد!"}, status=404)

        to_toman_rate = 10
        data = {"merchant": settings.ZIBAL_MERCHANT, "trackId": track_id}
        url = "https://gateway.zibal.ir/v1/verify"

        try:
            response = requests.post(url, json=data, timeout=50)
            response_json = response.json()
        except Exception:
            return Response({"message": "خطا در برقراری ارتباط با سرور!"}, status=400)

        if response_json.get("status") == "success":
            if response_json.get("amount", 0) == int(
                float(transaction.amount) * to_toman_rate
            ):
                transaction.mark_as_successful(
                    ref_number=response_json.get("ref_id", ""),
                    track_id=track_id,
                    card_number=response_json.get("cardNumber", ""),
                )

                frontend_url = settings.FRONTEND_URL
                return redirect(
                    f"{frontend_url}/payment-success?transaction_id={transaction.id}"
                )
            else:
                return Response({"message": "مبلغ تراکنش نامعتبر است!"}, status=400)
        else:
            transaction.mark_as_failed(
                reason=response_json.get("message", "پرداخت ناموفق")
            )
            frontend_url = settings.FRONTEND_URL
            return redirect(
                f"{frontend_url}/payment-failed?transaction_id={transaction.id}"
            )


class VerifyCardToCardPaymentAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not (
            request.user.is_staff or getattr(request.user, "role", None) == "admin"
        ):
            return Response({"message": "شما دسترسی لازم را ندارید"}, status=403)

        serializer = VerifyCardToCardPaymentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        transaction = serializer.validated_data["transaction"]
        receipt = serializer.validated_data["receipt"]

        transaction.payment_receipt = receipt
        transaction.mark_as_successful()

        receipt.verified = True
        receipt.verified_by = request.user
        receipt.verified_at = timezone.now()
        receipt.save()

        return Response(
            {
                "message": "پرداخت با موفقیت تأیید شد",
                "transaction": TransactionSerializer(transaction).data,
            },
            status=status.HTTP_200_OK,
        )


class UploadPaymentReceiptAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, transaction_id):
        try:
            transaction = Transaction.objects.get(id=transaction_id, user=request.user)
        except Transaction.DoesNotExist:
            return Response({"message": "تراکنش یافت نشد"}, status=404)

        if transaction.is_successful:
            return Response({"message": "این تراکنش قبلاً موفق شده است"}, status=400)

        image = request.FILES.get("image")
        if not image:
            return Response({"message": "لطفاً تصویر رسید را آپلود کنید"}, status=400)

        receipt = PaymentReceipt.objects.create(
            user=request.user,
            image=image,
            description=request.data.get("description", ""),
        )

        transaction.payment_receipt = receipt
        transaction.save()

        return Response(
            {
                "message": "رسید با موفقیت آپلود شد. پس از تأیید ادمین، بلیط‌ها صادر می‌شوند.",
                "receipt": PaymentReceiptSerializer(receipt).data,
            },
            status=status.HTTP_201_CREATED,
        )


class ApplyDiscountCodeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ApplyDiscountSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        discount_code = serializer.validated_data["discount_code"]
        booking_id = serializer.validated_data["booking_id"]

        try:
            booking = Booking.objects.get(id=booking_id, user=request.user)
        except Booking.DoesNotExist:
            return Response({"message": "رزرو یافت نشد"}, status=404)

        try:
            discount = DiscountCode.objects.get(
                code=discount_code.upper(), is_active=True
            )
        except DiscountCode.DoesNotExist:
            return Response({"message": "کد تخفیف نامعتبر است"}, status=400)

        valid, message = discount.is_valid(booking.total_amount)
        if not valid:
            return Response({"message": message}, status=400)

        final_amount = discount.apply_discount(booking.total_amount)

        return Response(
            {
                "message": "کد تخفیف معتبر است",
                "discount_code": discount.code,
                "original_amount": str(booking.total_amount),
                "discount_amount": str(booking.total_amount - final_amount),
                "final_amount": str(final_amount),
            },
            status=status.HTTP_200_OK,
        )


class DiscountCodeListAPIView(ListAPIView):
    serializer_class = DiscountCodeSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomLimitOffsetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ["code"]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or getattr(user, "role", None) == "admin":
            return DiscountCode.objects.all()
        # کاربران عادی فقط کدهای فعال رو می‌بینند
        return DiscountCode.objects.filter(is_active=True)


class TransactionAdminListView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TransactionAdminListSerializer
    pagination_class = CustomLimitOffsetPagination
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    search_fields = [
        "transaction_no",
        "description",
        "user__first_name",
        "user__last_name",
    ]
    filterset_fields = ["status", "payment_method"]
    ordering_fields = ["amount", "status", "created_at", "final_amount"]
    ordering = ["-created_at"]

    def get_queryset(self):
        user = self.request.user
        if not (user.is_staff or getattr(user, "role", None) == "admin"):
            return Transaction.objects.none()
        return Transaction.objects.select_related("user", "booking").all()


class TransactionUserListView(ListAPIView):
    serializer_class = TransactionUserListSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomLimitOffsetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["status"]
    ordering_fields = ["created_at", "amount", "status"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user).select_related(
            "booking"
        )


class TransactionDetailAPIView(RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TransactionDetailSerializer
    lookup_field = "id"

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or getattr(user, "role", None) == "admin":
            return Transaction.objects.all()
        return Transaction.objects.filter(user=user)


class AdminTransactionStatusUpdateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, transaction_id):
        if not (
            request.user.is_staff or getattr(request.user, "role", None) == "admin"
        ):
            return Response({"message": "شما دسترسی لازم را ندارید"}, status=403)

        try:
            transaction = Transaction.objects.get(id=transaction_id)
        except Transaction.DoesNotExist:
            return Response({"message": "تراکنش یافت نشد"}, status=404)

        serializer = TransactionStatusUpdateSerializer(
            transaction, data=request.data, partial=True
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        old_status = transaction.status
        new_status = serializer.validated_data["status"]
        transaction.status = new_status

        if new_status == TransactionStatus.success and not transaction.paid_at:
            transaction.paid_at = timezone.now()

        transaction.save()

        if (
            new_status == TransactionStatus.success
            and transaction.booking
            and not transaction.booking.is_paid
        ):
            transaction.booking.is_paid = True
            transaction.booking.payment_time = timezone.now()
            transaction.booking.save()

        return Response(
            {
                "message": f"وضعیت تراکنش از {old_status} به {new_status} تغییر یافت",
                "transaction": TransactionSerializer(transaction).data,
            },
            status=status.HTTP_200_OK,
        )
