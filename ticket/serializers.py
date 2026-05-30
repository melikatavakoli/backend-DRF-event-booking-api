from rest_framework import serializers
from django.contrib.auth import get_user_model

from seat.models import Seat
from ticket.models import Ticket
from common.serializers import GenericModelSerializer
from booking.models import Booking

User = get_user_model()


class TicketSerializer(GenericModelSerializer):
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
            "booking",
            "seat",
            "code",
        )
