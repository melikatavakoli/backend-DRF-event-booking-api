from decimal import ROUND_HALF_UP, Decimal
from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

from booking.models import Booking
from transaction.utils import generate_random_transaction_no
from common.models import GenericModel
from .choices import TransactionStatus

User = get_user_model()


class PaymentReceipt(GenericModel):
    user = models.ForeignKey(
        User,
        related_name="receipts_user",
        verbose_name="user",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    verified_by = models.ForeignKey(
        User,
        related_name="verified_receipts",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    image = models.ImageField(upload_to="upload_to_by_date", blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    description = models.CharField(max_length=1000, blank=True, null=True)
    verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "payment_receipt"
        verbose_name = "payment_receipt"
        db_table = "payment_receipt"

    def __str__(self):
        return f"Receipt {self.user} - {self.uploaded_at}"


class Transaction(GenericModel):
    transaction_no = models.CharField(
        max_length=50, unique=True, blank=True, null=True, editable=False
    )
    user = models.ForeignKey(
        User,
        related_name="user_transactions",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    booking = models.ForeignKey(
        Booking,
        related_name="booking_transactions",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    payment_receipt = models.ForeignKey(
        PaymentReceipt,
        on_delete=models.SET_NULL,
        related_name="reciept_transactions",
        verbose_name="رسید پرداخت",
        null=True,
        blank=True,
    )
    amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    bank_name = models.CharField(max_length=50, blank=True, null=True)
    card_number = models.CharField(max_length=50, blank=True, null=True)
    ref_number = models.CharField(max_length=50, blank=True, null=True)
    track_id = models.CharField(max_length=300, blank=True, null=True)
    fee = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    gateway = models.CharField(max_length=50, blank=True, null=True)
    description = models.CharField(
        max_length=300,
        blank=True,
        null=True,
    )
    status = models.CharField(
        max_length=20,
        choices=TransactionStatus.choices,
        default=TransactionStatus.pending,
    )
    stock_reduced = models.BooleanField(
        default=False, verbose_name="Stock Reduced Flag"
    )
    discount_amount = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "transaction"
        verbose_name_plural = "transactions"
        db_table = "transaction"

    def __str__(self):
        return f"{self.transaction_no} | {self.user} | {self.status}"

    @property
    def calculated_amount(self):
        """مبلغ واقعی تراکنش: از رزرو گرفته می‌شه"""
        if self.booking and self.booking.total_amount:
            return Decimal(str(self.booking.total_amount))
        return Decimal(str(self.amount)) if self.amount else Decimal("0.00")

    @property
    def calculated_fee(self):
        """محاسبه کارمزد تراکنش: فقط برای درگاه زیبال"""
        # Only apply fee for Zibal gateway
        if self.gateway and self.gateway.lower() == 'zibal':
            fee_amount = (self.calculated_amount * Decimal("0.005")).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            return fee_amount
        return Decimal("0.00")

    @property
    def total_amount_with_fee(self):
        """مجموع مبلغ تراکنش + کارمزد"""
        return (self.calculated_amount + self.calculated_fee).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

    @property
    def net_amount(self):
        """مبلغ قابل پرداخت نهایی (مبلغ کل - تخفیف + کارمزد)"""
        base_amount = self.calculated_amount
        discount = Decimal(str(self.discount_amount)) if self.discount_amount else Decimal("0")
        amount_after_discount = base_amount - discount
        return (amount_after_discount + self.calculated_fee).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

    @property
    def is_successful(self):
        return self.status == TransactionStatus.success

    @property
    def is_pending(self):
        return self.status == TransactionStatus.pending

    @property
    def is_failed(self):
        return self.status == TransactionStatus.failed

    @property
    def is_online_payment(self):
        """آیا پرداخت آنلاین است (فقط زیبال)"""
        return self.gateway and self.gateway.lower() == 'zibal'

    @property
    def is_card_to_card(self):
        """آیا پرداخت کارت به کارت است"""
        return self.gateway and self.gateway.lower() == 'card_to_card'

    @property
    def payment_method_display(self):
        """نمایش روش پرداخت (محاسبه شده از gateway)"""
        if not self.gateway:
            return "نامشخص"
        
        gateway_mapping = {
            'zibal': 'درگاه زیبال',
            'card_to_card': 'کارت به کارت',
            'cash': 'نقدی',
            'pos': 'دستگاه POS',
        }
        return gateway_mapping.get(self.gateway.lower(), self.gateway)

    def update_fee(self):
        """بروزرسانی مقدار کارمزد در فیلد fee"""
        self.fee = self.calculated_fee
        if not self.pk:
            return
        self.save(update_fields=['fee'])

    def mark_as_successful(self, ref_number=None, track_id=None, card_number=None):
        """علامت‌گذاری تراکنش به عنوان موفق"""
        from ticket.models import Ticket
        
        self.status = TransactionStatus.success
        self.paid_at = timezone.now()
        
        if ref_number:
            self.ref_number = ref_number
        if track_id:
            self.track_id = track_id
        if card_number:
            self.card_number = card_number
        
        # Update fee before saving
        self.fee = self.calculated_fee
        self.save()
        
        if self.booking and not self.booking.is_paid:
            self.booking.is_paid = True
            self.booking.payment_time = timezone.now()
            self.booking.save()
            
            # Create tickets if tickets_data exists
            if hasattr(self.booking, 'tickets_data'):
                for ticket_data in self.booking.tickets_data.all():
                    Ticket.objects.create(
                        booking=self.booking,
                        category=ticket_data.category,
                        no_seat=ticket_data.seat_number,
                    )
            
            self.send_payment_notification()

    def mark_as_failed(self, reason=None):
        """علامت‌گذاری تراکنش به عنوان ناموفق"""
        self.status = TransactionStatus.failed
        if reason:
            self.description = reason
        self.save()

    def mark_as_pending(self):
        """بازگرداندن تراکنش به حالت pending"""
        self.status = TransactionStatus.pending
        self.paid_at = None
        self.save()

    def save(self, *args, **kwargs):
        """
        تولید شماره تراکنش خودکار و محاسبه مبلغ نهایی
        """
        # Generate transaction number if not exists
        if not self.transaction_no:
            self.transaction_no = generate_random_transaction_no()
        
        # Set amount from booking if not provided
        if self.booking and not self.amount:
            self.amount = self.calculated_amount
        
        # Calculate and set fee
        self.fee = self.calculated_fee
        
        super().save(*args, **kwargs)
        
    def get_payment_link(self, request):
        """دریافت لینک پرداخت برای درگاه زیبال"""
        if not self.is_online_payment:
            return None

    def verify_card_to_card_payment(self, receipt_id, admin_user):
        """تأیید پرداخت کارت به کارت توسط ادمین"""
        if not self.is_card_to_card:
            raise ValueError("این روش پرداخت برای تراکنش کارت به کارت نیست")
        
        try:
            receipt = PaymentReceipt.objects.get(id=receipt_id)
        except PaymentReceipt.DoesNotExist:
            raise ValueError("رسید پرداخت یافت نشد")
        
        self.payment_receipt = receipt
        self.mark_as_successful()
        receipt.verified = True
        receipt.verified_by = admin_user
        receipt.verified_at = timezone.now()
        receipt.save()
        return True


class DiscountCode(GenericModel):
    code = models.CharField("کد تخفیف", max_length=50, unique=True)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    max_uses = models.PositiveIntegerField("حداکثر تعداد استفاده", default=1)
    used_count = models.PositiveIntegerField("تعداد استفاده شده", default=0)
    valid_from = models.DateTimeField("معتبر از")
    valid_to = models.DateTimeField("معتبر تا")
    min_purchase_amount = models.DecimalField(
        max_digits=12, decimal_places=0, default=0
    )
    is_active = models.BooleanField("فعال", default=True)

    class Meta:
        verbose_name = "discount_code"
        verbose_name_plural = "discount_codes"
        db_table = "discount_code"

    def __str__(self):
        return f"{self.code} - {self.discount_percent}%"

    def is_valid(self, amount=None):
        """بررسی اعتبار کد تخفیف"""
        now = timezone.now()

        if not self.is_active:
            return False, "کد تخفیف غیرفعال است"

        if self.used_count >= self.max_uses:
            return False, "کد تخفیف به حداکثر استفاده رسیده است"

        if now < self.valid_from or now > self.valid_to:
            return False, "کد تخفیف منقضی شده است"

        if amount and amount < self.min_purchase_amount:
            return (
                False,
                f"حداقل مبلغ خرید برای این کد تخفیف {self.min_purchase_amount} تومان است",
            )

        return True, "کد تخفیف معتبر است"

    def apply_discount(self, amount):
        """اعمال تخفیف روی مبلغ"""
        amount_decimal = Decimal(str(amount))
        
        if self.discount_amount > 0:
            discount = Decimal(str(self.discount_amount))
            return max(Decimal("0"), amount_decimal - discount)
        elif self.discount_percent > 0:
            discount_percent = Decimal(str(self.discount_percent))
            discount = amount_decimal * (discount_percent / Decimal("100"))
            return (amount_decimal - discount).quantize(Decimal("0"), rounding=ROUND_HALF_UP)
        
        return amount_decimal

    def use(self):
        """افزایش تعداد استفاده"""
        self.used_count += 1
        self.save()