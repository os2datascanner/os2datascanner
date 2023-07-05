import logging
import requests


logger = logging.getLogger(__name__)


def _default_wrapper(function, *args, **kwargs):
    return function(*args, **kwargs)


def mint_cc_token(
        endpoint: str,  # URL
        client_id: str,
        client_secret: str,
        *, wrapper=None, **kwargs):
    """Retrieves a token from the given endpoint following the OAuth 2.0
    client credentials flow.

    Callers can set the wrapper keyword argument to wrap this operation in
    (for example) a retrier; all other keyword arguments are passed into the
    JSON body of the request."""
    response = (wrapper or _default_wrapper)(
            requests.post,
            endpoint,
            {
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
                **kwargs
            })
    response.raise_for_status()
    logger.info(f"Collected new token from {endpoint}")
    return response.json()["access_token"]


__all__ = [
    "mint_cc_token",
]
