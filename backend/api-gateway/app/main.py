from contextlib import asynccontextmanager
import logging
import uuid

import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from prometheus_fastapi_instrumentator import Instrumentator

from app.core.config import get_settings
from app.core.correlation import CORRELATION_HEADER, get_or_create_correlation_id
from app.dashboard import aggregate_dashboard

settings = get_settings()

class _DefaultCorrelationId(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "correlation_id"):
            record.correlation_id = "-"
        return True


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s correlation_id=%(correlation_id)s %(message)s",
)
logging.getLogger().addFilter(_DefaultCorrelationId())


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.http_client = httpx.AsyncClient(
        timeout=httpx.Timeout(settings.request_timeout_seconds)
    )
    yield
    await app.state.http_client.aclose()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Public API gateway for the Museum Collection Lifecycle Platform.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def correlation_middleware(request: Request, call_next):
    correlation_id = get_or_create_correlation_id(request)
    request.state.correlation_id = correlation_id

    logger = logging.LoggerAdapter(
        logging.getLogger("gateway.request"),
        {"correlation_id": correlation_id},
    )

    logger.info("%s %s", request.method, request.url.path)

    response = await call_next(request)

    response.headers[CORRELATION_HEADER] = correlation_id
    return response


Instrumentator().instrument(app).expose(
    app,
    endpoint="/metrics",
    include_in_schema=False,
)


@app.get("/health", tags=["system"])
async def health():
    return {
        "status": "healthy",
        "service": "api-gateway",
    }


@app.get("/ready", tags=["system"])
async def readiness():
    return {
        "status": "ready",
        "service": "api-gateway",
    }


def _forward_headers(
    request: Request,
    correlation_id: str,
) -> dict[str, str]:
    headers = {
        key: value
        for key, value in request.headers.items()
        if key.lower() not in {
            "host",
            "content-length",
            "connection",
        }
    }

    headers[CORRELATION_HEADER] = correlation_id
    return headers

def _response_headers(
    headers: httpx.Headers,
) -> dict[str, str]:
    excluded = {
        "content-length",
        "transfer-encoding",
        "connection",
        "content-encoding",
    }

    result: dict[str, str] = {}

    for key, value in headers.items():
        if key.lower() in excluded:
            continue

        result[key] = value

    return result


async def proxy_request(
    request: Request,
    service_url: str,
    service_path: str,
) -> Response:
    correlation_id = request.state.correlation_id
    upstream_url = f"{service_url.rstrip('/')}{service_path}"

    try:
        body = await request.body()

        upstream = await request.app.state.http_client.request(
            method=request.method,
            url=upstream_url,
            headers=_forward_headers(request, correlation_id),
            content=body,
            params=request.query_params,
        )

    except httpx.RequestError:
        return JSONResponse(
            status_code=502,
            content={
                "error": {
                    "code": "UPSTREAM_UNAVAILABLE",
                    "message": "Requested application service is unavailable.",
                    "correlation_id": correlation_id,
                }
            },
        )

    response_headers = _response_headers(upstream.headers)
    response_headers[CORRELATION_HEADER] = correlation_id

    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        headers=response_headers,
        media_type=upstream.headers.get("content-type"),
    )

@app.api_route(
    "/api/v1/loans",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
)
async def loan_root_proxy(request: Request):
    return await proxy_request(
        request,
        settings.loan_service_url,
        "/api/v1/loans",
    )


@app.api_route(
    "/api/v1/notifications",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
)
async def notification_root_proxy(request: Request):
    return await proxy_request(
        request,
        settings.notification_service_url,
        "/api/v1/notifications",
    )


@app.api_route(
    "/api/v1/audit",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
)
async def audit_root_proxy(request: Request):
    return await proxy_request(
        request,
        settings.audit_service_url,
        "/api/v1/audit",
    )

@app.api_route(
    "/api/v1/auth/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
)
async def auth_proxy(request: Request, path: str):
    return await proxy_request(
        request,
        settings.auth_service_url,
        f"/api/v1/auth/{path}",
    )


@app.api_route(
    "/api/v1/collection/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
)
async def collection_proxy(request: Request, path: str):
    return await proxy_request(
        request,
        settings.collection_service_url,
        f"/api/v1/collection/{path}",
    )


@app.api_route(
    "/api/v1/conservation/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
)
async def conservation_proxy(request: Request, path: str):
    return await proxy_request(
        request,
        settings.conservation_service_url,
        f"/api/v1/conservation/{path}",
    )


@app.api_route(
    "/api/v1/loans/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
)
async def loan_proxy(request: Request, path: str):
    return await proxy_request(
        request,
        settings.loan_service_url,
        f"/api/v1/loans/{path}",
    )


@app.api_route(
    "/api/v1/notifications/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
)
async def notification_proxy(request: Request, path: str):
    return await proxy_request(
        request,
        settings.notification_service_url,
        f"/api/v1/notifications/{path}",
    )


@app.api_route(
    "/api/v1/audit/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
)
async def audit_proxy(request: Request, path: str):
    return await proxy_request(
        request,
        settings.audit_service_url,
        f"/api/v1/audit/{path}",
    )


@app.exception_handler(Exception)
async def unhandled_exception(request: Request, exc: Exception):
    correlation_id = getattr(
        request.state,
        "correlation_id",
        str(uuid.uuid4()),
    )

    logging.getLogger("gateway.error").exception(
        "Unhandled gateway exception"
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected gateway error occurred.",
                "correlation_id": correlation_id,
            }
        },
        headers={CORRELATION_HEADER: correlation_id},
    )

@app.get("/api/v1/dashboard/summary", tags=["dashboard"])
async def dashboard_summary(request: Request):
    result = await aggregate_dashboard(
        request.app.state.http_client,
        {
            "collection": settings.collection_service_url,
            "conservation": settings.conservation_service_url,
            "loan": settings.loan_service_url,
        },
        request.headers.get("Authorization"),
    )
    # Uncomment to fail closed when collection (mandatory) is down:
    # if result["collection"]["status"] != "ok":
    #     return JSONResponse(status_code=503, content=result)
    return result
