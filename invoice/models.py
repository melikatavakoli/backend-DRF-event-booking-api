from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone
from decimal import Decimal

from booking.models import Booking
from common.models import GenericModel
from .choices import InvoiceStatus
from ticket.models import Ticket
from transaction.models import Transaction

User = get_user_model()


class Invoice(GenericModel):
    user = models.ForeignKey(
        User,
        related_name="invoices",
        verbose_name="user",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    booking = models.ForeignKey(
        Booking,
        related_name="invoices",
        verbose_name="booking",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    transaction = models.ForeignKey(
        Transaction,
        related_name="invoices",
        verbose_name="transaction",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    invoice_number = models.CharField(
        max_length=50, unique=True, blank=True, null=True, editable=False
    )
    tracking_code = models.CharField(max_length=50, blank=True, null=True)
    issue_date = models.DateTimeField(default=timezone.now)
    description = models.CharFIeld(max_length=1000, blank=True, null=True)
    status = models.CharField(
        max_length=10,
        choices=InvoiceStatus.choices,
        default=InvoiceStatus.unpaid,
    )
    subtotal = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    tax_amount = models.DecimalField(
        max_digits=12, decimal_places=0, default=0
    )
    discount_amount = models.DecimalField(
        max_digits=12, decimal_places=0, default=0
    )
    final_amount = models.DecimalField(
        max_digits=12, decimal_places=0, default=0
    )

    class Meta:
        verbose_name = "invoice"
        verbose_name_plural = "invoices"
        db_table = "invoice"
        ordering = ["-issue_date"]

    def __str__(self):
        return f"{self.invoice_number} - {self.user}"

    def calculate_total(self):
        """محاسبه مجموع مبلغ از آیتم‌ها"""
        total = Decimal("0")
        for item in self.items.all():
            total += Decimal(item.final_price or 0)
        return total

    def calculate_tax(self, amount, tax_percent=9):
        """محاسبه مالیات"""
        return (amount * Decimal(tax_percent) / Decimal("100")).quantize(
            Decimal("0")
        )

    def update_totals(self):
        """بروزرسانی مبالغ فاکتور"""
        self.subtotal = self.calculate_total()
        self.tax_amount = self.calculate_tax(self.subtotal)
        self.final_amount = (
            self.subtotal + self.tax_amount - self.discount_amount
        )
        self.save(update_fields=["subtotal", "tax_amount", "final_amount"])

    def save(self, *args, **kwargs):
        from invoice.services import (
            generate_invoice_number,
            generate_tracking_code,
        )

        if not self.invoice_number:
            self.invoice_number = generate_invoice_number()
        if not self.tracking_code:
            self.tracking_code = generate_tracking_code()

        super().save(*args, **kwargs)


class InvoiceItem(GenericModel):
    invoice = models.ForeignKey(
        Invoice,
        related_name="items",
        verbose_name="invoice",
        on_delete=models.CASCADE,
    )
    ticket = models.ForeignKey(
        Ticket,
        related_name="invoice_items",
        verbose_name="ticket",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=0)
    discount_percent = models.DecimalField(
        max_digits=5, decimal_places=2, default=0
    )
    discount_amount = models.DecimalField(
        max_digits=12, decimal_places=0, default=0
    )
    tax_percent = models.DecimalField(
        max_digits=5, decimal_places=2, default=9
    )
    tax_amount = models.DecimalField(
        max_digits=12, decimal_places=0, default=0
    )
    final_price = models.DecimalField(
        max_digits=12, decimal_places=0, default=0
    )

    class Meta:
        verbose_name = "invoice_item"
        verbose_name_plural = "invoice_items"
        db_table = "invoice_item"
        ordering = ["row_number"]

    def __str__(self):
        return f"{self.seat_number} - {self.category_name}"

    def calculate_final_price(self):
        """محاسبه قیمت نهایی هر آیتم"""
        base_price = Decimal(self.unit_price) * Decimal(self.quantity)

        discount = Decimal("0")
        if self.discount_percent > 0:
            discount = base_price * (self.discount_percent / Decimal("100"))
        elif self.discount_amount > 0:
            discount = self.discount_amount

        price_after_discount = base_price - discount

        tax = price_after_discount * (self.tax_percent / Decimal("100"))

        self.discount_amount = discount
        self.tax_amount = tax
        self.final_price = price_after_discount + tax

        return self.final_price

    def save(self, *args, **kwargs):
        self.calculate_final_price()
        super().save(*args, **kwargs)
        if self.invoice:
            self.invoice.update_totals()

