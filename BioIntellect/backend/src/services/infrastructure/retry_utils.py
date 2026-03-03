import asyncio
import functools
import logging
from typing import Callable, Type, Tuple

logger = logging.getLogger("infrastructure.retry")


def async_retry(
    max_retries: int = 3,
    backoff_factor: float = 2.0,
    initial_delay: float = 1.0,
    retry_on_exceptions: Tuple[Type[Exception], ...] = (Exception,),
):
    """
    Plan Section 8.A: Async Retry Decorator with Exponential Backoff.
    """

    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            from src.security.config import security_config

            if not getattr(security_config, "ENABLE_RETRIES", True):
                return await func(*args, **kwargs)

            delay = initial_delay
            last_exception = None

            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except retry_on_exceptions as e:
                    last_exception = e
                    if attempt == max_retries - 1:
                        logger.error(
                            f"Final attempt failed for {func.__name__}: {str(e)}"
                        )
                        raise e

                    logger.warning(
                        f"Attempt {attempt + 1} failed for {func.__name__}: {str(e)}. "
                        f"Retrying in {delay}s..."
                    )
                    await asyncio.sleep(delay)
                    delay *= backoff_factor

            raise last_exception

        return wrapper

    return decorator

