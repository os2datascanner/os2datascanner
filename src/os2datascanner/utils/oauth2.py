import logging
import requests


logger = logging.getLogger(__name__)


def _default_wrapper(function, *args, **kwargs):
    return function(*args, **kwargs)


def mint_cc_token(
        endpoint: str,  # URL
        client_id: str,
        client_secret: str,
        *, wrapper=None, post_timeout=60, **kwargs):
    """Retrieves a token from the given endpoint following the OAuth 2.0
    client credentials flow.

    All keyword arguments are passed into the JSON body of the request, apart
    from two: the wrapper argument can be set to wrap this operation in (for
    example) a retrier, and the post_timeout argument can be set to specify a
    timeout for the HTTP POST request."""
    response = (wrapper or _default_wrapper)(
            requests.post,
            endpoint,
            {
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
                **kwargs
            },
            timeout=post_timeout)
    response.raise_for_status()
    logger.info(f"Collected new token from {endpoint}")
    return response.json()["access_token"]


__all__ = [
    "mint_cc_token",
]
