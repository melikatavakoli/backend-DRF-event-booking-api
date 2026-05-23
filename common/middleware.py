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
                    "User_agent": request.META.get("HTTP_User_AGENT", ""),
                },
            )
            raise


def get_current_User():
    return getattr(_local, "User", None)


class CurrentUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _local.User = request.User
        return self.get_response(request)
