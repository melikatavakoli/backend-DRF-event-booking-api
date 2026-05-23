from django.db import models


class RoleType(models.TextChoices):
    PATIENT = "P", "patient"
    Doctor = "D", "doctor"
    ADMIN = "A", "admin"


class StatusType(models.TextChoices):
    ACTIVE = "A", "active"
    INACTIVE = "I", "inactive"
    BANNED = "B", "banned"
    PENDING = "P", "pending"
