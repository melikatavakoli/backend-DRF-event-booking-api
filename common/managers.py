from django.db import models
from django.utils import timezone
from django.contrib.auth.models import BaseUserManager
from core.choices import RoleType


class SoftDeleteQuerySet(models.QuerySet):
    def delete(self):
        return super().update(_is_deleted=True, _deleted_at=timezone.now())

    def hard_delete(self):
        return super().delete()

    def alive(self):
        return self.filter(_is_deleted=False)

    def dead(self):
        return self.filter(_is_deleted=True)


class SoftDeleteManager(models.Manager):
    def __init__(self, *args, **kwargs):
        self.alive_only = kwargs.pop("alive_only", None)
        super().__init__(*args, **kwargs)

    def get_queryset(self):
        if self.alive_only is True:
            return SoftDeleteQuerySet(self.model).filter(_is_deleted=False)
        if self.alive_only is False:
            return SoftDeleteQuerySet(self.model).filter(_is_deleted=True)
        if self.alive_only is None:
            return SoftDeleteQuerySet(self.model)

    def hard_delete(self):
        return self.get_queryset().hard_delete()


class UserManager(BaseUserManager, SoftDeleteManager):
    use_in_migrations = True

    def _create_user(self, mobile, password, **extra_fields):
        if not mobile:
            raise ValueError("mobile must be set")
        user = self.model(mobile=mobile, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, mobile, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(mobile, password, **extra_fields)

    def create_superuser(self, mobile, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", RoleType.ADMIN)
        return self._create_user(mobile, password, **extra_fields)
