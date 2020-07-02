from io import BytesIO
import requests
from contextlib import contextmanager
from simplejson.decoder import JSONDecodeError

from ..conversions.utilities.results import SingleResult
from .core import Handle, Source, Resource, FileResource
from .derived.derived import DerivedSource


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
        token = response.json()["access_token"]

        def _graph_get(tail):
            response = requests.get(
                    "https://graph.microsoft.com/v1.0/{0}".format(tail),
                    headers={"authorization": "Bearer {0}".format(token)})
            response.raise_for_status()
            try:
                return response.json()
            except JSONDecodeError:
                return response.content
        yield _graph_get

    def _list_users(self, sm):
        return sm.open(self)("users")


class MSGraphMailSource(MSGraphSource):
    type_label = "msgraph-mail"

    def handles(self, sm):
        for user in self._list_users(sm)["value"]:
            pn = user["userPrincipalName"]
            any_mails = sm.open(self)(
                    "users/{0}/messages?$select=id&$top=1".format(pn))
            if not any_mails["value"]:
                continue
            else:
                yield MSGraphMailAccountHandle(self, pn)

    def to_json_object(self):
        return dict(**super().to_json_object(), **{
            "client_id": self._client_id,
            "tenant_id": self._tenant_id,
            "client_secret": self._client_secret
        })

    @staticmethod
    @Source.json_handler(type_label)
    def from_json_object(obj):
        return MSGraphMailSource(
                client_id=obj["client_id"],
                tenant_id=obj["tenant_id"],
                client_secret=obj["client_secret"])


DUMMY_MIME = "application/vnd.os2.datascanner.graphmailaccount"


class MSGraphMailAccountResource(Resource):
    def compute_type(self):
        return DUMMY_MIME


@Handle.stock_json_handler("msgraph-mail-account")
class MSGraphMailAccountHandle(Handle):
    type_label = "msgraph-mail-account"
    resource_type = MSGraphMailAccountResource

    @property
    def presentation(self):
        return self.relative_path

    def guess_type(self):
        return DUMMY_MIME

    def censor(self):
        return MSGraphMailAccountHandle(
                self.source.censor(), self.relative_path)


@Source.mime_handler(DUMMY_MIME)
class MSGraphMailAccountSource(DerivedSource):
    type_label = "msgraph-mail-account"

    def _generate_state(self, sm):
        yield sm.open(self.handle.source)

    def handles(self, sm):
        pn = self.handle.relative_path
        for message in sm.open(self)(
                "users/{0}/messages?$select=id,subject,webLink".format(
                        pn))["value"]:
            yield MSGraphMailMessageHandle(self,
                    message["id"], message["subject"], message["webLink"])


class MSGraphMailMessageResource(FileResource):
    def __init__(self, handle, sm):
        super().__init__(handle, sm)
        self._message = None

    def get_message_object(self):
        if not self._message:
            self._message = self._get_cookie()("users/{0}/messages/{1}/".format(
                    self.handle.source.handle.relative_path,
                    self.handle.relative_path))
        return self._message

    @contextmanager
    def make_path(self):
        with NamedTemporaryResource(self.handle.name) as ntr:
            with ntr.open("wb") as res:
                with self.make_stream() as s:
                    res.write(s.read())
            yield ntr.get_path()

    @contextmanager
    def make_stream(self):
        response = self._get_cookie()("users/{0}/messages/{1}/$value".format(
                self.handle.source.handle.relative_path,
                self.handle.relative_path))
        with BytesIO(response) as fp:
            yield fp

    # XXX: actually pack these SingleResult objects into a MultipleResults

    def get_size(self):
        # XXX: there's no obvious way to implement this, but is this a problem?
        # Do we really need it for anything?
        return SingleResult(None, 'size', 1024)

    def get_last_modified(self):
        return super().get_last_modified()

    def compute_type(self):
        return "message/rfc822"


class MSGraphMailMessageHandle(Handle):
    type_label = "msgraph-mail-message"
    resource_type = MSGraphMailMessageResource
    eq_properties = Handle.BASE_PROPERTIES

    def __init__(self, source, path, mail_subject, weblink=None):
        super().__init__(source, path)
        self._mail_subject = mail_subject
        self._weblink = weblink

    @property
    def presentation(self):
        return "\"{0}\" (in account {1})".format(
                self._mail_subject, self.source.handle.relative_path)

    @property
    def presentation_url(self):
        return self._weblink

    def censor(self):
        return MSGraphMailMessageHandle(
                self.source.censor(), self.relative_path,
                self._mail_subject, self._weblink)

    def guess_type(self):
        return "message/rfc822"

    def to_json_object(self):
        return dict(**super().to_json_object(), **{
            "mail_subject": self._mail_subject,
            "weblink": self._weblink
        })

    @staticmethod
    @Handle.json_handler(type_label)
    def from_json_object(obj):
        return MSGraphMailMessageHandle(
                Source.from_json_object(obj["source"]),
                obj["path"], obj["mail_subject"], obj["weblink"])
