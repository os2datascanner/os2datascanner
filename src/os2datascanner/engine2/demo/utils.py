'''Utilities for the demo application'''
from base64 import b64encode
from urllib.parse import quote, unquote, urlsplit, urlunsplit

from os2datascanner.engine2.model.core.errors import UnknownSchemeError
from os2datascanner.engine2.model.smb import SMBSource, make_smb_url
from os2datascanner.engine2.model.smbc import SMBCSource
from os2datascanner.engine2.model.dropbox import DropboxSource
from os2datascanner.engine2.model.data import DataSource, unpack_data_url
from os2datascanner.engine2.model.file import FilesystemSource
from os2datascanner.engine2.model.http import WebSource


class DemoSourceUtility:
    '''
    Utility for Sources that extends the sources capabilities
    just for use in the demo app.
    '''

    @staticmethod
    def from_url(url):
        '''
        Takes a URL and a Source Type and converts the URL
        to a Source of the type provided if supported.
        The Source is then wrapped as a DemoSourceUtility
        and returned as such.

        Supported Types:
        - SMBCSource
        - SMBSource
        - DropboxSource
        - DataSource
        - FilesystemSource
        - WebSource
        '''

        scheme, _, _, _, _ = urlsplit(url)

        if scheme in ("smbc", "smb"):
            _, netloc, path, _, _ = urlsplit(url.replace("\\", "/"))
            mtc = SMBSource.netloc_regex.match(netloc)
            if mtc:
                if scheme == "smb":
                    return SMBSource("//" + mtc.group("unc") + unquote(path),
                                     mtc.group("username"), mtc.group("password"),
                                     mtc.group("domain"))
                if scheme == "smbc":
                    return SMBCSource("//" + mtc.group("unc") + unquote(path),
                                      mtc.group("username"), mtc.group("password"),
                                      mtc.group("domain"))

        elif scheme == "dropbox":
            _, token, _, _, _ = urlsplit(url)
            return DropboxSource(token=token)

        elif scheme == "data":
            mime, content = unpack_data_url(url)
            return DataSource(content=content, mime=mime)

        elif scheme == "file":
            _, netloc, path, _, _ = urlsplit(url)
            assert not netloc
            return FilesystemSource(unquote(path) if path else None)

        elif scheme in ("http", "https"):
            return WebSource(url, extended_hints=True)

        raise UnknownSchemeError()

    @staticmethod
    def to_url(src) -> str:
        '''
        Converts the wrapped Source to a URL.

        Supported Types:
        - SMBCSource
        - SMBSource
        - DropboxSource
        - DataSource
        - FilesystemSource
        - WebSource
        '''
        src_type = type(src)

        if src_type is SMBCSource:
            return make_smb_url(
                "smbc", src._unc, src._user, src._domain, src._password)

        if src_type is SMBSource:
            return make_smb_url(
                "smb", src._unc, src._user, src._domain, src._password)

        if src_type is DropboxSource:
            return f"dropbox://{src._token}"

        if src_type is DataSource:
            content = b64encode(src._content).decode(encoding='ascii')
            return f"data:{src._mime};base64,{content}"

        if src_type is FilesystemSource:
            return urlunsplit(('file', '', quote(str(src.path)), None, None))

        if src_type is WebSource:
            return src._url

        return None
