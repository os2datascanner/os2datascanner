import requests


from .core import Source


def _make_token_endpoint(tenant_id):
    return "https://login.microsoftonline.com/{0}/oauth2/v2.0/token".format(
            tenant_id)


class MSGraphSource(Source):
    def __init__(self, client_id, tenant_id, client_secret):
        super().__init__()
        self._client_id = client_id
        self._tenant_id = tenant_id
        self._client_secret = client_secret

    def censor(self):
        return type(self)(self._client_id, self._tenant_id, None)

    def _generate_state(self, sm):
        response = requests.post(
                _make_token_endpoint(self._tenant_id),
                {
                    "client_id": self._client_id,
                    "scope": "https://graph.microsoft.com/.default",
                    "client_secret": self._client_secret,
                    "grant_type": "client_credentials"
                })
        response.raise_for_status()
        yield response.json()["access_token"]


class MSGraphMailSource(MSGraphSource):
    type_label = "msgraph-mail"

    def handles(self, sm):
        token = sm.open(self)
        yield from []

    def to_json_object(self):
        return {
            "client_id": self._client_id,
            "tenant_id": self._tenant_id,
            "client_secret": self._client_secret
        }

    @staticmethod
    @Source.json_handler(type_label)
    def from_json_object(cls, obj):
        return MSGraphMailSource(
                client_id=obj["client_id"],
                tenant_id=obj["tenant_id"],
                client_secret=obj["client_secret"])
