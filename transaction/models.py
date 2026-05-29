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
        if self.booking:
            return Decimal(self.booking.total_amount or 0)
        return self.amount or Decimal("0.00")

    @property
    def fee(self):
        """کارمزد تراکنش: 0.5٪ برای درگاه آنلاین"""
        if self.payment_method == "online":
            return (self.calculated_amount * Decimal("0.005")).quantize(
                Decimal("0"), rounding=ROUND_HALF_UP
            )
        return Decimal("0")

    @property
    def total_amount_with_fee(self):
        """مجموع مبلغ تراکنش + کارمزد"""
        return (self.calculated_amount + self.fee).quantize(
            Decimal("0"), rounding=ROUND_HALF_UP
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

    def mark_as_successful(self, ref_number=None, track_id=None, card_number=None):
        """علامت‌گذاری تراکنش به عنوان موفق"""
        from concert.models import Ticket

        self.status = TransactionStatus.success
        self.paid_at = timezone.now()
        if ref_number:
            self.ref_number = ref_number
        if track_id:
            self.track_id = track_id
        if card_number:
            self.card_number = card_number
        self.save()
        if self.booking and not self.booking.is_paid:
            self.booking.is_paid = True
            self.booking.payment_time = timezone.now()
            self.booking.save()
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
        if not self.transaction_no:
            self.transaction_no = generate_random_transaction_no()

        if self.booking and not self.final_amount:
            self.final_amount = self.booking.total_amount - self.discount_amount
            self.amount = self.final_amount

        if self.final_amount and not self.amount:
            self.amount = self.final_amount

        super().save(*args, **kwargs)

        if self.is_successful and self.booking and not self.booking.tickets_issued:
            self.issue_tickets()

    def send_payment_notification(self):
        """ارسال ایمیل/پیامک به کاربر"""
        from concert.notifications import send_ticket_email

        if self.user and self.user.email:
            send_ticket_email(self.user, self.booking)

    def get_payment_link(self, request):
        """دریافت لینک پرداخت برای درگاه آنلاین"""
        if self.payment_method != "online":
            return None
        from concert.payment_gateways import create_zarinpal_payment

        return create_zarinpal_payment(self, request)

    def verify_card_to_card_payment(self, receipt_id, admin_user):
        """تأیید پرداخت کارت به کارت توسط ادمین"""
        if self.payment_method != "card_to_card":
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
        verbose_name_plural = "discount_code"
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
        if self.discount_amount > 0:
            return max(0, amount - self.discount_amount)
        elif self.discount_percent > 0:
            discount = amount * (self.discount_percent / 100)
            return amount - discount
        return amount

    def use(self):
        """افزایش تعداد استفاده"""
        self.used_count += 1
        self.save()
