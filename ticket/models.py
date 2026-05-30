import datetime
from django.db import models
from booking.models import Booking
from common.models import GenericModel
from seat.models import Seat

class Ticket(GenericModel):
    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name="tickets",
        null=True,
        blank=True,
    )
    seat = models.ForeignKey(
        Seat,
        on_delete=models.CASCADE,
        related_name="tickets",
        null=True,
        blank=True,
    )
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    code = models.CharField(max_length=200, unique=True, blank=True)

    class Meta:
        verbose_name = "ticket"
        verbose_name_plural = "tickets"
        db_table = "ticket"

    def __str__(self):
        return self.code or f"Ticket {self.id}"

    def save(self, *args, **kwargs):
        if not self.code:
            year = str(datetime.date.today().year)[-2:]
            date_part = datetime.date.today().strftime("%m%d")
            seat_number = self.seat.seat_number if self.seat else "000"
            self.code = f"CON-{year}{date_part}-{seat_number}-{self.id}"
        super().save(*args, **kwargs)