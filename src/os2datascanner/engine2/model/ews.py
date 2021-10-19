from io import BytesIO
from urllib.parse import urlsplit, quote
from contextlib import contextmanager
from exchangelib import (
    Account, Message, Credentials, IMPERSONATION,
    Configuration, FaultTolerance, ExtendedProperty)
from exchangelib.errors import (ErrorServerBusy, ErrorItemNotFound)
from exchangelib.protocol import BaseProtocol

from .utilities import NamedTemporaryResource
from ..utilities.backoff import run_with_backoff
from ..conversions.types import OutputType
from ..conversions.utilities.results import SingleResult
from .core import Source, Handle, FileResource


BaseProtocol.SESSION_POOLSIZE = 1


# An "entry ID" is the special identifier used to open something in the Outlook
# rich client (after converting it to a hexadecimal string). This property can
# be retrieved over the EWS protocol, but exchangelib doesn't do so by default;
# make sure that it does by explicitly registering the property details

class EntryID(ExtendedProperty):
    property_tag = 4095
    property_type = 'Binary'


Message.register("entry_id", EntryID)


OFFICE_365_ENDPOINT = "https://outlook.office365.com/EWS/Exchange.asmx"
# XXX: actually use Microsoft Graph to do this properly (deeplink URLs are
# available through an email's "webLink" property)
_OFFICE_365_DEEPLINK = (
        "https://outlook.office365.com/owa/?ItemID={0}"
        "&exvsurl=1&viewmodel=ReadMessageItem")


def _make_o365_deeplink(outlook_message_id):
    return _OFFICE_365_DEEPLINK.format(quote(outlook_message_id, safe=''))


def _dictify_headers(headers):
    if headers:
        d = InsensitiveDict()
        for mh in headers:
            n, v = mh.name, mh.value
            if n not in d:
                d[n] = v
            else:
                if isinstance(d[n], list):
                    d[n].append(v)
                else:
                    d[n] = [d[n], v]
        return d
    else:
        return None


class InsensitiveDict(dict):
    def __getitem__(self, key):
        return super().__getitem__(key.lower())

    def __setitem__(self, key, value):
        return super().__setitem__(key.lower(), value)


class EWSAccountSource(Source):
    type_label = "ews"

    def __init__(self, domain, server, admin_user, admin_password, user):
        self._domain = domain
        self._server = server
        self._admin_user = admin_user
        self._admin_password = admin_password
        self._user = user

    @property
    def user(self):
        return self._user

    @property
    def domain(self):
        return self._domain

    @property
    def address(self):
        return "{0}@{1}".format(self.user, self.domain)

    def _generate_state(self, sm):
        service_account = Credentials(
                username=self._admin_user, password=self._admin_password)
        config = Configuration(
                retry_policy=FaultTolerance(max_wait=1800),
                service_endpoint=self._server,
                credentials=service_account if self._server else None)

        account = Account(
                primary_smtp_address=self.address,
                credentials=service_account,
                config=config,
                autodiscover=not bool(self._server),
                access_type=IMPERSONATION)

        try:
            yield account
        finally:
            # XXX: we should, in principle, close account.protocol here, but
            # exchangelib seems to keep a reference to it internally and so
            # waits forever if we do
            pass

    def censor(self):
        return EWSAccountSource(
                self._domain, self._server, None, None, self._user)

    def handles(self, sm):  # noqa: CCR001, E501 too high cognitive complexity
        account = sm.open(self)

        def relevant_folders():
            for container in account.msg_folder_root.walk():
                if (container.folder_class != "IPF.Note"
                        or container.total_count == 0):
                    continue
                yield container

        def relevant_mails(relevant_folders):
            for folder in relevant_folders:
                for mail in (m
                             for m in folder.all().only("id", "headers", "entry_id")
                             if isinstance(m, Message) and hasattr(m, "entry_id")):
                    headers = _dictify_headers(mail.headers)
                    if headers:
                        yield EWSMailHandle(
                            self,
                            "{0}.{1}".format(folder.id, mail.id),
                            headers.get("subject", "(no subject)"),
                            folder.name,
                            mail.entry_id.hex())

        yield from relevant_mails(relevant_folders())

    def to_json_object(self):
        return dict(
            **super().to_json_object(),
            domain=self._domain,
            server=self._server,
            admin_user=self._admin_user,
            admin_password=self._admin_password,
            user=self._user,
        )

    @staticmethod
    @Source.url_handler("test-ews365")
    def from_url(url):
        scheme, netloc, path, _, _ = urlsplit(url)
        auth, domain = netloc.split("@", maxsplit=1)
        au, ap = auth.split(":", maxsplit=1)
        return EWSAccountSource(
                domain=domain,
                server=OFFICE_365_ENDPOINT,
                admin_user="{0}@{1}".format(au, domain),
                admin_password=ap,
                user=path[1:])

    @staticmethod
    @Source.json_handler(type_label)
    def from_json_object(obj):
        return EWSAccountSource(
                obj["domain"], obj["server"], obj["admin_user"],
                obj["admin_password"], obj["user"])


