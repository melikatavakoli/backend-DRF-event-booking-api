from import_export import resources
from django.contrib import admin
from .models import Ticket
from common.admin import BaseAdmin, SoftDeleteListFilter


class TicketResource(resources.ModelResource):

    class Meta:
        model = Ticket
        fields = (
            "id",
            "code",
            "category",
            "booking",
            "seat",
            "_is_deleted",
        )
        import_id_fields = ["code"]


@admin.register(Ticket)
class TicketAdmin(BaseAdmin):
    model = Ticket
    resource_class = TicketResource

    list_display = (
        "code",
        "booking_info",
        "_is_deleted",
        "_created_at",
    )

    list_editable = (
    )

    search_fields = (
        "code",
        "booking__id",
        "booking__user__mobile",
        "seat__seat_number",
        "id",
    )

    list_filter = (
        SoftDeleteListFilter,
        "booking__show",
        "_is_deleted",
    )

    readonly_fields = (
        "id",
        "code",
        "_deleted_at",
        "_created_at",
        "_updated_at",
        "booking_info",
        "_created_by",
        "_updated_by",
    )

    ordering = ("_created_at",)

    def booking_info(self, obj):
        """Display booking information"""
        if obj.booking:
            return f"{obj.booking.id} - {obj.booking.status}"
        return "-"
    booking_info.short_description = "Booking"
    booking_info.admin_order_field = "booking"

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            obj.delete()

    def delete_model(self, request, obj):
        obj.delete()

    actions = ["generate_codes_for_selected"]

    @admin.action(description="Generate/Regenerate ticket codes for selected")
    def generate_codes_for_selected(self, request, queryset):
        regenerated = 0
        for ticket in queryset:
            if not ticket.code or request.POST.get('force_regenerate'):
                ticket.save()
                regenerated += 1
        self.message_user(
            request, 
            f"Successfully generated codes for {regenerated} tickets."
        )


class TicketInline(admin.TabularInline):
    """Inline tickets in booking admin"""
    model = Ticket
    extra = 0
    fields = ("code", "category", "seat", "created_at")
    readonly_fields = ("code", "_created_at")
    can_delete = True
    show_change_link = True

    def has_add_permission(self, request, obj=None):
        return obj is not None

