import random
from persiantools.jdatetime import JalaliDate
from order.models import Order


def generate_random_transaction_no():
    today = JalaliDate.today()
    year = today.year % 100
    prefix = f"T{year}{today.month}{today.day}"

    while True:
        order_no = prefix + str(random.randrange(1000, 9999, 1))

        if Order.objects.all().exists():
            if Order.objects.filter(order_no=order_no).exists():
                continue
        break
    return order_no
