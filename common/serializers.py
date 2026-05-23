from django.contrib.auth import get_User_model
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

User = get_User_model()


class GenericSerializer(serializers.ModelSerializer):
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
        User = getattr(obj, "_created_by", None)
        if not User or hasattr(User, "all"):
            return None
        return f"{User.first_name} {User.last_name}".strip() or User.mobile

    def get_updated_by(self, obj):
        User = getattr(obj, "_updated_by", None)
        if not User or hasattr(User, "all"):
            return None
        return f"{User.first_name} {User.last_name}".strip() or User.mobile

    def get__created_by(self, obj):
        User = getattr(obj, "_created_by", None)
        if not User or hasattr(User, "all"):
            return None
        return str(User.id)

    def get__updated_by(self, obj):
        User = getattr(obj, "_updated_by", None)
        if not User or hasattr(User, "all"):
            return None
        return str(User.id)

    def get_created_at(self, obj):
        return getattr(obj, "created_at", None)

    def get_updated_at(self, obj):
        return getattr(obj, "updated_at", None)

    @extend_schema_field(serializers.BooleanField)
    def get_can_delete(self, obj):
        return getattr(obj, "can_delete", False)
