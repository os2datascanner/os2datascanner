from io import BytesIO
from contextlib import contextmanager

from ...conversions.utilities.results import SingleResult
from ..core import Handle, Source, Resource, FileResource
from ..derived.derived import DerivedSource
from ..utilities import NamedTemporaryResource
from .utilities import MSGraphSource, ignore_responses


class MSGraphMailSource(MSGraphSource):
    type_label = "msgraph-mail"

    def handles(self, sm):
        for user in self._list_users(sm)["value"]:
            pn = user["userPrincipalName"]
            with ignore_responses(404):
                any_mails = sm.open(self).get(
                        "users/{0}/messages?$select=id&$top=1".format(pn))
                if not any_mails["value"]:
                    # This user has a mail account that contains no mails
                    continue
                else:
                    yield MSGraphMailAccountHandle(self, pn)

    @staticmethod
    @Source.json_handler(type_label)
    def from_json_object(obj):
        return MSGraphMailSource(
                client_id=obj["client_id"],
                tenant_id=obj["tenant_id"],
                client_secret=obj["client_secret"])


DUMMY_MIME = "application/vnd.os2.datascanner.graphmailaccount"


class MSGraphMailAccountResource(Resource):
    def check(self) -> bool:
        response = self._get_cookie().get_raw(
                "users/{0}/messages?$select=id&$top=1".format(
                        self.handle.relative_path))
        return response.status_code not in (404, 410,)

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
        for message in sm.open(self).get(
                "users/{0}/messages?$select=id,subject,webLink".format(
                        pn))["value"]:
            yield MSGraphMailMessageHandle(self,
                                           message["id"],
                                           message["subject"],
                                           message["webLink"])


class MSGraphMailMessageResource(FileResource):
    def __init__(self, handle, sm):
        super().__init__(handle, sm)
        self._message = None

    def _generate_metadata(self):
        yield "email-account", self.handle.source.handle.relative_path
        yield from super()._generate_metadata()

    def check(self) -> bool:
        response = self._get_cookie().get_raw(
                self.make_object_path() + "?$select=id")
        return response.status_code not in (404, 410,)

    def make_object_path(self):
        return "users/{0}/messages/{1}".format(
                self.handle.source.handle.relative_path,
                self.handle.relative_path)

    def get_message_metadata(self):
        if not self._message:
            self._message = self._get_cookie().get(
                    self.make_object_path() + "?$select=lastModifiedDateTime")
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
        response = self._get_cookie().get(
                self.make_object_path() + "/$value", json=False)
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

    def __init__(self, source, path, mail_subject, weblink):
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
