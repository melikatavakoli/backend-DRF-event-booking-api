import logging
from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

logger = logging.getLogger(__name__)


def _extract_messages(error_data):
    if isinstance(error_data, (str, Exception)):
        return [str(error_data)]

    if isinstance(error_data, dict):
        messages = []
        for field, value in error_data.items():
            if field in ("non_field_errors", "__all__"):
                messages.extend(_extract_messages(value))
            else:
                for msg in _extract_messages(value):
                    messages.append(f"{field}: {msg}")
        return messages

    if isinstance(error_data, (list, tuple)):
        messages = []
        for item in error_data:
            messages.extend(_extract_messages(item))
        return messages
    return [str(error_data)]


def _format_response(error_messages, status_code):
    return {
        "success": False,
        "error": error_messages[0] if error_messages else "An error occurred",
        "status_code": status_code,
        "messages": [{"message": msg} for msg in error_messages],
    }


def exception_handler(exc, context):
    response = drf_exception_handler(exc, context)
    if not response or response.status_code >= 500:
        request = context.get("request")
        logger.exception(
            f"Server error: {exc}",
            extra={
                "path": getattr(request, "path", None),
                "method": getattr(request, "method", None),
            },
        )
        if settings.DEBUG:
            raise
    if response and response.status_code < 500:
        messages = _extract_messages(response.data)
        return Response(
            _format_response(messages, response.status_code),
            status=response.status_code,
        )
    return Response(
        _format_response(
            ["Internal server error"], status.HTTP_500_INTERNAL_SERVER_ERROR
        ),
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
