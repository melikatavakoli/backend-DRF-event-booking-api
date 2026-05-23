import os
from datetime import datetime
import uuid


BASE_PATH = "uploads"


def upload_to_by_date(instance, filename):
    today = datetime.now()
    timestamp = today.strftime("%Y%m%d%H%M%S")
    file_extension = os.path.splitext(filename)[1]
    new_filename = f"{timestamp}{file_extension}"
    return os.path.join(f"{BASE_PATH}/{today.year}/", new_filename)


def upload_to_by_uuid(instance, filename):
    today = datetime.now()
    ext = os.path.splitext(filename)[1]
    new_filename = f"{uuid.uuid4()}{ext}"
    return os.path.join(f"{BASE_PATH}/{today.year}/", new_filename)
