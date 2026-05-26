from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import Invoice, Item


class ItemInlineAdmin(admin.TabularInline):
    model = Item
    extra = 1
    readonly_fields = ['total_price', 'final_price']


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = [
        'invoice_number', 'tracking_code', 'user', 
        'order', 'final_amount', 'status', 'issue_date'
    ]
    list_filter = ['status', 'issue_date', 'created_at']
    search_fields = ['invoice_number', 'tracking_code', 'user__username', 'order__id']
    readonly_fields = ['invoice_number', 'tracking_code', 'created_at', 'updated_at']
    inlines = [ItemInlineAdmin]
    ordering = ['-created_at']
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
    
    actions = ['mark_as_paid', 'mark_as_unpaid']
    
    @admin.action(description='Mark selected invoices as paid')
    def mark_as_paid(self, request, queryset):
        updated = queryset.update(status='paid')
        self.message_user(request, f'{updated} invoice(s) marked as paid.')
    
    @admin.action(description='Mark selected invoices as unpaid')
    def mark_as_unpaid(self, request, queryset):
        updated = queryset.update(status='unpaid')
        self.message_user(request, f'{updated} invoice(s) marked as unpaid.')


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'invoice', 'product_code', 'quantity', 'unit_price']
    list_filter = ['created_at']
    search_fields = ['product_code', 'description', 'invoice__invoice_number']
    readonly_fields = ['created_at', 'updated_at']