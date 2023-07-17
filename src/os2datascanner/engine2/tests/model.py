from os2datascanner.engine2.model.core import Source, Handle, Resource
from os2datascanner.engine2.model.derived.derived import DerivedSource


DUMMY_MIME = "application/x.os2datascanner.tests.dummy-mime"


class DummySource(Source):
    type_label = "-test-dummy"

    def __init__(self, count, *, secret):
        self._count = max(0, count)
        self._secret = secret

    def _generate_state(self, sm):
        yield dict()

    def censor(self):
        return DummySource(self._count, secret=None)

    def handles(self, sm):
        for k in range(0, self._count):
            yield DummyHandle(self, str(k))

    @staticmethod
    @Source.json_handler(type_label)
    def from_json_object(obj):
        return DummySource(obj["count"], secret=obj["secret"])

    def to_json_object(self):
        return dict(
                **super().to_json_object(),
                **{
                    "count": self._count,
                    "secret": self._secret
                })


class DummyResource(Resource):
    def check(self):
        counts = self._get_cookie()
        if self.handle not in counts:
            counts[self.handle] = 0
        counts[self.handle] += 1

        hint = self.handle.hint("exists", True)
        if hint is None:
            raise OSError("Transient error, try again later")
        else:
            return hint

    def compute_type(self):
        return DUMMY_MIME


@Handle.stock_json_handler("-test-dummy")
class DummyHandle(Handle):
    type_label = "-test-dummy"
    resource_type = DummyResource

    def censor(self):
        return DummyHandle(self.source.censor(), self.relative_path)

    @property
    def presentation_name(self):
        return f"dummy no. {self.relative_path}"

    @property
    def presentation_place(self):
        return "dreamland"

    def guess_type(self):
        return DUMMY_MIME


@Source.mime_handler(DUMMY_MIME)
class DummySubsource(DerivedSource):
    type_label = "-test-dummy-sub"

    def _generate_state(self, sm):
        yield self.handle.follow(sm)

    def handles(self, sm):
        for k in range(0, self.handle.source._count):
            yield DummySubhandle(self, str(k))


class DummySubresource(Resource):
    def check(self):
        self._get_cookie().check()


@Handle.stock_json_handler("-test-dummy-sub")
class DummySubhandle(Handle):
    type_label = "-test-dummy-sub"
    resource_type = DummySubresource

    @property
    def presentation_name(self):
        return f"sub-dummy no. {self.relative_path}"

    @property
    def presentation_place(self):
        return str(self.source.handle)

    def censor(self):
        return DummySubhandle(self.source.censor(), self.relative_path)
