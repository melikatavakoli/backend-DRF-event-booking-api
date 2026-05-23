from address.models import City, Country, State
from common.format import calculate_age, common_datetime_str
from common.managers import UserManager
from django.db import models
from core.choices import RoleType, StatusType
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils import timezone
from uuid import uuid4


class CoreUser(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(
        "unique id",
        primary_key=True,
        unique=True,
        null=False,
        default=uuid4,
        editable=False,
    )
    Username = None
    mobile = models.CharField(max_length=15, unique=True)
    email = models.EmailField(blank=True, default="")
    birth_date = models.DateField(blank=True, null=True)
    role = models.CharField(
        max_length=1, choices=RoleType.choices, default=RoleType.PATIENT
    )
    description = models.TextField(blank=True, default="")
    password_updated_at = models.DateTimeField(blank=True, null=True)
    state = models.ForeignKey(State, on_delete=models.SET_NULL, null=True, blank=True)
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True)
    country = models.ForeignKey(
        Country, on_delete=models.SET_NULL, null=True, blank=True
    )
    is_verified = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    is_staff = models.BooleanField(default=False)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    status = models.CharField(
        max_length=20, choices=StatusType.choices, default=StatusType.ACTIVE
    )
    _is_deleted = models.BooleanField(default=False)
    _deleted_at = models.DateTimeField(null=True, blank=True)
    objects = UserManager(alive_only=True)
    all_objects = UserManager(alive_only=None)
    deleted_objects = UserManager(alive_only=False)
    avatar = models.ImageField(upload_to="upload_to_by_date", null=True, blank=True)
    national_code = models.CharField(max_length=10, blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    def delete(self, using=None, keep_parents=False):
        self._is_deleted = True
        self._deleted_at = timezone.now()
        self.save(update_fields=["_is_deleted", "_deleted_at"])

    def hard_delete(self, using=None, keep_parents=False):
        super().delete(using=using, keep_parents=keep_parents)

    def restore(self):
        self._is_deleted = False
        self._deleted_at = None
        self.save()

    UserNAME_FIELD = "mobile"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    class Meta:
        verbose_name = "base_User"
        verbose_name_plural = "base_Users"
        db_table = "base_User"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    @property
    def full_name(self):
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name if full_name else "Anonymous"

    @property
    def age(self):
        return calculate_age(self.birth_date)

    @property
    def created_at_display(self):
        return common_datetime_str(self.created_at)

    @property
    def is_patient(self):
        return self.role == RoleType.PATIENT

    @property
    def is_doctor(self):
        return self.role == RoleType.DOCTOR

    @property
    def is_staff_User(self):
        return self.role in [RoleType.ADMIN]
