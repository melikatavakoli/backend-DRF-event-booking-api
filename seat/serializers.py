from rest_framework import serializers
from django.contrib.auth import get_user_model

from common.serializers import GenericModelSerializer
from seat.models import Prefix, Seat, Suffix

User = get_user_model()


class PrefixSerializer(GenericModelSerializer):
    class Meta:
        model = Prefix
        fields = GenericModelSerializer.Meta.fields + (
            "id",
            "title",
        )
        
    
class SuffixSerializer(GenericModelSerializer):
    class Meta:
        model = Suffix
        fields = GenericModelSerializer.Meta.fields + (
            "id",
            "title",
        )
        
        
class SeatSerializer(GenericModelSerializer):
    class Meta:
        model = Seat
        fields = GenericModelSerializer.Meta.fields + (
            "id",
            "suffix",
            "prefix",
        )