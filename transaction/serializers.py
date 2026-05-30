from persiantools.jdatetime import JalaliDateTime
from rest_framework import serializers

from booking.models import Booking
from ticket.serializers import TicketSerializer
from transaction.models import Transaction, PaymentReceipt, DiscountCode


class PaymentReceiptSerializer(serializers.ModelSerializer):
    uploaded_at = serializers.SerializerMethodField(read_only=True)
    receipt_url = serializers.SerializerMethodField(read_only=True)
    verified_by_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = PaymentReceipt
        fields = [
            "id",
            "user",
            "image",
            "description",
            "uploaded_at",
            "receipt_url",
            "verified",
            "verified_by_name",
            "verified_at",
        ]
        read_only_fields = ["user", "verified", "verified_by", "verified_at"]

    def get_uploaded_at(self, obj):
        return JalaliDateTime.to_jalali(obj.uploaded_at).strftime("%Y/%m/%d %H:%M")

    def get_receipt_url(self, obj):
        return obj.image.url if obj.image else None

    def get_verified_by_name(self, obj):
        if obj.verified_by:
            return f"{obj.verified_by.first_name} {obj.verified_by.last_name}"
        return None


class DiscountCodeSerializer(serializers.ModelSerializer):
    is_valid = serializers.SerializerMethodField()

    class Meta:
        model = DiscountCode
        fields = [
            "id",
            "code",
            "discount_percent",
            "discount_amount",
            "max_uses",
            "used_count",
            "valid_from",
            "valid_to",
            "min_purchase_amount",
            "is_active",
            "is_valid",
        ]

    def get_is_valid(self, obj):
        valid, _ = obj.is_valid()
        return valid


class ApplyDiscountSerializer(serializers.Serializer):
    discount_code = serializers.CharField(max_length=50)
    booking_id = serializers.IntegerField()


class TransactionSerializer(serializers.ModelSerializer):
    payment_receipt = PaymentReceiptSerializer(read_only=True)
    user = serializers.SerializerMethodField()
    fee = serializers.SerializerMethodField()
    calculated_amount = serializers.SerializerMethodField()
    created_at_jalali = serializers.SerializerMethodField()
    paid_at_jalali = serializers.SerializerMethodField()
    booking_detail = serializers.SerializerMethodField()

    class Meta:
        model = Transaction
        fields = [
            "id",
            "transaction_no",
            "user",
            "booking",
            "booking_detail",
            "amount",
            "fee",
            "discount_amount",
            "bank_name",
            "card_number",
            "ref_number",
            "track_id",
            "status",
            "gateway",
            "payment_receipt",
            "description",
            "calculated_amount",
            "created_at_jalali",
            "paid_at_jalali",
        ]
        read_only_fields = ["user", "transaction_no"]

    def get_created_at_jalali(self, obj):
        return JalaliDateTime.to_jalali(obj.created_at).strftime("%Y/%m/%d %H:%M")

    def get_paid_at_jalali(self, obj):
        if obj.paid_at:
            return JalaliDateTime.to_jalali(obj.paid_at).strftime("%Y/%m/%d %H:%M")
        return None

    def get_user(self, obj):
        if not obj.user:
            return None
        return {
            "id": obj.user.id,
            "first_name": obj.user.first_name,
            "last_name": obj.user.last_name,
            "mobile": getattr(obj.user, "mobile", ""),
            "email": obj.user.email,
            "full_name": getattr(
                obj.user,
                "full_name",
                f"{obj.user.first_name} {obj.user.last_name}",
            ),
        }

    def get_fee(self, obj):
        return str(obj.fee) if obj.fee else "0"

    def get_calculated_amount(self, obj):
        return str(obj.calculated_amount) if obj.calculated_amount else "0"

    def get_booking_detail(self, obj):
        if not obj.booking:
            return None
        return {
            "id": obj.booking.id,
            "concert_name": getattr(obj.booking.concert, "name", None),
            "concert_date": (
                str(obj.booking.concert.date)
                if hasattr(obj.booking, "concert")
                else None
            ),
            "total_amount": str(obj.booking.total_amount),
            "tickets_count": (
                obj.booking.tickets.count() if hasattr(obj.booking, "tickets") else 0
            ),
        }


class TransactionCreateSerializer(serializers.Serializer):
    booking_id = serializers.IntegerField()
    discount_code = serializers.CharField(
        max_length=50, required=False, allow_blank=True
    )

    def validate_booking_id(self, value):

        try:
            booking = Booking.objects.get(id=value)
        except Booking.DoesNotExist:
            raise serializers.ValidationError("رزرو مورد نظر یافت نشد")

        user = self.context["request"].user
        if booking.user != user:
            raise serializers.ValidationError("این رزرو متعلق به شما نیست")

        if booking.is_paid:
            raise serializers.ValidationError("این رزرو قبلاً پرداخت شده است")

        from django.utils import timezone

        if booking.expires_at and timezone.now() > booking.expires_at:
            raise serializers.ValidationError("زمان رزرو شما به اتمام رسیده است")

        self.booking = booking
        return value

    def validate_discount_code(self, value):
        if not value:
            return None

        try:
            discount = DiscountCode.objects.get(code=value.upper(), is_active=True)
        except DiscountCode.DoesNotExist:
            raise serializers.ValidationError("کد تخفیف نامعتبر است")

        if hasattr(self, "booking"):
            valid, message = discount.is_valid(self.booking.total_amount)
            if not valid:
                raise serializers.ValidationError(message)

        self.discount = discount
        return value


class TransactionStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ["id", "status", "description"]

    def validate_status(self, value):
        from .choices import TransactionStatus

        valid_statuses = [
            TransactionStatus.success,
            TransactionStatus.failed,
            TransactionStatus.pending,
        ]
        if value not in valid_statuses:
            raise serializers.ValidationError(
                f"وضعیت باید یکی از این مقادیر باشد: {valid_statuses}"
            )
        return value


class VerifyCardToCardPaymentSerializer(serializers.Serializer):
    transaction_id = serializers.IntegerField()
    receipt_id = serializers.IntegerField()

    def validate_transaction_id(self, value):
        try:
            transaction = Transaction.objects.get(id=value)
        except Transaction.DoesNotExist:
            raise serializers.ValidationError("تراکنش یافت نشد")

        if transaction.is_successful:
            raise serializers.ValidationError("این تراکنش قبلاً موفق شده است")

        self.transaction = transaction
        return value

    def validate_receipt_id(self, value):
        try:
            receipt = PaymentReceipt.objects.get(id=value)
        except PaymentReceipt.DoesNotExist:
            raise serializers.ValidationError("رسید پرداخت یافت نشد")

        self.receipt = receipt
        return value


class TransactionAdminListSerializer(serializers.ModelSerializer):
    user_full_name = serializers.SerializerMethodField()
    booking_id = serializers.IntegerField(source="booking.id", read_only=True)
    created_at_jalali = serializers.SerializerMethodField()
    paid_at_jalali = serializers.SerializerMethodField()

    class Meta:
        model = Transaction
        fields = [
            "id",
            "transaction_no",
            "user_full_name",
            "booking_id",
            "amount",
            "status",
            "description",
            "created_at_jalali",
            "paid_at_jalali",
        ]
        read_only_fields = fields

    def get_user_full_name(self, obj):
        if not obj.user:
            return None
        return getattr(
            obj.user,
            "full_name",
            f"{obj.user.first_name} {obj.user.last_name}",
        )

    def get_created_at_jalali(self, obj):
        return JalaliDateTime.to_jalali(obj.created_at).strftime("%Y/%m/%d %H:%M")

    def get_paid_at_jalali(self, obj):
        if obj.paid_at:
            return JalaliDateTime.to_jalali(obj.paid_at).strftime("%Y/%m/%d %H:%M")
        return None


class TransactionUserListSerializer(serializers.ModelSerializer):
    fee = serializers.SerializerMethodField()
    calculated_amount = serializers.SerializerMethodField()
    created_at_jalali = serializers.SerializerMethodField()
    concert_name = serializers.SerializerMethodField()

    class Meta:
        model = Transaction
        fields = [
            "id",
            "transaction_no",
            "description",
            "status",
            "amount",
            "calculated_amount",
            "fee",
            "created_at_jalali",
            "concert_name",
        ]
        read_only_fields = fields

    def get_fee(self, obj):
        return str(obj.fee)

    def get_calculated_amount(self, obj):
        return str(obj.calculated_amount)

    def get_created_at_jalali(self, obj):
        return JalaliDateTime.to_jalali(obj.created_at).strftime("%Y/%m/%d %H:%M")

    def get_concert_name(self, obj):
        if obj.booking and hasattr(obj.booking, "concert"):
            return obj.booking.concert.name
        return None


class TransactionDetailSerializer(serializers.ModelSerializer):
    user_detail = serializers.SerializerMethodField()
    booking_detail = serializers.SerializerMethodField()
    tickets_detail = serializers.SerializerMethodField()
    payment_receipt = PaymentReceiptSerializer(read_only=True)

    class Meta:
        model = Transaction
        fields = [
            "id",
            "transaction_no",
            "user_detail",
            "booking_detail",
            "tickets_detail",
            "amount",
            "discount_amount",
            "fee",
            "bank_name",
            "card_number",
            "ref_number",
            "track_id",
            "gateway",
            "status",
            "payment_receipt",
            "description",
            "created_at",
            "paid_at",
        ]

    def get_user_detail(self, obj):
        if not obj.user:
            return None
        return {
            "id": obj.user.id,
            "full_name": f"{obj.user.first_name} {obj.user.last_name}",
            "mobile": getattr(obj.user, "mobile", ""),
            "email": obj.user.email,
        }

    def get_booking_detail(self, obj):
        if not obj.booking:
            return None
        return {
            "id": obj.booking.id,
            "concert": (
                obj.booking.concert.name if hasattr(obj.booking, "concert") else None
            ),
            "concert_date": (
                str(obj.booking.concert.date)
                if hasattr(obj.booking, "concert")
                else None
            ),
            "total_amount": str(obj.booking.total_amount),
            "is_paid": obj.booking.is_paid,
        }

    def get_tickets_detail(self, obj):
        if not obj.booking or not hasattr(obj.booking, "tickets"):
            return []

        tickets = obj.booking.tickets.all()
        return TicketSerializer(tickets, many=True).data
