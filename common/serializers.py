from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

User = get_user_model()


class GenericModelSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    created_by = serializers.SerializerMethodField()
    updated_by = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()
    updated_at = serializers.SerializerMethodField()
    _created_by = serializers.SerializerMethodField()
    _updated_by = serializers.SerializerMethodField()
    can_delete = serializers.ReadOnlyField()

    class Meta:
        model = None
        fields = (
            "id",
            "_created_by",
            "created_by",
            "_updated_by",
            "updated_by",
            "created_at",
            "updated_at",
            "can_delete",
        )
        read_only_fields = fields

    def get_created_by(self, obj):
        user = getattr(obj, "_created_by", None)
        if not user or hasattr(user, "all"):
            return None
        return f"{user.first_name} {user.last_name}".strip() or user.mobile

    def get_updated_by(self, obj):
        user = getattr(obj, "_updated_by", None)
        if not user or hasattr(user, "all"):
            return None
        return f"{user.first_name} {user.last_name}".strip() or user.mobile

    def get__created_by(self, obj):
        user = getattr(obj, "_created_by", None)
        if not user or hasattr(user, "all"):
            return None
        return str(user.id)

    def get__updated_by(self, obj):
        user = getattr(obj, "_updated_by", None)
        if not user or hasattr(user, "all"):
            return None
        return str(user.id)

    def get_created_at(self, obj):
        return getattr(obj, "created_at", None)

    def get_updated_at(self, obj):
        return getattr(obj, "updated_at", None)

    @extend_schema_field(serializers.BooleanField)
    def get_can_delete(self, obj):
        return getattr(obj, "can_delete", False)
