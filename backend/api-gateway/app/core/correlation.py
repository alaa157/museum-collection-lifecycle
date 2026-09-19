import re
from uuid import UUID, uuid4

from fastapi import Request

CORRELATION_HEADER = "X-Correlation-ID"

# UUID string or conservative token (alnum, dash, underscore), max 64
_SAFE_CORRELATION = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


def get_or_create_correlation_id(request: Request) -> str:
    value = request.headers.get(CORRELATION_HEADER)
    if not value:
        return str(uuid4())

    value = value.strip()
    try:
        return str(UUID(value))
    except (ValueError, TypeError, AttributeError):
        pass

    if _SAFE_CORRELATION.fullmatch(value):
        return value

    return str(uuid4())