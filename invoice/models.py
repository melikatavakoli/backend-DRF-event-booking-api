from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone
from decimal import Decimal, InvalidOperation
from django.utils.translation import gettext_lazy as _
from common.models import GenericModel
from invoice.types import InvoiceStatus
from order.models import Order
from product.models import Product
User = get_user_model()

class Invoice(GenericModel):
    invoice_number = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        null=True,
        editable=False
    )
    tracking_code = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )
    issue_date = models.DateTimeField(
        default=timezone.now,
        blank=True,
        null=True
    )
    invoice_date = models.DateTimeField(
        default=timezone.now,
        blank=True,
        null=True
    )
    user = models.ForeignKey(
        User,
        related_name="invoice_user",
        verbose_name="user",
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    product = models.ForeignKey(
        Product,
        related_name="invoice_product",
        verbose_name="product",
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    order = models.ForeignKey(
        Order,
        related_name="invoice_order",
        verbose_name="order",
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    fiscal_memory_number = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )
    fiscal_memory_serial = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )
    pos_serial = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )
    description = models.TextField(
        blank=True,
        null=True
    )
    status = models.CharField(
        max_length=10,
        choices=InvoiceStatus.choices,
        default=InvoiceStatus.unpaid,
    )
    final_amount = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        default="0"
    )

    @property
    def final_amount(self):
        total = Decimal("0")
        for item in self.items.all():
            try:
                quantity = Decimal(item.quantity or "0")
                unit_price = Decimal(item.unit_price or "0")
                total_price = quantity * unit_price
                
                discount_percent = Decimal(item.discount_percent or "0")
                discount_amount = Decimal(item.discount_amount or "0")
                
                if discount_percent > 0:
                    discount_amount = total_price * (discount_percent / Decimal("100"))
                
                total_after_discount = total_price - discount_amount
                tax = total_after_discount * Decimal("0.09")
                final_price_item = total_after_discount + tax
                
                total += final_price_item
            except:
                continue
        
        return str(total.quantize(Decimal("0.01")))
    
    class Meta:
        verbose_name_plural = 'invoices'
        verbose_name = 'invoice'
        db_table = 'invoice'

    def __str__(self):
        return f"{self.invoice_number} - {self.user}"

    def save(self, *args, **kwargs):
        from invoice.services import generate_invoice_number, generate_tracking_code
        if not self.invoice_number:
            self.invoice_number = generate_invoice_number()
        if not self.tracking_code:
            self.tracking_code = generate_tracking_code()
        super().save(*args, **kwargs)


class Item(BaseModel):
    TAX_PERCENT = Decimal("0.09") 
    
    invoice = models.ForeignKey(
        Invoice,
        related_name="items",
        verbose_name="invoice",
        on_delete=models.CASCADE,
        blank=True,
        null=True
    )
    row_number = models.PositiveIntegerField(
        null=True, 
        blank=True
        )
    product_code = models.CharField(
        max_length=50, 
        blank=True, 
        null=True
        )
    description = models.TextField(
        null=True, 
        blank=True
        )
    quantity = models.CharField(
        max_length=100, 
        blank=True, 
        null=True
        )
    unit_price = models.CharField( 
        max_length=100, 
        blank=True, 
        null=True
    )
    discount_amount = models.CharField( 
        max_length=100, 
        blank=True, 
        null=True
    )
    discount_percent = models.CharField( 
        max_length=100, 
        blank=True, 
        null=True
    )
    total_price = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )
    final_price = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )
    
    class Meta:
        verbose_name_plural = '02-invoice_items'
        verbose_name = '02-invoice_item'
        db_table = 'invoice_item'

    def __str__(self):
        return f"Item {self.product_code} ({self.description})"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)