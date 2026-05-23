import os
from datetime import datetime
from django.utils import timezone


def common_User_str(User):
    if not User:
        return ""
    return User.full_name or User.mobile


def _localize_datetime(dt):
    if not dt:
        return None

    if not timezone.is_aware(dt):
        dt = timezone.make_aware(dt, timezone.get_current_timezone())
    return timezone.localtime(dt)


def _format_datetime(dt, format_str):
    dt = _localize_datetime(dt)
    return dt.strftime(format_str) if dt else ""


def common_datetime_str(dt):
    return _format_datetime(dt, "%Y.%m.%d %H:%M")


def common_date_str(dt):
    return _format_datetime(dt, "%Y.%m.%d")


def file_name_datetime_str():
    now = timezone.now()
    return now.strftime("%Y-%m-%d-%H-%M-%S")


def upload_to_by_date(instance, filename):
    today = datetime.now()
    timestamp = today.strftime("%Y%m%d%H%M%S")
    file_extension = os.path.splitext(filename)[1]
    new_filename = f"{timestamp}{file_extension}"
    return os.path.join(f"storage/{today.year}/", new_filename)


def calculate_age(birth_date):
    if not birth_date:
        return None
    today = timezone.localdate()
    return (
        today.year
        - birth_date.year
        - int((today.month, today.day) < (birth_date.month, birth_date.day))
    )
