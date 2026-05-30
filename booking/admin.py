from django.contrib import admin
from .models import Show, Booking


@admin.register(Show)
class ShowAdmin(admin.ModelAdmin):
    list_display = ("title", "city", "state", "address")
    search_fields = ("title", "address", "city__name", "state__name")
    list_filter = ("city", "state")


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "title", "status", "date", "time", "is_paid", "is_reserved")
    list_filter = ("status", "is_paid", "is_reserved", "date")
    search_fields = ("user__mobile", "user__first_name", "user__last_name", "title")
    list_editable = ("status", "is_paid")
