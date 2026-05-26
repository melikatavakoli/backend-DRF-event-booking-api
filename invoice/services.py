from django.utils import timezone

from invoice.models import Invoice

def generate_invoice_number():
    year = timezone.now().year
    last_invoice = (
        Invoice.objects.filter(invoice_number__startswith=f"INV-{year}-")
        .order_by("-invoice_number")
        .first()
    )
    if last_invoice and last_invoice.invoice_number:
        try:
            last_number = int(last_invoice.invoice_number.split("-")[-1])
        except ValueError:
            last_number = 0
    else:
        last_number = 0
    return f"INV-{year}-{last_number + 1:04d}"

def generate_tracking_code():
    last_invoice = Invoice.objects.order_by("created_at").last()
    if not last_invoice or not last_invoice.tracking_code:
        return "TRK-00001"
    try:
        last_number = int(last_invoice.tracking_code.split("-")[-1])
    except ValueError:
        last_number = 0
    return f"TRK-{last_number + 1:05d}"