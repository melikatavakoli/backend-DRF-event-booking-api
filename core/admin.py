from import_export import resources
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib import admin
from .models import CoreUser
from common.admin import BaseAdmin, SoftDeleteListFilter


class CoreUserResource(resources.ModelResource):

    class Meta:
        model = CoreUser
        fields = (
            "id",
            "mobile",
            "first_name",
            "last_name",
            "email",
            "role",
            "is_staff",
            "is_active",
            "status",
            "country",
            "state",
            "city",
        )
        import_id_fields = ["mobile"]

from django.contrib.admin.actions import delete_selected

@admin.register(CoreUser)
class CoreUserAdmin(BaseAdmin, BaseUserAdmin):

    model = CoreUser
    resource_class = CoreUserResource

    # Remove username field since we're using mobile as USERNAME_FIELD
    username_field = "mobile"
    
    list_display = (
        "full_name",
        "mobile",
        "email",
        "role",
        "is_active",
        "is_staff",
        "status",
        "_is_deleted",
    )


    list_editable = (
        "role",
        "status",
        "is_active",
    )

    search_fields = (
        "mobile",
        "first_name",
        "last_name",
        "email",
        "id",
    )

    list_filter = (
        SoftDeleteListFilter,
        "role",
        "status",
        "is_active",
        "is_staff",
        "country",
    )

    readonly_fields = (
        "id",
        "_deleted_at",
        "last_login",
        "password_updated_at",
        "full_name",
        "age",
        "created_at_display",
    )

    ordering = ("-id",)

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "id",
                    "mobile",
                    "password",
                )
            },
        ),
        (
            "Personal Info",
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "full_name",
                    "email",
                    "birth_date",
                    "age",
                    "role",
                    "description",
                )
            },
        ),
        (
            "Location",
            {
                "fields": (
                    "country",
                    "state",
                    "city",
                )
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                    "status",
                )
            },
        ),
        (
            "Security",
            {
                "fields": (
                    "last_login",
                    "last_login_ip",
                    "password_updated_at",
                )
            },
        ),
        (
            "Soft Delete",
            {
                "fields": (
                    "_is_deleted",
                    "_deleted_at",
                )
            },
        ),
        (
            "Audit",
            {
                "fields": (
                    "created_at_display",
                )
            },
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "mobile",
                    "password1",
                    "password2",
                    "first_name",
                    "last_name",
                    "email",
                    "role",
                    "is_active",
                    "is_staff",
                ),
            },
        ),
    )

    # If you have actions_row from BaseAdmin, keep it
    # actions_row = [
    #     "reset_password_action",
    # ]

    def delete_queryset(self, request, queryset):
        """Soft delete for bulk actions"""
        for obj in queryset:
            obj.delete()

    def delete_model(self, request, obj):
        """Soft delete for single object deletion"""
        obj.delete()

    def get_queryset(self, request):
        """Use all_objects to include soft-deleted items in admin"""
        return self.model.all_objects.all()

    actions = ["soft_delete_selected", "restore_selected"]

    def get_actions(self, request):
        actions = super().get_actions(request)

        if "delete_selected" in actions:
            del actions["delete_selected"]

        return actions


    @admin.action(description="Soft delete selected users")
    def soft_delete_selected(self, request, queryset):

        for obj in queryset:
            obj.delete()

        self.message_user(
            request,
            f"{queryset.count()} users soft deleted successfully."
        )