from datetime import timedelta, timezone
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.db.models import Max
from django.db import models, transaction

from address.models import City, State
from booking.types import Status
from common.models import GenericModel
from core.models import CoreUser

User = get_user_model()


class Show(GenericModel):
    city = models.ForeignKey(
        City,
        on_delete=models.CASCADE,
        related_name="event_city",
        null=True,
        blank=True
    )
    state = models.ForeignKey(
        State,
        on_delete=models.CASCADE,
        related_name="event_state",
        null=True,
        blank=True
    )
    address = models.CharField(max_length=400,null=True,blank=True)
    title = models.CharField(max_length=400,null=True,blank=True)
    description = models.CharField(max_length=1000,null=True,blank=True)

    class Meta:
        verbose_name = "show"
        verbose_name_plural = "show"
        db_table = 'show'

    def __str__(self):
        return self.title or "none"


class Booking(GenericModel):
    user = models.ForeignKey(
        CoreUser,
        on_delete=models.CASCADE,
        related_name="user_booking",
        null=True,
        blank=True
    )
    show = models.ForeignKey(
        Show,
        on_delete=models.CASCADE,
        related_name="booking_show",
        null=True,
        blank=True
    )
    title = models.CharField(max_length=400,null=True,blank=True)
    status = models.CharField(max_length=24,default="pending",choices=Status,null=True,blank=True)
    date = models.DateField(null=True,blank=True)
    time = models.TimeField(null=True,blank=True,)
    is_pass = models.BooleanField(null=True,blank=True)
    is_reserved = models.BooleanField(null=True,blank=True)
    total_price  = models.CharField(max_length=400,null=True,blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_paid = models.BooleanField(default=False)
    payment_time = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "booking"
        verbose_name_plural = "booking"
        db_table = 'booking'

    def calculate_total_price(self):
        """
        Calculates the total by summing Category prices.
        Assumes Ticket has a 'category' FK and a 'booking' FK.
        """
        total = Decimal('0.00')
        for ticket in self.booking_tickets.all():
            if ticket.category and ticket.category.price:
                total += Decimal(str(ticket.category.price))
        return str(total)
        
    def __str__(self):
        return f"{self.user} - {self.title}"
    
    def save(self, *args, **kwargs):
        if not self.title:
            with transaction.atomic():
                last_title = Booking.objects.select_for_update().aggregate(max_title=Max("title"))["max_title"]
                self.title = str(int(last_title) + 1) if (last_title and last_title.isdigit()) else "1000"
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=10)
        super().save(*args, **kwargs)