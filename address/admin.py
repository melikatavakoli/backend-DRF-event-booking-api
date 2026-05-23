from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import City, Country, State
from common.admin import BaseAdmin


@admin.register(Country)
class CountryAdmin(BaseAdmin):
    list_display = ["label", "created_at", "updated_at"]
    # list_filter = ["is_active"]
    search_fields = ["label"]
    ordering = ["label"]
    readonly_fields = ["id", "created_at", "updated_at", "_is_deleted", "_deleted_at"]


@admin.register(State)
class StateAdmin(BaseAdmin):
    list_display = ["label", "country", "created_at", "updated_at"]
    list_filter = [
        "country",
    ]
    search_fields = ["label", "country__label"]
    ordering = ["country__label", "label"]
    readonly_fields = ["id", "created_at", "updated_at", "_is_deleted", "_deleted_at"]


@admin.register(City)
class CityAdmin(BaseAdmin):
    list_display = ["label", "state", "created_at", "updated_at"]
    list_filter = ["state", "state__country"]
    search_fields = ["label", "state__label", "state__country__label"]
    ordering = ["state__country__label", "state__label", "label"]
    readonly_fields = ["id", "created_at", "updated_at", "_is_deleted", "_deleted_at"]