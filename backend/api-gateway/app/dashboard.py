import asyncio


async def fetch_json(client, url, headers):
    try:
        response = await client.get(url, headers=headers)
    except Exception as exc:
        return {
            "status": "unavailable",
            "data": None,
            "error": str(exc) or "upstream request failed",
        }

    if response.status_code >= 400:
        detail = None
        try:
            body = response.json()
            detail = body.get("detail") or body.get("error") or body
        except Exception:
            detail = response.text[:500] if response.text else None

        return {
            "status": "error",
            "data": None,
            "error": detail or f"HTTP {response.status_code}",
            "http_status": response.status_code,
        }

    try:
        return {
            "status": "ok",
            "data": response.json(),
            "error": None,
        }
    except Exception as exc:
        return {
            "status": "error",
            "data": None,
            "error": f"invalid JSON from upstream: {exc}",
        }

async def aggregate_dashboard(
    client,
    services: dict[str, str],
    authorization: str | None,
):
    headers = {}
    if authorization:
        headers["Authorization"] = authorization

    collection_r, conservation_r, loans_r = await asyncio.gather(
        fetch_json(
            client,
            f"{services['collection']}/api/v1/collection/dashboard/summary",
            headers,
        ),
        fetch_json(
            client,
            f"{services['conservation']}/api/v1/conservation/dashboard/summary",
            headers,
        ),
        fetch_json(
            client,
            f"{services['loan']}/api/v1/loans/dashboard/summary",
            headers,
        ),
    )

    collection_data = collection_r.get("data") or {}
    conservation_data = conservation_r.get("data") or {}
    loans_data = loans_r.get("data") or {}

    sources = {
        "collection": collection_r,
        "conservation": conservation_r,
        "loans": loans_r,
    }
    degraded = [
        name
        for name, result in sources.items()
        if result.get("status") != "ok"
    ]

    summary = {
        "total_items": collection_data.get("total_items"),
        "on_display": collection_data.get("on_display"),
        "in_storage": collection_data.get("in_storage"),
        "under_conservation": collection_data.get(
            "under_conservation",
            conservation_data.get("treatments_in_progress"),
        ),
        "active_loans": loans_data.get("active_loans"),
        "overdue_loans": loans_data.get("overdue_loans"),
        "upcoming_exhibitions": loans_data.get("upcoming_exhibitions"),
        "environmental_warnings": conservation_data.get("environmental_warnings"),
    }

    # Do not coerce missing upstreams to 0 — leave null so UI can show “unavailable”
    return {
        "collection": collection_r,
        "conservation": conservation_r,
        "loans": loans_r,
        "summary": summary,
        "meta": {
            "status": "degraded" if degraded else "ok",
            "unavailable": degraded,
        },
    }
