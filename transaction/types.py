from django.db import models

class TransactionStatus(models.TextChoices):
    pending = 'pending', 'Pending'
    approved = 'approved', 'Approved'
    failed = 'failed', 'Failed'
    success = 'success', 'Success'