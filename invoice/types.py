from django.db import models

class InvoiceStatus(models.TextChoices):
    unpaid = 'unpaid', 'Unpaid'
    paid = 'paid', 'Paid'
    cancelled = 'cancelled', 'Cancelled'
    refunded = 'refunded', 'Refunded'