class EWSMailResource(FileResource):
    def __init__(self, handle, sm):
        super().__init__(handle, sm)
        self._mr = None
        self._ids = self.handle.relative_path.split(".", maxsplit=1)
        self._message = None

    def _generate_metadata(self):
        yield "email-account", self.handle.source.address
        yield from super()._generate_metadata()

    def check(self) -> bool:
        folder_id, mail_id = self._ids
        account = self._get_cookie()

        def _retrieve_message():
            return account.root.get_folder(
                    folder_id).all().only("message_id").get(id=mail_id)
        m, _ = run_with_backoff(_retrieve_message, ErrorServerBusy, fuzz=0.25)

        return not isinstance(m, ErrorItemNotFound)

    def get_message_object(self):
        if not self._message:
            folder_id, mail_id = self._ids
            account = self._get_cookie()

            def _retrieve_message():
                return account.root.get_folder(folder_id).get(id=mail_id)
            self._message, _ = run_with_backoff(
                    _retrieve_message, ErrorServerBusy, fuzz=0.25)
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
        with BytesIO(self.get_message_object().mime_content) as fp:
            yield fp

    # XXX: actually pack these SingleResult objects into a MultipleResults

    def get_size(self):
        return SingleResult(None, "size", self.get_message_object().size)

    def get_last_modified(self):
        o = self.get_message_object()
        oldest_stamp = max(filter(
                lambda ts: ts is not None,
                [o.datetime_created, o.datetime_received, o.datetime_sent]))
        return SingleResult(None, OutputType.LastModified, oldest_stamp)

    def compute_type(self):
        return "message/rfc822"


class EWSMailHandle(Handle):
    type_label = "ews"
    resource_type = EWSMailResource

    # The mail subject and folder name are useful for presentation purposes,
    # but not important when computing equality
    eq_properties = Handle.BASE_PROPERTIES

    def __init__(
        self,
        source: EWSAccountSource,
        path: str,
        mail_subject: str,
        folder_name: str,
        entry_id: int,
    ):
        super().__init__(source, path)
        self._mail_subject = mail_subject
        self._folder_name = folder_name
        self._entry_id = entry_id

    @property
    def presentation(self):
        return "\"{0}\" (in folder {1} of account {2})".format(
                self._mail_subject,
                self._folder_name or "(unknown folder)", self.source.address)

    @property
    def presentation_url(self):
        # There appears to be no way to extract a webmail URL from an arbitrary
        # EWS server (and why should there be?), so at present we only support
        # web links to Office 365 mails
        if self.source._server == OFFICE_365_ENDPOINT:
            message_id = self.relative_path.split(".", maxsplit=1)[1]
            return _make_o365_deeplink(message_id)
        elif self._entry_id:
            # ... although, if we have an entry ID, then we can at least try to
            # point Outlook at the relevant mail
            return "outlook:{0}".format(self._entry_id)
        else:
            return None

    @property
    def sort_key(self):
        "Return adress@example.com/folder"
        return "{0}/{1}".format(
            self.source.address,
            self._folder_name.removeprefix("/") or "(unknown folder)")

    @property
    def presentation_name(self):
        return self._mail_subject

    def censor(self):
        return EWSMailHandle(
                self.source.censor(), self.relative_path,
                self._mail_subject, self._folder_name,
                self._entry_id)

    def guess_type(self):
        return "message/rfc822"

    def to_json_object(self):
        return dict(
            **super().to_json_object(),
            mail_subject=self._mail_subject,
            folder_name=self._folder_name,
            entry_id=self._entry_id,
        )

    @staticmethod
    @Handle.json_handler(type_label)
    def from_json_object(obj):
        return EWSMailHandle(Source.from_json_object(
            obj["source"]),
            obj["path"], obj["mail_subject"],
            obj.get("folder_name"), obj.get("entry_id"))
