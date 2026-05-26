from django_filters.rest_framework import DjangoFilterBackend
from common.paginations import CustomLimitOffsetPagination
from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from rest_framework.filters import OrderingFilter, SearchFilter

from ticket.models import Category, Ticket
from ticket.serializers import CategorySerializer, TicketSerializer
from core.permissions import IsAdminRole, IsStaffOrAdminRole


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    pagination_class = CustomLimitOffsetPagination
    filter_backends = (DjangoFilterBackend, OrderingFilter, SearchFilter)

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAdminRole()]
        return [AllowAny()]


class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
    pagination_class = CustomLimitOffsetPagination
    filter_backends = (DjangoFilterBackend, OrderingFilter, SearchFilter)

    def get_permissions(self):
        if self.action in ["update", "partial_update", "destroy"]:
            return [IsStaffOrAdminRole()]
        return [AllowAny()]
