from django_filters.rest_framework import DjangoFilterBackend
from common.paginations import CustomLimitOffsetPagination
from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from rest_framework.filters import OrderingFilter, SearchFilter

from seat.models import Prefix, Seat, Suffix
from seat.serializers import PrefixSerializer, SeatSerializer, SuffixSerializer


class PrefixViewSet(viewsets.ModelViewSet):
    queryset = Prefix.objects.all()
    serializer_class = PrefixSerializer
    pagination_class = CustomLimitOffsetPagination
    filter_backends = (DjangoFilterBackend, OrderingFilter, SearchFilter)


class SuffixViewSet(viewsets.ModelViewSet):
    queryset = Suffix.objects.all()
    serializer_class = SuffixSerializer
    pagination_class = CustomLimitOffsetPagination
    filter_backends = (DjangoFilterBackend, OrderingFilter, SearchFilter)


class SeatViewSet(viewsets.ModelViewSet):
    queryset = Seat.objects.all()
    serializer_class = SeatSerializer
    pagination_class = CustomLimitOffsetPagination
    filter_backends = (DjangoFilterBackend, OrderingFilter, SearchFilter)
