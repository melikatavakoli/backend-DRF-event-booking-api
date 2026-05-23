from auditlog.mixins import AuditlogHistoryAdminMixin
from django.contrib import admin, messages
from django.db import transaction
from django.db.models.deletion import ProtectedError
from import_export.admin import ImportExportModelAdmin


class SoftDeleteListFilter(admin.SimpleListFilter):
    title = "Soft Delete Status"
    parameter_name = "_is_deleted"

    def lookups(self, request, model_admin):
        return [("0", "Active"), ("1", "Deleted")]

    def queryset(self, request, queryset):
        if self.value() == "0":
            return queryset.filter(_is_deleted=False)
        if self.value() == "1":
            return queryset.model.deleted_objects.all()
        return queryset


class BaseAdmin(AuditlogHistoryAdminMixin, ImportExportModelAdmin):
    show_auditlog_history_link = True
    actions = ["hard_delete_selected", "restore_selected"]
    list_filter = (SoftDeleteListFilter,)

    def get_queryset(self, request):
        return self.model.all_objects.all()

    @admin.action(description="Hard delete selected (permanent)")
    def hard_delete_selected(self, request, queryset):
        count = queryset.count()
        try:
            with transaction.atomic():
                queryset.hard_delete()
            self.message_user(
                request, f"{count} record(s) permanently deleted.", messages.SUCCESS
            )
        except ProtectedError:
            self.message_user(
                request,
                "Cannot hard delete because related protected objects exist.",
                messages.ERROR,
            )
        except Exception as e:
            self.message_user(request, str(e), messages.ERROR)

    @admin.action(description="Restore selected (undo soft delete)")
    def restore_selected(self, request, queryset):
        restored = sum(
            1
            for obj in queryset
            if getattr(obj, "_is_deleted", False) and obj.restore()
        )
        self.message_user(request, f"{restored} record(s) restored.", messages.SUCCESS)

    def get_actions(self, request):
        actions = super().get_actions(request)
        if not request.user.is_superuser:
            actions.pop("hard_delete_selected", None)
        if request.GET.get("_is_deleted") != "1":
            actions.pop("restore_selected", None)
            actions.pop("hard_delete_selected", None)
        return actions
