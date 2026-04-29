"""Tochka acquiring API v1.0 client.

Docs: https://developers.tochka.com/
Base: https://enter.tochka.com/uapi/acquiring/v1.0

Auth: Bearer JWT issued in Точка кабинете для интернет-эквайринга.
"""
from __future__ import annotations

import logging
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class TochkaError(Exception):
    """Raised on Tochka API failure."""


def _is_configured() -> bool:
    return bool(settings.TOCHKA_JWT and settings.TOCHKA_CUSTOMER_CODE)


def _headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {settings.TOCHKA_JWT}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


async def create_payment_operation(
    *,
    amount: float,
    purpose: str,
    order_id: str,
    redirect_url: str | None = None,
    fail_url: str | None = None,
    consumer_id: str | None = None,
    payment_mode: list[str] | None = None,
    client_email: str | None = None,
    client_phone: str | None = None,
    item_name: str | None = None,
) -> dict[str, Any]:
    """Create a payment operation and return Tochka response.

    Returns dict with at least: operationId, paymentLink, status.
    """
    if not _is_configured():
        raise TochkaError("Tochka not configured (TOCHKA_JWT / TOCHKA_CUSTOMER_CODE)")

    amount_str = f"{float(amount):.2f}"
    item_label = (item_name or purpose or "Подписка")[:128]

    client_info: dict[str, Any] = {}
    if client_email:
        client_info["email"] = client_email
    if client_phone:
        client_info["phone"] = client_phone
    # Tochka requires either email or phone for receipt delivery (54-ФЗ).
    if not client_info:
        client_info["email"] = "noreply@meepo.su"

    body = {
        "Data": {
            "customerCode": settings.TOCHKA_CUSTOMER_CODE,
            "amount": amount_str,
            "purpose": (purpose or item_label)[:140],
            "paymentMode": payment_mode or ["sbp", "card"],
            "redirectUrl": redirect_url or settings.TOCHKA_REDIRECT_URL,
            "failRedirectUrl": fail_url or settings.TOCHKA_FAIL_URL,
            "saveCard": False,
            "preAuthorization": False,
            "Client": client_info,
            "Items": [
                {
                    "vatType": "none",
                    "name": item_label,
                    "amount": amount_str,
                    "quantity": 1,
                    "paymentMethod": "full_payment",
                    "paymentObject": "service",
                    "measure": "шт.",
                }
            ],
        }
    }
    if consumer_id:
        body["Data"]["consumerId"] = consumer_id

    url = f"{settings.TOCHKA_BASE_URL.rstrip('/')}/payments_with_receipt"
    timeout = httpx.Timeout(20.0, connect=10.0)
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(url, json=body, headers=_headers())
    except httpx.RequestError as e:
        logger.error("Tochka request error: %s", e)
        raise TochkaError(f"network error: {e}") from e

    if resp.status_code >= 400:
        logger.error("Tochka HTTP %s: %s", resp.status_code, resp.text[:500])
        raise TochkaError(f"HTTP {resp.status_code}: {resp.text[:300]}")

    try:
        data = resp.json()
    except Exception as e:
        raise TochkaError(f"invalid JSON: {e}") from e

    inner = data.get("Data", data)
    return {
        "operation_id": inner.get("operationId") or inner.get("operation_id"),
        "payment_link": inner.get("paymentLink") or inner.get("payment_link"),
        "status": inner.get("status"),
        "raw": data,
    }


async def get_payment_operation(operation_id: str) -> dict[str, Any]:
    """Fetch payment operation status from Tochka."""
    if not _is_configured():
        raise TochkaError("Tochka not configured")
    url = (
        f"{settings.TOCHKA_BASE_URL.rstrip('/')}"
        f"/{settings.TOCHKA_CUSTOMER_CODE}/payments/{operation_id}"
    )
    timeout = httpx.Timeout(15.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.get(url, headers=_headers())
    if resp.status_code >= 400:
        raise TochkaError(f"HTTP {resp.status_code}: {resp.text[:300]}")
    return resp.json()
