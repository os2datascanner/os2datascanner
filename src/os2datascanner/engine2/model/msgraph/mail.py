from dataclasses import dataclass
from io import BytesIO
from urllib.parse import urlsplit
from contextlib import contextmanager
from dateutil.parser import isoparse

from ...conversions.types import OutputType
from ...conversions.utilities.results import SingleResult
from ... import settings as engine2_settings
from ..core import Handle, Source, Resource, FileResource
from ..derived.derived import DerivedSource
from .utilities import MSGraphSource, ignore_responses


class MSGraphMailSource(MSGraphSource):
    type_label = "msgraph-mail"

    def __init__(self, client_id, tenant_id, client_secret, userlist=None):
        super().__init__(client_id, tenant_id, client_secret)
        self._userlist = userlist

    def handles(self, sm):  # noqa
        if self._userlist is None:
            for user in self._list_users(sm):
                pn = user["userPrincipalName"]  # e.g. dan@contoso.onmicrosoft.com
                # Getting a HTTP 404 response from the /messages endpoint means
                # that this user doesn't have a mail account at all
                with ignore_responses(404):
                    any_mails = sm.open(self).get(
                        "users/{0}/messages?$select=id&$top=1".format(pn))
                    if not any_mails["value"]:
                        # This user has a mail account that contains no mails
                        continue
                    else:
                        yield MSGraphMailAccountHandle(self, pn)

        else:
            for pn in self._userlist:
                with ignore_responses(404):
                    any_mails = sm.open(self).get(
                        "users/{0}/messages?$select=id&$top=1".format(pn))
                    if any_mails["value"]:
                        yield MSGraphMailAccountHandle(self, pn)

    def to_json_object(self):
        return dict(
                **super().to_json_object(),
                userlist=list(self._userlist) if self._userlist is not None else None)

    @staticmethod
    @Source.json_handler(type_label)
    def from_json_object(obj):
        userlist = obj.get("userlist")
        return MSGraphMailSource(
                client_id=obj["client_id"],
                tenant_id=obj["tenant_id"],
                client_secret=obj["client_secret"],
                userlist=frozenset(userlist) if userlist is not None else None)


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
    def presentation_name(self):
        return self.relative_path

    @property
    def presentation_place(self):
        return "Office 365"

    @property
    def sort_key(self):
        """ Returns a string to sort by formatted as:
            DOMAIN/ACCOUNT/MAIL_SUBJECT"""
        # We should probably look towards EWS implementation and see if you get/can get folder
        # the mail resides in and add this.
        account, domain = self.relative_path.split("@", 1)
        return f'{domain}/{account}/'

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
        ps = engine2_settings.model["msgraph"]["page_size"]

        folder_map = self._generate_folder_map(sm)

        result = sm.open(self).get(
            f"users/{pn}/messages?$select=id,subject,webLink,parentFolderId&$top={ps}")

        yield from (self._wrap(msg, folder_map) for msg in result["value"])
        # We want to get all emails for given account
        # This key takes us to the next page and is only present
        # as long as there is one.
        while '@odata.nextLink' in result:
            result = sm.open(self).follow_next_link(result["@odata.nextLink"])
            yield from (self._wrap(msg, folder_map) for msg in result["value"])

    def _generate_folder_map(self, sm):
        folder_map = {}
        pn = self.handle.relative_path
        ps = engine2_settings.model["msgraph"]["page_size"]

        result = sm.open(self).get(
            f"users/{pn}/mailFolders?$select=id,parentFolderId,displayName&$top={ps}")

        for folder in result["value"]:
            folder_map[folder["id"]] = _MailFolder(folder["id"],
                                                   folder["parentFolderId"],
                                                   folder["displayName"])

        while '@odata.nextLink' in result:
            result = sm.open(self).follow_next_link(result["@odata.nextLink"])
            for folder in result["value"]:
                folder_map[folder["id"]] = _MailFolder(folder["id"],
                                                       folder["parentFolderId"],
                                                       folder["displayName"])

        return folder_map

    def _wrap(self, message, folder_map):
        fid = message["parentFolderId"]
        folder = self._construct_folder_path(fid, folder_map)
        return MSGraphMailMessageHandle(
            self, message["id"], mail_subject=message["subject"],
            weblink=message["webLink"], folder=folder)

    def _construct_folder_path(self, fid, folder_map):
        folder = folder_map.get(fid, None)

        def _reverse_traverse(f):
            if f is None:
                return ""

            parent = folder_map.get(f._parent_folder_id, None)
            if parent is None:
                return f._display_name

            return _reverse_traverse(parent) + '/' + f._display_name

        return _reverse_traverse(folder)

    @staticmethod
    @Source.url_handler("test-msgraph")
    def from_url(url):
        scheme, netloc, path, _, _ = urlsplit(url)
        auth, tenant_id = netloc.split("@", maxsplit=1)
        client_id, client_secret = auth.split(":", maxsplit=1)
        user = path[1:]
        return MSGraphMailAccountSource(
                MSGraphMailAccountHandle(
                        MSGraphMailSource(client_id, tenant_id, client_secret),
                        user))


@dataclass
class _MailFolder:
    def __init__(self, fid, parent_folder_id, display_name):
        self._id = fid
        self._parent_folder_id = parent_folder_id
        self._display_name = display_name


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
        timestamp = self.get_message_metadata().get("lastModifiedDateTime")
        timestamp = isoparse(timestamp) if timestamp else None
        return SingleResult(None, OutputType.LastModified, timestamp)

    def compute_type(self):
        return "message/rfc822"


class MSGraphMailMessageHandle(Handle):
    type_label = "msgraph-mail-message"
    resource_type = MSGraphMailMessageResource
    eq_properties = Handle.BASE_PROPERTIES

    def __init__(self, source, path,  # noqa: R0913
                 mail_subject, weblink,
                 folder=None):
        super().__init__(source, path)
        self._mail_subject = mail_subject
        self._weblink = weblink
        self._folder = folder

    @property
    def presentation_name(self):
        return f"\"{self._mail_subject}\""

    @property
    def presentation_place(self):
        return f"{self._folder} of {str(self.source.handle)}"

    @property
    def presentation_url(self):
        return self._weblink

    @property
    def sort_key(self):
        return self.presentation_place

    def censor(self):
        return MSGraphMailMessageHandle(
                self.source.censor(), self.relative_path,
                self._mail_subject, self._weblink,
                self._folder)

    def guess_type(self):
        return "message/rfc822"

    def to_json_object(self):
        return dict(
            **super().to_json_object(),
            mail_subject=self._mail_subject,
            weblink=self._weblink,
            folder=self._folder,
        )

    @staticmethod
    @Handle.json_handler(type_label)
    def from_json_object(obj):
        return MSGraphMailMessageHandle(
                Source.from_json_object(obj["source"]),
                obj["path"], obj["mail_subject"], obj["weblink"],
                obj.get("folder", None))
