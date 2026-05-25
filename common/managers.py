from django.db import models
from django.utils import timezone
from core.types import RoleType


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


class UserManager(SoftDeleteManager):
    use_in_migrations = True

    def __init__(self, alive_only=True, *args, **kwargs):
        self.alive_only = alive_only
        super().__init__(*args, **kwargs)
    
    def get_queryset(self):
        if self.alive_only is True:
            return super().get_queryset().filter(_is_deleted=False)
        elif self.alive_only is False:
            return super().get_queryset().filter(_is_deleted=True)
        return super().get_queryset()
    
    def create_user(self, mobile, password=None, **extra_fields):
        if not mobile:
            raise ValueError('شماره موبایل الزامی است')
        
        user = self.model(mobile=mobile, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, mobile, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', RoleType.ADMIN)
        extra_fields.setdefault('is_active', True)
        
        return self.create_user(mobile, password, **extra_fields)
    
    def create_staffuser(self, mobile, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('role', RoleType.STAFF)
        extra_fields.setdefault('is_active', True)
        return self.create_user(mobile, password, **extra_fields)
