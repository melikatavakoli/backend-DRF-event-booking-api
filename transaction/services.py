def issue_tickets(self):
    """صدور بلیط‌ها بعد از پرداخت موفق"""
    
    from concert.models import Ticket
    if not self.booking:
        return
    for seat in self.booking.seats.all():
        ticket = Ticket.objects.create(
            booking=self.booking,
            category=seat.category,
            no_seat=seat.number,
        )
    self.booking.tickets_issued = True
    self.booking.save()
    self.send_payment_notification()