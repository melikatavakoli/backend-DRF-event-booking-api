from django.contrib import admin
from .models import Invoice, InvoiceItem

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = [
        "invoice_number",
        "tracking_code",
        "user",
        "final_amount",
        "status",
        "issue_date",
    ]
    list_filter = ["status", "issue_date", "_created_at"]
    search_fields = [
        "invoice_number",
        "tracking_code",
    ]
    readonly_fields = [
        "invoice_number",
        "tracking_code",
        "_created_at",
        "_updated_at",
    ]
    ordering = ["_created_at"]

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj._created_by = request.user
        obj._updated_by = request.user
        super().save_model(request, obj, form, change)

    actions = ["mark_as_paid", "mark_as_unpaid"]

    @admin.action(description="Mark selected invoices as paid")
    def mark_as_paid(self, request, queryset):
        updated = queryset.update(status="paid")
        self.message_user(request, f"{updated} invoice(s) marked as paid.")

    @admin.action(description="Mark selected invoices as unpaid")
    def mark_as_unpaid(self, request, queryset):
        updated = queryset.update(status="unpaid")
        self.message_user(request, f"{updated} invoice(s) marked as unpaid.")


@admin.register(InvoiceItem)
class ItemAdmin(admin.ModelAdmin):
    list_display = ["id", "invoice","quantity", "unit_price"]
    list_filter = ["_created_at"]
    search_fields = ["description", "invoice__invoice_number"]
    readonly_fields = ["_created_at", "_updated_at"]
