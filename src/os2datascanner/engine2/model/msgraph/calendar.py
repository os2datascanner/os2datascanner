from io import BytesIO
from contextlib import contextmanager

from ...conversions.utilities.results import SingleResult
from ... import settings as engine2_settings
from ..core import Handle, Source, Resource, FileResource
from ..derived.derived import DerivedSource
from ..utilities import NamedTemporaryResource
from .utilities import MSGraphSource, ignore_responses


class MSGraphCalendarSource(MSGraphSource):
    type_label = "msgraph-calendar"

    def handles(self, sm):
        for user in self._list_users(sm)["value"]:
            pn = user["userPrincipalName"]

            with ignore_responses(404):
                any_events = sm.open(self).get(
                    "users/{0}/events?$select=id&$top=1".format(pn))
                if not any_events["value"]:
                    continue

                yield MSGraphCalendarAccountHandle(self, pn)

    @staticmethod
    @Source.json_handler(type_label)
    def from_json_object(obj):
        return MSGraphCalendarSource(
            client_id=obj["client_id"],
            tenant_id=obj["tenant_id"],
            client_secret=obj["client_secret"])


DUMMY_MIME = "application/vnd.os2.datascanner.graphcalendaraccount"


class MSGraphCalendarAccountResource(Resource):
    def check(self) -> bool:
        response = self._get_cookie().get_raw(
            "users/{0}/events?$select=id&$top=1".format(
                self.handle.relative_path))
        return response.status_code not in (404, 410,)

    def compute_type(self):
        return DUMMY_MIME


@Handle.stock_json_handler("msgraph-calendar-account")
class MSGraphCalendarAccountHandle(Handle):
    type_label = "msgraph-calendar-account"
    resource_type = MSGraphCalendarAccountResource

    @property
    def presentation(self):
        return self.relative_path

    def guess_type(self):
        return DUMMY_MIME

    def censor(self):
        return MSGraphCalendarAccountHandle(
            self.source.censor(), self.relative_path)


@Source.mime_handler(DUMMY_MIME)
class MSGraphCalendarAccountSource(DerivedSource):
    type_label = "msgraph-calendar-account"

    def _generate_state(self, sm):
        yield sm.open(self.handle.source)

    def handles(self, sm):
        pn = self.handle.relative_path
        result = sm.open(self).get(
            "users/{}/events?$select=id,subject,webLink&$top={}".format(
                pn, engine2_settings.model["msgraph"]["page_size"]))

        yield from (self._wrap(msg) for msg in result["value"])

        while '@odata.nextLink' in result:
            result = sm.open(self).follow_next_link(result["@odata.nextLink"])
            yield from (self._wrap(evt) for evt in result["value"])

    def _wrap(self, event):
        return MSGraphCalendarEventHandle(
            self, event["id"], event["subject"], event["webLink"])


class MSGraphCalendarEventResource(FileResource):
    def __init__(self, handle, sm):
        super().__init__(handle, sm)
        self._event = None
        self._body = None

    def _generate_metadata(self):
        yield "email-account", self.handle.source.handle.relative_path
        yield from super()._generate_metadata()

    def _get_body(self):
        if not self._body:
            self._body = self._get_cookie().get(
                    self.make_object_path() + "?$select=body")
        return self._body

    def check(self) -> bool:
        response = self._get_cookie().get_raw(
                self.make_object_path() + "?$select=id")
        return response.status_code not in (404, 410,)

    def make_object_path(self):
        return "users/{0}/events/{1}".format(
            self.handle.source.handle.relative_path,
            self.handle.relative_path)

    def get_event_metadata(self):
        if not self._event:
            self._event = self._get_cookie().get(
                self.make_object_path() + "?$select=lastModifiedDateTime")
        return self._event

    @contextmanager
    def make_path(self):
        with NamedTemporaryResource(self.handle.name) as ntr:
            with ntr.open("wb") as res:
                with self.make_stream() as s:
                    res.write(s.read())
            yield ntr.get_path()

    @contextmanager
    def make_stream(self):
        with BytesIO(self._get_body()["body"]["content"].encode()) as fp:
            yield fp

    def compute_type(self):
        return ("text/html"
                if self._get_body()["body"]["contentType"] == "html"
                else "text/plain")

    def get_size(self):
        return SingleResult(None, 'size', 1024)


class MSGraphCalendarEventHandle(Handle):
    type_label = "msgraph-calendar-event"
    resource_type = MSGraphCalendarEventResource
    eq_properties = Handle.BASE_PROPERTIES

    def __init__(self, source, path, event_subject, weblink):
        super().__init__(source, path)
        self._event_subject = event_subject
        self._weblink = weblink

    @property
    def presentation(self):
        return f'Account {self.source.handle.relative_path}'

    @property
    def presentation_name(self):
        return self._event_subject

    @property
    def presentation_url(self):
        return self._weblink

    def censor(self):
        return MSGraphCalendarEventHandle(
            self.source.censor(), self.relative_path,
            self._event_subject, self._weblink)

    def to_json_object(self):
        return dict(
            **super().to_json_object(),
            event_subject=self._event_subject,
            weblink=self._weblink,
        )

    @staticmethod
    @Handle.json_handler(type_label)
    def from_json_object(obj):
        return MSGraphCalendarEventHandle(
            Source.from_json_object(obj["source"]),
            obj["path"], obj["event_subject"], obj["weblink"])
