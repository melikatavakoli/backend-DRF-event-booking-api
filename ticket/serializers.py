from rest_framework import serializers
from django.contrib.auth import get_user_model

from seat.models import Seat
from ticket.models import Category, Ticket
from common.serializers import GenericModelSerializer
from booking.models import Booking, Show

User = get_user_model()


class CategorySerializer(GenericModelSerializer):
    price = serializers.CharField(read_only=True)
    show = serializers.PrimaryKeyRelatedField(
        queryset=Show.objects.all(),
        allow_null=True,
        required=False,
    )

    def update(self, instance, validated_data):
        if "price" in validated_data:
            instance.price = validated_data.pop("price")
        return super().update(instance, validated_data)

    class Meta:
        model = Category
        fields = GenericModelSerializer.Meta.fields + (
            "id",
            "show",
            "title",
            "stock",
            "price",
        )


class TicketSerializer(GenericModelSerializer):
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        allow_null=True,
        required=False,
    )
    booking = serializers.PrimaryKeyRelatedField(
        queryset=Booking.objects.all(),
        allow_null=True,
        required=False,
    )
    seat = serializers.PrimaryKeyRelatedField(
        queryset=Seat.objects.all(),
        allow_null=True,
        required=False,
    )

    class Meta:
        model = Ticket
        fields = GenericModelSerializer.Meta.fields + (
            "id",
            "category",
            "booking",
            "seat",
            "code",
        )
