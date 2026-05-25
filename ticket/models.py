import datetime
from django.db import models
from django.utils.translation import gettext_lazy as _

from booking.models import Booking, Show
from common.models import GenericModel
from seat.models import Seat
    
    
class Category(GenericModel):
    show = models.ForeignKey(
        Show,
        on_delete=models.CASCADE,
        related_name="user_appointment",
        null=True,
        blank=True
    )
    title = models.CharField(max_length=400,null=True,blank=True)
    stock = models.PositiveIntegerField(default=0)
    _price = models.CharField(max_length=400, null=True, blank=True, db_column='price')

    class Meta:
        verbose_name = "category"
        verbose_name_plural = "categories"
        db_table = "category"

    @property
    def price(self):
        """
        Public property to access price. 
        You can add logic here to convert it (e.g., to float or decimal) 
        or format it.
        """
        return self._price

    @price.setter
    def price(self, value):
        """Allows setting the price via Category.price = '100'"""
        self._price = str(value)
        
    def __str__(self):
        return self.title or "none"


class Ticket(GenericModel):
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="ticket_category",
        null=True,
        blank=True
    )
    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name="ticket_booking",
        null=True,
        blank=True
    )
    seat = models.ForeignKey(
        Seat,
        on_delete=models.CASCADE,
        related_name="ticket_seat",
        null=True,
        blank=True
    )
    code = models.CharField(max_length=200, unique=True, blank=True)

    class Meta:
        verbose_name = "ticket"
        verbose_name_plural = "tickets"
        db_table = "ticket"

    def __str__(self):
        return self.code or "none"

    """
    year-created_at(date)-no_seat
    """
    def save(self, *args, **kwargs):
        if not self.code:
            year = str(datetime.date.today().year)[-2:]
            date_part = self.booking._created_at.strftime("%m-%d")
            self.code = f"{year}-{date_part}-{self.no_seat}"
        super().save(*args, **kwargs)