from django.db import transaction
from rest_framework.exceptions import ValidationError
from .models import Ticket, Category


def create_booking_tickets(booking, category_id, quantity):
    """
    Call this inside your DRF view.
    'booking' is the instance already saved to the DB.
    """
    try:
        with transaction.atomic():
            category = Category.objects.select_for_update().get(id=category_id)
            
            if category.stock < quantity:
                raise ValidationError("Not enough stock available for this category.")
            
            for i in range(quantity):
                seat_number = category.stock  
                
                Ticket.objects.create(
                    booking=booking,
                    category=category,
                    no_seat=seat_number
                )
                category.stock -= 1
            
            category.save()
            booking.total_price = booking.calculate_total_price()
            booking.save()
            
    except Category.DoesNotExist:
        raise ValidationError("Selected category does not exist.")