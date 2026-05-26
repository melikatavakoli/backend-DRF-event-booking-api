from django.db import models


class RoleType(models.TextChoices):
    CUSTOMER = "C", "customer"
    STAFF = "S", "staff"
    ADMIN = "A", "admin"


class StatusType(models.TextChoices):
    ACTIVE = "A", "active"
    INACTIVE = "I", "inactive"
    BANNED = "B", "banned"
    PENDING = "P", "pending"
