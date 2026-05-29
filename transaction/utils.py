import random
from persiantools.jdatetime import JalaliDate




def generate_random_transaction_no():
    today = JalaliDate.today()
    year = today.year % 100
    prefix = f"T{year}{today.month}{today.day}"

    while True:
        transaction_no = prefix + str(random.randrange(1000, 9999, 1))

        from transaction.models import Transaction
        if Transaction.objects.all().exists():
            if Transaction.objects.filter(transaction_no=transaction_no).exists():
                continue
        break
    return transaction_no
