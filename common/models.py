from uuid import uuid4
from functools import cached_property
from django.db import models
from django.utils import timezone
from common.managers import SoftDeleteManager
from .format import common_datetime_str
from django_currentuser.db.models import CurrentUserField
from auditlog.registry import auditlog
from django.db.models.base import ModelBase
from django.db import transaction
from django.utils.translation import gettext_lazy as _


class AuditLogModelBase(ModelBase):
    def __new__(cls, name, bases, attrs, **kwargs):
        new_class = super().__new__(cls, name, bases, attrs, **kwargs)
        if not new_class._meta.abstract:
            auditlog.register(new_class)
        return new_class


class GenericModel(models.Model, metaclass=AuditLogModelBase):
    id = models.UUIDField(
        verbose_name=_("unique id"),
        primary_key=True,
        unique=True,
        null=False,
        default=uuid4,
        editable=False,
    )
    _created_by = CurrentUserField(
        related_name="%(app_label)s_%(class)s_created_by",
        verbose_name=_("created by"),
    )
    _updated_by = CurrentUserField(
        related_name="%(app_label)s_%(class)s_updated_by",
        verbose_name=_("updated by"),
        on_update=True,
    )
    _created_at = models.DateTimeField(
        verbose_name=_("created at"), default=timezone.now
    )
    _updated_at = models.DateTimeField(verbose_name=_("updated at"), auto_now=True)
    _is_deleted = models.BooleanField(default=False)
    _deleted_at = models.DateTimeField(null=True, blank=True)
    objects = SoftDeleteManager(alive_only=True)
    all_objects = SoftDeleteManager(alive_only=None)
    deleted_objects = SoftDeleteManager(alive_only=False)

    @classmethod
    def get_or_restore(cls, defaults=None, **kwargs):
        with transaction.atomic():
            instance = cls.all_objects.filter(**kwargs).first()
            if instance:
                restored = False
                if instance._is_deleted:
                    instance.restore()
                    restored = True
                if defaults:
                    for key, value in defaults.items():
                        setattr(instance, key, value)
                    instance.save(update_fields=list(defaults.keys()))
                return instance, False, restored
            instance, created = cls.objects.get_or_create(defaults=defaults, **kwargs)
            return instance, created, False

    @classmethod
    def update_or_restore(cls, defaults=None, **kwargs):
        with transaction.atomic():
            instance = cls.all_objects.filter(**kwargs).first()
            if instance:
                restored = False
                if instance._is_deleted:
                    instance.restore()
                    restored = True
                if defaults:
                    for key, value in defaults.items():
                        setattr(instance, key, value)
                    instance.save(update_fields=list(defaults.keys()))
                return instance, False, restored
            instance, created = cls.objects.update_or_create(
                defaults=defaults, **kwargs
            )
            return instance, created, False

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

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=["id"], name="id_idx"),
        ]

    @property
    def created_by(self):
        if self._created_by:
            return (
                f"{self._created_by.first_name} {self._created_by.last_name}".strip()
                or self._created_by.mobile
            )
        return None

    @property
    def updated_by(self):
        if self._updated_by:
            return (
                f"{self._updated_by.first_name} {self._updated_by.last_name}".strip()
                or self._updated_by.mobile
            )
        return None

    @property
    def created_at(self):
        return common_datetime_str(self._created_at)

    @property
    def updated_at(self):
        return common_datetime_str(self._updated_at)

    @cached_property
    def can_delete(self):
        for field in self._meta.related_objects:
            try:
                if getattr(self, field.related_name).all().exists():
                    return False
            except Exception:
                pass
        return True
