from core.models import LoginAttempt
from core.types import StatusType


def _get_ip(request) -> str | None:
    if not request:
        return None
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    return (
        x_forwarded_for.split(",")[0]
        if x_forwarded_for
        else request.META.get("REMOTE_ADDR")
    )


def record_login_attempt(request, user=None, status=StatusType.FAILED):
    LoginAttempt.objects.create(
        user=user,
        status=status,
        ip_address=_get_ip(request),
    )
