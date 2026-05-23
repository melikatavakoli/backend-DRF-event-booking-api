import logging
import threading

logger = logging.getLogger(__name__)
_local = threading.local()


class ExceptionLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            return self.get_response(request)
        except Exception:
            logger.exception(
                "Unhandled exception",
                extra={
                    "request_method": request.method,
                    "request_url": request.get_full_path(),
                    "remote_addr": request.META.get("REMOTE_ADDR"),
                    "user_agent": request.META.get("HTTP_USER_AGENT", ""),
                },
            )
            raise


def get_current_user():
    return getattr(_local, "user", None)


class CurrentUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _local.user = request.user
        return self.get_response(request)
