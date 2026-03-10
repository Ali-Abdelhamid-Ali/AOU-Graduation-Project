from __future__ import annotations

import pytest

from src.services.infrastructure.retry_utils import (
    async_retry,
    should_retry_http_exception,
)


@pytest.mark.unit
async def test_async_retry_skips_storage_client_errors() -> None:
    attempts = 0

    @async_retry(
        max_retries=3,
        initial_delay=0,
        backoff_factor=1,
        retry_if=should_retry_http_exception,
    )
    async def flaky():
        nonlocal attempts
        attempts += 1
        raise RuntimeError(
            "{'statusCode': 400, 'error': InvalidRequest, 'message': mime type application/octet-stream is not supported}"
        )

    with pytest.raises(RuntimeError):
        await flaky()

    assert attempts == 1


@pytest.mark.unit
async def test_async_retry_retries_transient_failures() -> None:
    attempts = 0

    @async_retry(
        max_retries=3,
        initial_delay=0,
        backoff_factor=1,
        retry_if=should_retry_http_exception,
    )
    async def flaky():
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise ConnectionError("temporary network failure")
        return "ok"

    assert await flaky() == "ok"
    assert attempts == 3
