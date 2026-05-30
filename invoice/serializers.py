from rest_framework import serializers
from persiantools.jdatetime import JalaliDateTime
from django.contrib.auth import get_user_model

from .models import Invoice, InvoiceItem
from .choices import InvoiceStatus
from ticket.serializers import TicketSerializer

User = get_user_model()


class InvoiceItemSerializer(serializers.ModelSerializer):
    ticket_detail = TicketSerializer(source="ticket", read_only=True)

    class Meta:
        model = InvoiceItem
        fields = [
            "id",
            "ticket",
            "ticket_detail",
            "quantity",
            "unit_price",
            "discount_percent",
            "discount_amount",
            "tax_percent",
            "tax_amount",
            "final_price",
        ]
        read_only_fields = ["discount_amount", "tax_amount", "final_price"]


class InvoiceItemWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceItem
        fields = [
            "ticket",
            "quantity",
            "unit_price",
            "discount_percent",
            "tax_percent",
        ]

    def validate(self, data):
        if data.get("quantity", 1) < 1:
            raise serializers.ValidationError(
                {"quantity": "تعداد باید حداقل 1 باشد"}
            )

        if data.get("unit_price", 0) < 0:
            raise serializers.ValidationError(
                {"unit_price": "قیمت واحد نمی‌تواند منفی باشد"}
            )

        if (
            data.get("discount_percent", 0) < 0
            or data.get("discount_percent", 0) > 100
        ):
            raise serializers.ValidationError(
                {"discount_percent": "درصد تخفیف باید بین 0 تا 100 باشد"}
            )

        return data


class InvoiceSerializer(serializers.ModelSerializer):
    user_detail = serializers.SerializerMethodField()
    booking_detail = serializers.SerializerMethodField()
    transaction_detail = serializers.SerializerMethodField()
    items = InvoiceItemSerializer(many=True, read_only=True)
    issue_date_jalali = serializers.SerializerMethodField()
    created_at_jalali = serializers.SerializerMethodField()

    class Meta:
        model = Invoice
        fields = [
            "id",
            "invoice_number",
            "tracking_code",
            "user",
            "user_detail",
            "booking",
            "booking_detail",
            "transaction",
            "transaction_detail",
            "issue_date",
            "issue_date_jalali",
            "description",
            "status",
            "subtotal",
            "tax_amount",
            "discount_amount",
            "final_amount",
            "items",
            "_created_at",
            "created_at_jalali",
        ]
        read_only_fields = [
            "invoice_number",
            "tracking_code",
            "subtotal",
            "tax_amount",
            "final_amount",
        ]

    def get_user_detail(self, obj):
        if not obj.user:
            return None
        return {
            "id": str(obj.user.id),
            "full_name": obj.user.full_name,
            "mobile": getattr(obj.user, "mobile", ""),
            "email": obj.user.email,
        }

    def get_booking_detail(self, obj):
        if not obj.booking:
            return None
        return {
            "id": obj.booking.id,
            "concert_name": (
                obj.booking.concert.name
                if hasattr(obj.booking, "concert")
                else None
            ),
            "concert_date": (
                str(obj.booking.concert.date)
                if hasattr(obj.booking, "concert")
                else None
            ),
            "total_tickets": (
                obj.booking.tickets.count()
                if hasattr(obj.booking, "tickets")
                else 0
            ),
        }

    def get_transaction_detail(self, obj):
        if not obj.transaction:
            return None
        return {
            "id": obj.transaction.id,
            "transaction_no": obj.transaction.transaction_no,
            "status": obj.transaction.status,
            "payment_method": obj.transaction.payment_method,
        }

    def get_issue_date_jalali(self, obj):
        if obj.issue_date:
            return JalaliDateTime.to_jalali(obj.issue_date).strftime(
                "%Y/%m/%d %H:%M"
            )
        return None

    def get_created_at_jalali(self, obj):
        if obj._created_at:
            return JalaliDateTime.to_jalali(obj._created_at).strftime(
                "%Y/%m/%d %H:%M"
            )
        return None


