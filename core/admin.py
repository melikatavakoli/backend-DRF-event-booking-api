from import_export import resources
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_User_model
from common.admin import BaseAdmin, SoftDeleteListFilter
from core.models import BaseUser
from django.contrib import admin

User = get_User_model()


class UserResource(resources.ModelResource):

    class Meta:
        model = User
        fields = (
            "id",
            "mobile",
            "first_name",
            "last_name",
            "email",
            "role",
            "is_verified",
            "is_staff",
            "status",
        )
        import_id_fields = ["mobile"]


@admin.register(BaseUser)
class BaseUserAdmin(BaseAdmin, BaseUserAdmin):

    model = BaseUser
    resource_class = UserResource

    list_display = (
        "full_name",
        "mobile",
        "role",
        "is_verified",
        "is_staff",
        "status",
        "_is_deleted",
    )

    list_editable = (
        "role",
        "status",
    )

    search_fields = (
        "mobile",
        "first_name",
        "last_name",
        "email",
    )

    list_filter = (
        SoftDeleteListFilter,
        "role",
        "status",
        "is_verified",
        "is_staff",
    )

    readonly_fields = (
        "id",
        "_deleted_at",
        "last_login",
        "password_updated_at",
        "full_name",
        "age",
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
                    "is_verified",
                    "is_email_verified",
                    "is_staff",
                    "is_superUser",
                    "groups",
                    "User_permissions",
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
            {"fields": ()},
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
                    "is_verified",
                    "is_staff",
                ),
            },
        ),
    )

    actions_row = [
        "reset_password_action",
    ]

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            obj.delete()

    def delete_model(self, request, obj):
        obj.delete()
