from uuid import uuid4
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from location_field.models.plain import PlainLocationField as LocationField
from common.models import SoftDeleteManager


class Country(models.Model):
    id = models.UUIDField(
        verbose_name="unique id",
        primary_key=True,
        unique=True,
        default=uuid4,
        editable=False,
    )
    label = models.CharField(
        "label", max_length=100, null=True, blank=True, unique=True
    )
    created_at = models.DateTimeField(verbose_name="created at", default=timezone.now)
    updated_at = models.DateTimeField(verbose_name="updated at", auto_now=True)
    _is_deleted = models.BooleanField(default=False)
    _deleted_at = models.DateTimeField(null=True, blank=True)

    objects = SoftDeleteManager(alive_only=True)
    all_objects = SoftDeleteManager(alive_only=None)
    deleted_objects = SoftDeleteManager(alive_only=False)

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

    class Meta:
        verbose_name = "country"
        verbose_name_plural = "countries"
        db_table = "country"
        ordering = ("-updated_at",)
        indexes = (models.Index(fields=["label"], name="country_label_idx"),)

    def __str__(self) -> str:
        return self.label


class State(models.Model):
    id = models.UUIDField(
        verbose_name="unique id",
        primary_key=True,
        unique=True,
        default=uuid4,
        editable=False,
    )
    country = models.ForeignKey(
        Country,
        related_name="states_country",
        verbose_name=_("country"),
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    label = models.CharField(
        "label", max_length=210, null=True, blank=True, unique=True
    )
    created_at = models.DateTimeField(verbose_name="created at", default=timezone.now)
    updated_at = models.DateTimeField(verbose_name="updated at", auto_now=True)
    _is_deleted = models.BooleanField(default=False)
    _deleted_at = models.DateTimeField(null=True, blank=True)

    objects = SoftDeleteManager(alive_only=True)
    all_objects = SoftDeleteManager(alive_only=None)
    deleted_objects = SoftDeleteManager(alive_only=False)

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

    class Meta:
        verbose_name = _("state")
        verbose_name_plural = _("states")
        db_table = "state"
        ordering = ("-updated_at",)
        indexes = (models.Index(fields=["label"], name="state_label_idx"),)

    def __str__(self) -> str:
        return self.label


class City(models.Model):
    id = models.UUIDField(
        verbose_name="unique id",
        primary_key=True,
        unique=True,
        default=uuid4,
        editable=False,
    )
    state = models.ForeignKey(
        State,
        related_name="city_states",
        verbose_name=_("state"),
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    label = models.CharField("label", max_length=310, null=True, blank=True)
    created_at = models.DateTimeField(verbose_name="created at", default=timezone.now)
    updated_at = models.DateTimeField(verbose_name="updated at", auto_now=True)
    _is_deleted = models.BooleanField(default=False)
    _deleted_at = models.DateTimeField(null=True, blank=True)

    objects = SoftDeleteManager(alive_only=True)
    all_objects = SoftDeleteManager(alive_only=None)
    deleted_objects = SoftDeleteManager(alive_only=False)

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

    class Meta:
        verbose_name = _("city")
        verbose_name_plural = _("cities")
        ordering = ("-updated_at",)
        db_table = "city"
        indexes = (models.Index(fields=["label"], name="city_label_idx"),)

    def __str__(self) -> str:
        return self.label


class Branch(models.Model):
    code = models.CharField(max_length=120, blank=True, default="")
    title = models.CharField(max_length=310, blank=True, default="")
    address = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)
    mobile = models.CharField(max_length=11, blank=True)
    location = LocationField(based_fields=["address"], zoom=15, blank=True, null=True)
    city = models.ForeignKey(
        City, related_name="branches", on_delete=models.CASCADE, null=True, blank=True
    )
    created_at = models.DateTimeField(verbose_name="created at", default=timezone.now)
    updated_at = models.DateTimeField(verbose_name="updated at", auto_now=True)
    _is_deleted = models.BooleanField(default=False)
    _deleted_at = models.DateTimeField(null=True, blank=True)

    objects = SoftDeleteManager(alive_only=True)
    all_objects = SoftDeleteManager(alive_only=None)
    deleted_objects = SoftDeleteManager(alive_only=False)

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

    class Meta:
        verbose_name = _("branch")
        verbose_name_plural = _("branches")
        ordering = ("-updated_at",)
        db_table = "branch"
        indexes = (
            models.Index(fields=["title"], name="branch_title_idx"),
            models.Index(fields=["code"], name="branch_code_idx"),
            models.Index(fields=["is_active"], name="branch_active_idx"),
        )

    def __str__(self):
        return f"{self.title} - {self.city}"
