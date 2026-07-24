from __future__ import annotations

import httpx


RETRYABLE_EXCEPTIONS = (
    httpx.ConnectError,
    httpx.ConnectTimeout,
    httpx.ReadTimeout,
    httpx.WriteTimeout,
    httpx.RemoteProtocolError,
    httpx.NetworkError,
)


def is_retryable_exception(exc: Exception) -> bool:
    """
    Returns whether an exception should trigger a retry.
    """
    return isinstance(exc, RETRYABLE_EXCEPTIONS)