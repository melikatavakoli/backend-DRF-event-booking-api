from django_filters import rest_framework as filters
from django_filters.rest_framework import OrderingFilter

from booking.models import Appointment

class AppointmentCalendarFilter(filters.FilterSet):

    class Meta:
        model = Appointment
        fields = [
            'doctor'
        ]

    ordering = OrderingFilter(
        fields=(
            ('appointment_date', 'appointment_date'),
            ('patient__user__full_name', 'patient_name'),
            ('_created_at', 'created_at'),
        ),
    )



class NumberInFilter(filters.BaseInFilter, filters.NumberFilter):
    pass


class DateFilter(filters.FilterSet):
    date = filters.DateFilter(field_name="appointment_date")
    start_date_from = filters.DateFilter(
        field_name="appointment_date",
        lookup_expr="gte"
    )
    end_date_to = filters.DateFilter(
        field_name="appointment_date",
        lookup_expr="lte"
    )
    category_title = filters.CharFilter(field_name="category__title",lookup_expr="icontains")
    
    class Meta:
        model = Appointment
        fields = [
            "date", 
            'patient',
            'status',
            'doctor', 
            'type',
            'start_date_from', 
            'end_date_to',
            'section',
            "category_title",
        ]
