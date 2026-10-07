from rest_framework.exceptions import ValidationError
from rest_framework.views import exception_handler


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return None
    fields = response.data if isinstance(exc, ValidationError) else {}
    detail = response.data.get("detail") if isinstance(response.data, dict) else None
    response.data = {
        "error": {
            "code": getattr(exc, "default_code", "request_error"),
            "message": str(detail) if detail else "Please check the submitted fields.",
            "fields": fields,
        }
    }
    return response
