from django.contrib import admin
from django.utils.html import format_html
from .models import Transaction,PaymentReceipt

@admin.register(PaymentReceipt)
class PaymentReceiptAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "preview_image", "uploaded_at", "description")
    list_filter = ("uploaded_at",)
    search_fields = ("user__username", "user__email", "user__mobile", "description")
    ordering = ("-uploaded_at",)

    def preview_image(self, obj):
        if obj.image:
            return format_html(f'<img src="{obj.image.url}" width="80" style="border-radius:8px;" />')
        return "-"
    preview_image.short_description = "Preview"

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("id", "colored_status", "user", "amount", "bank_name", "order", "payment_receipt", )
    list_filter = ("status", "gateway",)
    search_fields = ("user__username", "user__email", "user__mobile", "order__order_no", "ref_number", "track_id")
    ordering = ("-created_at",)

    def colored_status(self, obj):
        colors = {
            "APPROVED": "green",
            "REJECTED": "red",
            "FAILED": "orange",
            "CANCELLED": "gray",
            "PENDING": "blue",
            "REFUNDED": "purple",
        }
        color = colors.get(obj.status, "black")
        return format_html(f'<strong style="color:{color};">{obj.get_status_display()}</strong>')
    colored_status.short_description = "Status"

