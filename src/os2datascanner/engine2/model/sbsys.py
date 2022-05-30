from contextlib import contextmanager
from io import BytesIO

import requests
from os2datascanner.engine2.model.derived.derived import DerivedSource

from .core import Source, Handle, FileResource


class SbsysSource(Source):
    type_label = "sbsys"

    def __init__(self, client_id, client_secret, token_url, api_url):
        self._client_id = client_id
        self._client_secret = client_secret
        self._token_url = token_url
        self._api_url = api_url

    def _generate_state(self, sm):
        """ Retrieves an access_token and yields SbsysCaller with it
        SbsysCaller is then used for making post and get requests"""

        # Using the oauth grant type client_credentials
        grant_type = {'grant_type': 'client_credentials'}
        access_token_response = requests.post(
            self._token_url, data=grant_type, allow_redirects=False,
            auth=(self._client_id, self._client_secret))
        # Picking out the access token
        token = access_token_response.json()["access_token"]

        yield self.SbsysCaller(token, self._api_url)

    def handles(self, sm):
        # Query parameters - currently looking for active cases only.
        query_params = {
            "SagsStatus": {
                "SagsTilstand": "Aktiv"
            }
        }

        api_search_post = sm.open(self).post(tail='sag/search', json_params=query_params)
        for c in api_search_post.json():
            # For every case, picking out the ID.
            caseId = c["Id"]
            yield SbsysHandle(self, str(caseId))

    def to_json_object(self):
        return dict(
            **super().to_json_object(),
            client_id=self._client_id,
            client_secret=self._client_secret,
            token_url=self._token_url,
            api_url=self._api_url,
        )

    @staticmethod
    @Source.json_handler(type_label)
    def from_json_object(obj):
        return SbsysSource(obj["client_id"], obj["client_secret"], obj["token_url"], obj["api_url"])

    def censor(self):
        """ Censoring out credentials """
        return SbsysSource(None, None, None, None)

    class SbsysCaller:
        """ Used to make API calls with token it receives from SbsysSource """

        def __init__(self, token, api_url):
            self._token = token
            self._api_url = api_url

        def post(self, tail, json_params):
            """ Used for Post requests to the API """
            response = requests.post(
                self._api_url + "{0}".format(tail),
                headers={'Authorization': 'Bearer {0}'.format(self._token)}, json=json_params
            )
            return response

        def get(self, tail):
            """ Used for Get requests to the API """
            response = requests.get(
                self._api_url + "{0}".format(tail),
                headers={'Authorization': 'Bearer {0}'.format(self._token)}
            )
            return response


# Used for more case specific scan
CASE_TYPE = "application/x.os2datascanner.sbsys-case"


class SbsysResource(FileResource):
    def __init__(self, handle, sm):
        super().__init__(handle, sm)

    def compute_type(self):
        return CASE_TYPE

    @contextmanager
    def make_stream(self):
        response = self._get_cookie().get(tail='sag/{0}'.format(self._handle.relative_path))
        with BytesIO(response.content) as fp:
            yield fp

    def get_size(self):
        # Byte size
        response = self._get_cookie().get(tail='sag/{0}'.format(self._handle.relative_path))
        return len(response.content)


class SbsysHandle(Handle):
    type_label = "sbsys"
    resource_type = SbsysResource
    eq_properties = Handle.BASE_PROPERTIES

    def __init__(self, source, path):
        super().__init__(source, path)

    @property
    def presentation_name(self):
        return "Sag ID: {0}".format(self.relative_path)

    @property
    def presentation_place(self):
        return "SBSYS"

    def censor(self):
        return SbsysHandle(self.source.censor(), self.relative_path)

    @staticmethod
    @Handle.json_handler(type_label)
    def from_json_object(obj):
        return SbsysHandle(Source.from_json_object(obj["source"]), obj["path"])


@Source.mime_handler(CASE_TYPE)
class SbsysCaseSource(DerivedSource):
    type_label = "sbsys-case"

    def _generate_state(self, sm):
        yield sm.open(self.handle.source)

    def handles(self, sm):
        api_search_docs = sm.open(self).get(
            tail='sag/{0}/dokumenter'.format(self.handle.relative_path))
        for d in api_search_docs.json():
            # For every document on case, picking out the DocumentId.
            docId = d["DokumentID"]
            yield SbsysCaseHandle(self, str(docId))


class SbsysCaseResource(FileResource):

    def __init__(self, handle, sm):
        super().__init__(handle, sm)

    @contextmanager
    def make_stream(self):
        response = self._get_cookie().get(tail='dokument/{0}'.format(self.handle.relative_path))
        with BytesIO(response.content) as fp:
            yield fp

    def get_size(self):
        # Byte size
        response = self._get_cookie().get(tail='dokument/{0}'.format(self.handle.relative_path))
        return len(response.content)


class SbsysCaseHandle(Handle):
    type_label = "sbsys-case"
    resource_type = SbsysCaseResource
    eq_properties = Handle.BASE_PROPERTIES

    @property
    def presentation_name(self):
        return self.relative_path

    @property
    def presentation_place(self):
        return str(self.source.handle)

    def censor(self):
        return SbsysCaseHandle(self.source.censor(), self.relative_path)

    @staticmethod
    @Handle.json_handler(type_label)
    def from_json_object(obj):
        return SbsysCaseHandle(Source.from_json_object(obj["source"]), obj["path"])
