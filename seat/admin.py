from django.contrib import admin
from .models import Prefix, Suffix, Seat


@admin.register(Prefix)
class PrefixAdmin(admin.ModelAdmin):
    list_display = ("id", "title",)
    search_fields = ("title",)


@admin.register(Suffix)
class SuffixAdmin(admin.ModelAdmin):
    list_display = ("id", "title",)
    search_fields = ("title",)


@admin.register(Seat)
class SeatAdmin(admin.ModelAdmin):
    list_display = ("id", "prefix", "suffix",)
    search_fields = ("prefix__title", "suffix__title")
    list_filter = ( "prefix", "suffix")