class InvoiceListSerializer(serializers.ModelSerializer):
    user_full_name = serializers.SerializerMethodField()
    issue_date_jalali = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(source='_created_at', read_only=True)
    created_at_jalali = serializers.SerializerMethodField()
    concert_name = serializers.SerializerMethodField()

    class Meta:
        model = Invoice
        fields = [
            "id",
            "invoice_number",
            "tracking_code",
            "user_full_name",
            "concert_name",
            "issue_date",
            "issue_date_jalali",
            "status",
            "final_amount",
            "created_at",
            "created_at_jalali",
        ]

    def get_user_full_name(self, obj):
        if obj.user:
            return obj.user.full_name
        return None

    def get_issue_date_jalali(self, obj):
        if obj.issue_date:
            return JalaliDateTime.to_jalali(obj.issue_date).strftime(
                "%Y/%m/%d"
            )
        return None

    def get_created_at_jalali(self, obj):
        if obj._created_at:
            return JalaliDateTime.to_jalali(obj._created_at).strftime(
                "%Y/%m/%d %H:%M"
            )
        return None

    def get_concert_name(self, obj):
        if obj.booking and hasattr(obj.booking, "concert"):
            return obj.booking.concert.name
        return None


class InvoiceWriteSerializer(serializers.ModelSerializer):
    items = InvoiceItemWriteSerializer(many=True, required=False)

    class Meta:
        model = Invoice
        fields = [
            "booking",
            "transaction",
            "description",
            "status",
            "discount_amount",
            "items",
        ]

    def validate_booking(self, value):
        if not value:
            raise serializers.ValidationError("رزرو الزامی است")

        user = self.context["request"].user
        if value.user != user:
            raise serializers.ValidationError("این رزرو متعلق به شما نیست")

        return value

    def validate_transaction(self, value):
        if value and value.user != self.context["request"].user:
            raise serializers.ValidationError("این تراکنش متعلق به شما نیست")
        return value

    def validate_status(self, value):
        valid_statuses = [
            InvoiceStatus.paid,
            InvoiceStatus.unpaid,
            InvoiceStatus.cancelled,
        ]
        if value not in valid_statuses:
            raise serializers.ValidationError(
                f"وضعیت باید یکی از {valid_statuses} باشد"
            )
        return value

    def validate_discount_amount(self, value):
        if value < 0:
            raise serializers.ValidationError(
                "مبلغ تخفیف نمی‌تواند منفی باشد"
            )
        return value

    def create(self, validated_data):
        items_data = validated_data.pop("items", [])
        validated_data["user"] = self.context["request"].user
        validated_data["subtotal"] = 0
        validated_data["tax_amount"] = 0
        validated_data["final_amount"] = 0

        invoice = Invoice.objects.create(**validated_data)

        for item_data in items_data:
            if item_data.get("ticket"):
                ticket = item_data["ticket"]
                item_data["unit_price"] = (
                    ticket.category.price
                    if ticket.category
                    else item_data.get("unit_price", 0)
                )

            InvoiceItem.objects.create(invoice=invoice, **item_data)

        invoice.update_totals()

        if invoice.transaction and invoice.transaction.is_successful:
            invoice.status = InvoiceStatus.paid
            invoice.save(update_fields=["status"])

        return invoice


class InvoiceStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = ["status"]

    def validate_status(self, value):
        if value not in [
            InvoiceStatus.paid,
            InvoiceStatus.cancelled,
            InvoiceStatus.refunded,
        ]:
            raise serializers.ValidationError("وضعیت نامعتبر است")

        if self.instance.status == InvoiceStatus.paid:
            raise serializers.ValidationError("فاکتور قبلاً پرداخت شده است")

        if self.instance.status == InvoiceStatus.cancelled:
            raise serializers.ValidationError("فاکتور قبلاً لغو شده است")

        return value
