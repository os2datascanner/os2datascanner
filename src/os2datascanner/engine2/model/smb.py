from .core import Source, Handle
from .file import FilesystemResource

from os import rmdir
from regex import compile
from urllib.parse import quote, unquote, urlsplit, urlunsplit
from pathlib import Path
from tempfile import mkdtemp
from subprocess import run


def inlang(lang, s):
    """Indicates whether or not every character in a given string @s can be
    found in the string @lang."""
    return all(c in lang for c in s)


def compute_domain(unc):
    """Attempts to extract a domain name from a UNC path. Returns None when the
    server name is a simple, unqualified name or an IP address."""
    server, path = unc.replace("\\", "/").lstrip('/').split('/', maxsplit=1)
    dot_count = server.count(".")
    # Check if we can extract an authentication domain from a fully-qualified
    # server name
    if (server.startswith('[')  # IPv6 address
            or dot_count == 0  # NetBIOS name
            or (inlang("0123456789.", server)
                and dot_count == 3)):  # IPv4 address
        return None
    else:
        # The machine name is the first component, and the rest is the domain
        # name
        _, remainder = server.split(".", maxsplit=1)
        return remainder


class SMBSource(Source):
    type_label = "smb"
    eq_properties = ("_unc", "_user", "_password", "_domain",)

    def __init__(self, unc, user=None, password=None, domain=None,
                 driveletter=None):
        self._unc = unc.replace('\\', '/')
        self._user = user
        self._password = password
        self._domain = domain if domain is not None else compute_domain(unc)
        self._driveletter = driveletter

    @property
    def unc(self):
        return self._unc

    @property
    def driveletter(self):
        return self._driveletter

    def _make_optarg(self, display=True):
        optarg = ["ro"]
        if self._user:
            optarg.append('user=' + self._user)
        if self._password:
            optarg.append(
                    'password=' + (self._password if not display else "****"))
        else:
            optarg.append('guest')
        if self._domain:
            optarg.append('domain=' + self._domain)
        return ",".join(optarg)

    def _generate_state(self, sm):
        mntdir = mkdtemp()
        try:
            args = ["mount", "-t", "cifs", self._unc, mntdir, '-o']
            args.append(self._make_optarg(display=False))
            assert run(args).returncode == 0

            yield mntdir
        finally:
            try:
                assert run(["umount", mntdir]).returncode == 0
            finally:
                rmdir(mntdir)

    def censor(self):
        return SMBSource(self.unc, None, None, None, self.driveletter)

    def _close(self, mntdir):
        args = ["umount", mntdir]
        try:
            assert run(args).returncode == 0
        except Exception:
            raise
        finally:
            rmdir(mntdir)

    def handles(self, sm):
        pathlib_mntdir = Path(sm.open(self))
        for d in pathlib_mntdir.glob("**"):
            try:
                for f in d.iterdir():
                    if f.is_file():
                        yield SMBHandle(self,
                                        str(f.relative_to(pathlib_mntdir)))
            except PermissionError:
                pass

    def to_url(self):
        return make_smb_url(
                "smb", self._unc, self._user, self._domain, self._password)

    netloc_regex = compile(
        r"^(((?P<domain>\w+);)?(?P<username>\w+)(:(?P<password>\w+))?@)?(?P<unc>[\w.-]+)$")

    @staticmethod
    @Source.url_handler("smb")
    def from_url(url):
        scheme, netloc, path, _, _ = urlsplit(url.replace("\\", "/"))
        match = SMBSource.netloc_regex.match(netloc)
        if match:
            return SMBSource(
                "//" + match.group("unc") + unquote(path),
                match.group("username"), match.group("password"),
                match.group("domain"))
        else:
            return None

    def to_json_object(self):
        return dict(
            **super().to_json_object(),
            unc=self._unc,
            user=self._user,
            password=self._password,
            domain=self._domain,
            driveletter=self._driveletter,
        )

    @staticmethod
    @Source.json_handler(type_label)
    def from_json_object(obj):
        return SMBSource(
                obj["unc"], obj["user"], obj["password"], obj["domain"],
                obj["driveletter"])


@Handle.stock_json_handler("smb")
class SMBHandle(Handle):
    type_label = "smb"
    resource_type = FilesystemResource

    @property
    def presentation(self):
        return make_presentation(self)

    @property
    def presentation_url(self):
        return make_presentation_url(self)

    @property
    def sort_key(self):
        return self.presentation.removesuffix("\\")

    def censor(self):
        return SMBHandle(self.source.censor(), self.relative_path)


# Third form from https://www.iana.org/assignments/uri-schemes/prov/smb
def make_smb_url(schema, unc, user, domain, password):
    server, path = unc.replace("\\", "/").lstrip('/').split('/', maxsplit=1)
    netloc = ""
    if user:
        if domain:
            netloc += domain + ";"
        netloc += user
        if password:
            netloc += ":" + password
        netloc += "@"
    netloc += server
    return urlunsplit((schema, netloc, quote(path), None, None))


def make_presentation(self):
    p = self.source.driveletter
    if p:
        # If you have a network drive //SERVER/DRIVE with the drive letter X,
        # sometimes you want to set up a scan for a specific subfolder that
        # nonetheless uses the drive letter X ("X:\Departments\Finance", for
        # example). Checking to see if the "drive letter" already contains a
        # colon makes this work properly
        if ":" not in p:
            p += ":"
    else:
        p = self.source.unc

    if p[-1] != "/":
        p += "/"
    return (p + self.relative_path).replace("/", "\\")


def make_presentation_url(self):
    # Note that this implementation returns a Windows-friendly URL to the
    # underlying file -- i.e., one that uses the file: scheme and not smb:
    url = "file:"
    # XXX: our testing seems to indicate that drive letter URLs don't work
    # properly; we'll leave the disabled logic here for now...
    if False and self.source.driveletter:
        # Wikipedia indicates that local filesystem paths are represented
        # with an empty hostname followed by an absolute path...
        url += "///{0}:".format(self.source.driveletter)
    else:
        # ... and that remote ones are indicated with a hostname in the
        # usual place. Luckily the UNC already starts with two forward
        # slashes, so we can just paste it in here
        url += self.source.unc
    if url[-1] != "/":
        url += "/"
    return url + self.relative_path
