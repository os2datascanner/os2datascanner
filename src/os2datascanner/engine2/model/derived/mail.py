from io import BytesIO
import os.path
import email
from contextlib import contextmanager

from ..core import Source, Handle, FileResource
from ..utilities.mail import decode_encoded_words
from .derived import DerivedSource


def _parts_are_text_body(parts):
    return (len(parts) == 2
            and parts[0].get_content_type() == "text/plain"
            and parts[1].get_content_type() == "text/html")


@Source.mime_handler("message/rfc822")
class MailSource(DerivedSource):
    type_label = "mail"

    def _generate_state(self, sm):
        with self.handle.follow(sm).make_stream() as fp:
            yield email.message_from_bytes(
                    fp.read(), policy=email.policy.default)

    def handles(self, sm):
        def _process_message(path, part):
            ct, st = part.get_content_maintype(), part.get_content_subtype()
            if ct == "multipart":
                parts = part.get_payload()
                # XXX: this is a slightly hacky implementation of multipart/
                # alternative, but we don't know what task we're being asked to
                # perform and so we can't do any better
                if st == "alternative" and _parts_are_text_body(parts):
                    yield from _process_message(path + ["1"], parts[1])
                else:
                    for idx, part in enumerate(parts):
                        yield from _process_message(path + [str(idx)], part)
            else:
                filename = part.get_filename()
                full_path = "/".join(path + [filename or ''])
                yield MailPartHandle(self, full_path, part.get_content_type())
        yield from _process_message([], sm.open(self))


class MailPartResource(FileResource):
    def __init__(self, handle, sm):
        super().__init__(handle, sm)
        self._fragment = None

    def check(self) -> bool:
        # XXX: this implementation probably never returns True (_get_fragment
        # is likely to raise an exception before it returns None)
        return self._get_fragment() is not None

    def _get_fragment(self):
        if not self._fragment:
            where = self._get_cookie()
            path = self.handle.relative_path.split("/")[:-1]
            while path:
                next_idx, path = int(path[0]), path[1:]
                where = where.get_payload()[next_idx]
            self._fragment = where
        return self._fragment

    def get_last_modified(self):
        return self.handle.source.handle.follow(self._sm).get_last_modified()

    def get_size(self):
        with self.make_stream() as s:
            initial = s.seek(0, 1)
            try:
                s.seek(0, 2)
                return s.tell()
            finally:
                s.seek(initial, 0)

    @contextmanager
    def make_stream(self):
        yield BytesIO(self._get_fragment().get_payload(decode=True))


class MailPartHandle(Handle):
    type_label = "mail-part"
    resource_type = MailPartResource

    def __init__(self, source, path, mime):
        super().__init__(source, path)
        self._mime = mime

    @property
    def _path_name(self):
        return os.path.basename(self.relative_path)

    @property
    def presentation_name(self):
        container = self.source.handle.presentation_name
        if (name := self._path_name):
            # This is a named attachment
            return (f"attachment \"{decode_encoded_words(name)}\""
                    f" in {container}")
        else:
            # This is a message body. Use its subject
            return container

    @property
    def sort_key(self):
        return self.source.handle.sort_key

    @property
    def presentation_place(self):
        return self.source.handle.presentation_place

    def __str__(self):
        return (f"{self.presentation_name} (attached"
                f" to {self.presentation_place})")

    def censor(self):
        return MailPartHandle(
                self.source.censor(), self.relative_path, self._mime)

    def guess_type(self):
        if self._mime != "application/octet-stream":
            return self._mime
        else:
            # If this mail part has a completely generic type, then see if our
            # filename-based detection can manage anything better
            return super().guess_type()

    def to_json_object(self):
        return dict(**super().to_json_object(), mime=self._mime)

    @staticmethod
    @Handle.json_handler(type_label)
    def from_json_object(obj):
        return MailPartHandle(
            Source.from_json_object(obj["source"]), obj["path"], obj["mime"])
