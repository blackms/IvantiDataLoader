"""Retry decorator with exponential backoff."""
import functools
import random
import time
from typing import Any, Callable, Optional, Type, Union, Tuple

from loguru import logger

from ..core.exceptions import RetryableError


class RetryConfig:
    """Configuration for retry behavior."""

    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True
    ):
        """
        Initialize retry configuration.

        Args:
            max_attempts: Maximum number of retry attempts
            base_delay: Base delay between retries in seconds
            max_delay: Maximum delay between retries in seconds
            exponential_base: Base for exponential backoff
            jitter: Whether to add random jitter to delays
        """
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter


def retry_with_backoff(
    retryable_exceptions: Union[
        Type[Exception],
        Tuple[Type[Exception], ...],
    ] = RetryableError,
    config: Optional[RetryConfig] = None,
    on_retry: Optional[Callable[[Exception, int], None]] = None
) -> Callable:
    """
    Decorator for retrying operations with exponential backoff.

    Args:
        retryable_exceptions: Exception types to retry on
        config: Retry configuration
        on_retry: Callback function to execute before each retry

    Returns:
        Callable: Decorated function
    """
    config = config or RetryConfig()

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            attempt = 1
            last_exception = None

            while attempt <= config.max_attempts:
                try:
                    return func(*args, **kwargs)

                except retryable_exceptions as e:
                    last_exception = e

                    # Check if we should retry
                    if attempt == config.max_attempts:
                        logger.error(
                            "Max retry attempts reached",
                            function=func.__name__,
                            attempt=attempt,
                            error=str(e)
                        )
                        raise

                    # Calculate delay with exponential backoff
                    delay = min(
                        config.base_delay * (config.exponential_base ** (attempt - 1)),
                        config.max_delay
                    )

                    # Add jitter if enabled
                    if config.jitter:
                        delay = delay * (0.5 + random.random())

                    # Log retry attempt
                    logger.warning(
                        "Operation failed, retrying",
                        function=func.__name__,
                        attempt=attempt,
                        next_attempt_in=f"{delay:.2f}s",
                        error=str(e)
                    )

                    # Execute retry callback if provided
                    if on_retry:
                        try:
                            on_retry(e, attempt)
                        except Exception as callback_error:
                            logger.error(
                                "Error in retry callback",
                                error=str(callback_error)
                            )

                    # Wait before retrying
                    time.sleep(delay)
                    attempt += 1

                except Exception as e:
                    # Log non-retryable exceptions
                    logger.error(
                        "Non-retryable error occurred",
                        function=func.__name__,
                        error=str(e)
                    )
                    raise

            # This should never be reached due to the raise in the last iteration
            raise last_exception or Exception("Retry loop completed without success")

        return wrapper

    return decorator


def retry_async_with_backoff(
    retryable_exceptions: Union[
        Type[Exception],
        Tuple[Type[Exception], ...],
    ] = RetryableError,
    config: Optional[RetryConfig] = None,
    on_retry: Optional[Callable[[Exception, int], None]] = None
) -> Callable:
    """
    Decorator for retrying async operations with exponential backoff.

    Args:
        retryable_exceptions: Exception types to retry on
        config: Retry configuration
        on_retry: Callback function to execute before each retry

    Returns:
        Callable: Decorated async function
    """
    config = config or RetryConfig()

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            import asyncio
            attempt = 1
            last_exception = None

            while attempt <= config.max_attempts:
                try:
                    return await func(*args, **kwargs)

                except retryable_exceptions as e:
                    last_exception = e

                    if attempt == config.max_attempts:
                        logger.error(
                            "Max retry attempts reached",
                            function=func.__name__,
                            attempt=attempt,
                            error=str(e)
                        )
                        raise

                    delay = min(
                        config.base_delay * (config.exponential_base ** (attempt - 1)),
                        config.max_delay
                    )

                    if config.jitter:
                        delay = delay * (0.5 + random.random())

                    logger.warning(
                        "Operation failed, retrying",
                        function=func.__name__,
                        attempt=attempt,
                        next_attempt_in=f"{delay:.2f}s",
                        error=str(e)
                    )

                    if on_retry:
                        try:
                            on_retry(e, attempt)
                        except Exception as callback_error:
                            logger.error(
                                "Error in retry callback",
                                error=str(callback_error)
                            )

                    await asyncio.sleep(delay)
                    attempt += 1

                except Exception as e:
                    logger.error(
                        "Non-retryable error occurred",
                        function=func.__name__,
                        error=str(e)
                    )
                    raise

            raise last_exception or Exception("Retry loop completed without success")

        return wrapper

    return decorator