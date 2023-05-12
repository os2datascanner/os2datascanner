import gzip
import json
from typing import Optional
import logging
from pathlib import Path
from datetime import datetime
from functools import cached_property

import os2datascanner.engine2.settings as settings
from ...model.core import Resource
from ...utilities.datetime import make_datetime_aware
from ...utilities.cryptography import make_secret_box
from ..types import OutputType
from ..registry import convert


logger = logging.getLogger(__name__)


def lastmod(p: Path) -> Optional[datetime]:
    return make_datetime_aware(
            datetime.fromtimestamp(p.stat().st_mtime), local=True)


class CacheManager:
    """A CacheManager maintains a disk cache of representations for a given
    Resource.

    Cached representations are stored in a folder named for the hash of the
    Resource's crunched Handle, and are encrypted using the unhashed version as
    a password. This ensures that you can only decrypt a cached representation
    if you already know what it is and where it is (at which point you could
    just retrieve it yourself anyway.)"""
    def __init__(self, resource: Resource):
        self._resource = resource

    def _get_resource_lm(self) -> Optional[datetime]:
        """Retrieves the date of last modification from the underlying
        Resource (or, if it doesn't implement that function, then from
        whichever of its parents do)."""
        resource = self._resource
        while resource:
            if hasattr(resource, "get_last_modified"):
                return resource.get_last_modified()
            else:
                handle = resource.handle
                if handle.source.handle:
                    resource = handle.source.handle.follow(resource._sm)
                else:
                    resource = None
        return None

    @cached_property
    def handle(self):
        return self._resource.handle.censor()

    @cached_property
    def crunched(self):
        return self.handle.crunch()

    @cached_property
    def cache_dir(self) -> Path:
        cd_s = settings.conversions["cache"]["directory"]
        if cd_s:
            hashed_crunch = self.handle.censor().crunch(hash=True)

            cd = Path(cd_s) / hashed_crunch
            cd.mkdir(parents=True, exist_ok=True)
            return cd
        else:
            return None

    @cached_property
    def _box(self):
        return make_secret_box(self.crunched)

    class Representation:
        def __init__(self, parent: "CacheManager", output_type: OutputType):
            self._parent = parent
            self._output_type = output_type

        @property
        def path(self):
            if (cd := self._parent.cache_dir) is not None:
                return cd / self._output_type.value
            else:
                return None

        @property
        def cache_exists(self) -> bool:
            cf = self.path
            lm = make_datetime_aware(self._parent._get_resource_lm())
            return cf and cf.exists() and (not lm or lastmod(cf) >= lm)

        def create(self, mime_override: str = None):
            """Returns a representation corresponding to the output type of
            this Representation.

            If the system's configuration permits it, the representation will
            be saved to disk and reused by future calls to Representation.get.
            Otherwise, it'll just be returned."""
            output_type = self._output_type
            cf = self.path

            representation = convert(
                    self._parent._resource, output_type, mime_override)
            if cf:
                logger.debug(
                        f"saving cache for {self._parent.handle},"
                        f" type {output_type.value!r}")
                raw_json = json.dumps(
                        output_type.encode_json_object(representation))
                compressed = gzip.compress(raw_json.encode())
                with cf.open("wb") as fp:
                    fp.write(self._parent._box.encrypt(compressed))
            return representation

        def get(self, *, create=False, mime_override: str = None):
            """Returns a representation corresponding to the output type of
            this Representation, if one is available. If the create flag is
            set, then the representation will be produced by the create method
            if necessary."""
            output_type = self._output_type
            cf = self.path

            if not self.cache_exists:
                logger.debug(
                        f"cache for {self._parent.handle}, type"
                        f" {output_type.value!r} does not exist or"
                        " is stale")
                return self.create(mime_override) if create else None
            else:
                logger.debug(
                        f"returning cache for {self._parent.handle}, type"
                        f" {output_type.value!r}")
                with cf.open("rb") as fp:
                    unencrypted = self._parent._box.decrypt(fp.read())
                    decompressed = gzip.decompress(unencrypted)
                    raw_json = json.loads(decompressed.decode())
                    return output_type.decode_json_object(raw_json)

    def representation(self, output_type: OutputType):
        return self.Representation(self, output_type)


__all__ = (
        "CacheManager",
)
