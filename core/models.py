from address.models import City, Country, State
from common.managers import UserManager
from django.db import models
from core.types import RoleType, StatusType
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils import timezone
from uuid import uuid4


class CoreUser(AbstractBaseUser, PermissionsMixin):
    username = None
    id = models.UUIDField(
        "unique id",
        primary_key=True,
        unique=True,
        null=False,
        default=uuid4,
        editable=False,
    )
    groups = models.ManyToManyField(
        "auth.Group",
        related_name="core_user_groups",
        blank=True,
        verbose_name="groups",
    )
    user_permissions = models.ManyToManyField(
        "auth.Permission",
        related_name="core_user_permissions",
        blank=True,
        verbose_name="user permissions",
    )

    mobile = models.CharField(max_length=11, unique=True)
    email = models.EmailField(blank=True, default="")

    birth_date = models.DateField(blank=True, null=True)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)

    role = models.CharField(
        max_length=1, choices=RoleType.choices, default=RoleType.CUSTOMER
    )
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    description = models.TextField(blank=True, default="")
    state = models.ForeignKey(State, on_delete=models.SET_NULL, null=True, blank=True)
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True)
    country = models.ForeignKey(
        Country, on_delete=models.SET_NULL, null=True, blank=True
    )

    status = models.CharField(
        max_length=20, choices=StatusType.choices, default=StatusType.ACTIVE
    )
    _is_deleted = models.BooleanField(default=False)
    _deleted_at = models.DateTimeField(null=True, blank=True)
    password_updated_at = models.DateTimeField(null=True, blank=True, auto_now_add=True)

    objects = UserManager(alive_only=True)
    all_objects = UserManager(alive_only=None)
    deleted_objects = UserManager(alive_only=False)

    USERNAME_FIELD = "mobile"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    class Meta:
        verbose_name = "core_user"
        verbose_name_plural = "core_users"
        db_table = "core_user"

    def __str__(self):
        return f"{self.mobile} - {self.full_name}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def delete(self, using=None, keep_parents=False):
        self._is_deleted = True
        self._deleted_at = timezone.now()
        self.save(using=using)

    def hard_delete(self, using=None, keep_parents=False):
        super().delete(using=using, keep_parents=keep_parents)

    def restore(self):
        self._is_deleted = False
        self._deleted_at = None
        self.save()

    @property
    def full_name(self):
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name if full_name else "Anonymous"

    @property
    def age(self):
        if self.birth_date:
            today = timezone.now().date()
            return (
                today.year
                - self.birth_date.year
                - (
                    (today.month, today.day)
                    < (self.birth_date.month, self.birth_date.day)
                )
            )
        return None

    @property
    def created_at_display(self):
        return self._created_at.strftime("%Y/%m/%d %H:%M") if self._created_at else None

    @property
    def is_customer(self):
        return self.role == RoleType.CUSTOMER

    @property
    def is_staff_user(self):
        return self.role == RoleType.STAFF

    @property
    def is_admin(self):
        return self.role == RoleType.ADMIN

    @property
    def is_super_admin(self):
        return self.role == RoleType.SUPER_ADMIN

    def has_perm(self, perm, obj=None):
        if self.is_admin:
            return True
        return super().has_perm(perm, obj)

    def has_module_perms(self, app_label):
        if self.is_admin:
            return True
        return super().has_module_perms(app_label)
