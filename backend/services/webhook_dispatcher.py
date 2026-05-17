"""HTTP webhook firing — Section 7.6 / Section 14.

Pure HTTP + signing; no database access (the pipeline supplies the
subscription list via the repository, keeping this module testable without a
network or a DB). Payloads are signed HMAC-SHA256 and sent in the
``X-SEO-Signature`` header as ``sha256=<hexdigest>``.
"""

import hashlib
import hmac
import json
import logging
from collections.abc import Awaitable, Callable, Sequence
from datetime import datetime, timezone

logger = logging.getLogger("seo_portal.webhook")

# A sender takes (url, body_bytes, headers) and raises on failure.
Sender = Callable[[str, bytes, dict], Awaitable[None]]


def sign(secret: str, body: bytes) -> str:
    """HMAC-SHA256 hex digest of the raw body using the webhook secret."""
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def build_envelope(event: str, data: dict) -> tuple[dict, bytes]:
    """Section 7.6 envelope + its canonical JSON bytes (stable for signing)."""
    envelope = {
        "event": event,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": data,
    }
    body = json.dumps(
        envelope, separators=(",", ":"), sort_keys=True
    ).encode()
    return envelope, body


async def _httpx_sender(url: str, body: bytes, headers: dict) -> None:
    import httpx

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(url, content=body, headers=headers)
        resp.raise_for_status()


async def deliver(
    subscriptions: Sequence,
    event: str,
    data: dict,
    *,
    sender: Sender | None = None,
) -> list[tuple]:
    """Deliver one event to every subscription. Best-effort: a failing
    endpoint is logged, never raised, so one bad webhook can't fail an audit.

    Each subscription must expose ``.id``, ``.url`` and ``.secret``.
    Returns ``[(webhook_id, delivered: bool), ...]``.
    """
    send = sender or _httpx_sender
    _, body = build_envelope(event, data)
    results: list[tuple] = []
    for sub in subscriptions:
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "prithvi-seo-portal/1.0",
        }
        if sub.secret:
            headers["X-SEO-Signature"] = "sha256=" + sign(sub.secret, body)
        try:
            await send(sub.url, body, headers)
            delivered = True
        except Exception:  # noqa: BLE001 — never let a webhook abort the audit
            logger.warning(
                "Webhook delivery failed for %s (%s)", sub.url, event,
                exc_info=True,
            )
            delivered = False
        results.append((sub.id, delivered))
    return results
