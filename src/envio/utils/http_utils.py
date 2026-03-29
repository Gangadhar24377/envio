"""HTTP utilities with retry logic for network operations."""

from __future__ import annotations

import requests
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)


class NetworkError(Exception):
    """Base exception for network errors that can be retried."""

    pass


class HTTPError(NetworkError):
    """Exception for HTTP errors."""

    pass


class TimeoutError(NetworkError):
    """Exception for timeout errors."""

    pass


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((requests.ConnectionError, requests.Timeout)),
    before_sleep=lambda retry_state: None,
)
def get_with_retry(url: str, timeout: int = 10, **kwargs) -> requests.Response:
    """Make a GET request with retry logic.

    Args:
        url: URL to fetch
        timeout: Request timeout in seconds
        **kwargs: Additional arguments to pass to requests.get

    Returns:
        Response object

    Raises:
        requests.RequestException: If all retries fail
    """
    response = requests.get(url, timeout=timeout, **kwargs)
    return response


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((requests.ConnectionError, requests.Timeout)),
    before_sleep=lambda retry_state: None,
)
def post_with_retry(url: str, timeout: int = 10, **kwargs) -> requests.Response:
    """Make a POST request with retry logic.

    Args:
        url: URL to post to
        timeout: Request timeout in seconds
        **kwargs: Additional arguments to pass to requests.post

    Returns:
        Response object

    Raises:
        requests.RequestException: If all retries fail
    """
    response = requests.post(url, timeout=timeout, **kwargs)
    return response
