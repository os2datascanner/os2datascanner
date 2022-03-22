import logging
import requests
from contextlib import contextmanager

from os2datascanner.engine2.utilities.backoff import WebRetrier

from ..core import Source


logger = logging.getLogger(__name__)


def _make_token_endpoint(tenant_id):
    return "https://login.microsoftonline.com/{0}/oauth2/v2.0/token".format(
            tenant_id)


class MSGraphSource(Source):
    yields_independent_sources = True

    def __init__(self, client_id, tenant_id, client_secret):
        super().__init__()
        self._client_id = client_id
        self._tenant_id = tenant_id
        self._client_secret = client_secret

    def censor(self):
        return type(self)(self._client_id, self._tenant_id, None)

    def make_token(self):
        response = WebRetrier().run(
                requests.post,
                _make_token_endpoint(self._tenant_id),
                {
                    "client_id": self._client_id,
                    "scope": "https://graph.microsoft.com/.default",
                    "client_secret": self._client_secret,
                    "grant_type": "client_credentials"
                })
        response.raise_for_status()
        logger.info("Collected new token")
        return response.json()["access_token"]

    def _generate_state(self, sm):
        with requests.Session() as session:
            yield MSGraphSource.GraphCaller(self.make_token, session)

    def _list_users(self, sm):
        return sm.open(self).get("users")

    class GraphCaller:
        def __init__(self, token_creator, session=None):
            self._token_creator = token_creator
            self._token = token_creator()

            self._session = session or requests

        def _make_headers(self):
            return {
                "authorization": "Bearer {0}".format(self._token),
            }

        def get_raw(self, tail):
            return WebRetrier().run(
                    self._session.get,
                    "https://graph.microsoft.com/v1.0/{0}".format(tail),
                    headers=self._make_headers())

        def get(self, tail, *, json=True, _retry=False):
            response = self.get_raw(tail)
            try:
                response.raise_for_status()
                if json:
                    return response.json()
                else:
                    return response.content
            except requests.exceptions.HTTPError as ex:
                # If _retry, it means we have a status code 401 but are trying a second time.
                # It should've succeeded the first time, so we raise an exc to avoid a potential
                # endless loop
                if ex.response.status_code != 401 or _retry:
                    raise ex

                self._token = self._token_creator()
                return self.get(tail, json=json, _retry=True)

        def paginated_get(self, endpoint: str):
            """ Performs a GET request on specified MSGraph endpoint and
            uses generators to go through pages if response is paginated"""
            result = self.get(endpoint)
            yield from result.get('value')

            while '@odata.nextLink' in result:
                result = self.follow_next_link(result["@odata.nextLink"])
                yield from result.get('value')

        def head_raw(self, tail):
            return WebRetrier().run(
                    self._session.head,
                    "https://graph.microsoft.com/v1.0/{0}".format(tail),
                    headers=self._make_headers())

        def head(self, tail, _retry=False):
            response = self.head_raw(tail)
            try:
                response.raise_for_status()
                return response
            except requests.exceptions.HTTPError as ex:
                if ex.response.status_code != 401 or _retry:
                    raise ex

            self._token = self._token_creator()
            return self.head(tail, _retry=True)

        def follow_next_link(self, next_page, _retry=False):
            response = WebRetrier().run(
                    self._session.get, next_page, headers=self._make_headers())
            try:
                response.raise_for_status()
                return response.json()
            except requests.exceptions.HTTPError as ex:
                if ex.response.status_code != 401 or _retry:
                    raise ex
            self._token = self._token_creator()
            return self.follow_next_link(next_page, _retry=True)

    def to_json_object(self):
        return dict(
            **super().to_json_object(),
            client_id=self._client_id,
            tenant_id=self._tenant_id,
            client_secret=self._client_secret,
        )


@contextmanager
def ignore_responses(*status_codes):
    try:
        yield
    except requests.exceptions.HTTPError as ex:
        if ex.response.status_code in status_codes:
            pass
        else:
            raise
