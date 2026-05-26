from rest_framework import serializers
from django.contrib.auth import get_user_model

from address.models import City, State
from booking.models import Booking, Show
from common.serializers import GenericModelSerializer

User = get_user_model()


class ShowSerializer(GenericModelSerializer):
    city = serializers.PrimaryKeyRelatedField(
        queryset=City.objects.all(),
        required=False,
    )
    state = serializers.PrimaryKeyRelatedField(
        queryset=State.objects.all(),
        required=False,
    )

    class Meta:
        model = Show
        fields = GenericModelSerializer.Meta.fields + (
            "id",
            "city",
            "state",
            "address",
            "title",
            "description",
        )


class BookingSerializer(GenericModelSerializer):
    show = serializers.PrimaryKeyRelatedField(
        queryset=Show.objects.all(),
        required=False,
    )

    class Meta:
        model = Booking
        fields = GenericModelSerializer.Meta.fields + (
            "id",
            "user",
            "status",
            "date",
            "title",
            "time",
            "is_pass",
            "is_reserved",
        )
        read_only_fields = ["total_price"]
