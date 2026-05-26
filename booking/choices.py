from django.db import models


class Status(models.TextChoices):
    cancelled = "cancelled", "لغو شده"
    moved = "moved", "جابجا شده"
    done = "done", "انجام شده"
    pending = "pending", "در انتظار"
    persent = "persent", "حاضر"
    in_clinic = "in_clinic", "در کلینیک"
    not_present = "not_present", "عدم حضور"
    in_progress = "in_progress", "در حال انجام"
