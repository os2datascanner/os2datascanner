import os
import re
import json
import signal
from datetime import datetime
from dateutil import tz
import tempfile
import subprocess

from os2datascanner.engine2.conversions.types import DATE_FORMAT


def json_utf8_decode(body):
    try:
        body = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    return body


fixup = re.compile(r"(?P<s>[+-])(?P<h>\d{2}):(?P<m>\d{2})$")
"""Matches ISO 8601 timezone specifiers ("+0000", "-04:00", etc.) at the end of
a timestamp string. Note that this does not match the special specifier "Z",
which is instead given special treatment in parse_isoformat_timestamp."""


def parse_isoformat_timestamp(dt):
    """Parses a string produced by the datetime.isoformat() function back into
    a datetime.datetime, in the process working around a bug in Python versions
    prior to 3.7."""
    # The "%z" str[fp]time format specifier, which is supposed to handle
    # ISO 8601-style time zone specifiers ("Z", "+0200", "-05:30"), doesn't
    # understand colons until Python 3.7. Groan. Work around that by rebuilding
    # the time zone into a supported, colon-less form
    if dt.endswith("Z"):
        dt = dt[:-1] + "+0000"
    match = fixup.search(dt)
    if match:
        replacement = match.group("s") + match.group("h") + match.group("m")
        s, e = match.span()
        dt = dt[:s] + replacement + dt[e:]
    try:
        return datetime.strptime(dt, DATE_FORMAT)
    except ValueError:
        return None


def time_now() -> datetime:
    """Returns the current time in the system timezone with second precision.
    (This is the correct way to get the current time for all purposes in
    OS2datascanner.)"""
    return datetime.now().replace(tzinfo=tz.gettz(), microsecond=0)


def run_custom(
        args,
        # Arguments from subprocess.run not present in the Popen constructor
        input=None,
        timeout=None,
        check=False,
        # Our own arguments
        kill_group=False,
        isolate_tmp=False,
        **kwargs):
    """As subprocess.run, but with the following extra keyword arguments:

    * kill_group - if True, runs the subprocess in a new process group; in the
                   event of a timeout or error, the group rather than the
                   individual process will be killed
    * isolate_tmp - if True, runs the subprocess with an environment in which
                    $TMP, $TMPDIR and $TEMP all point to a freshly-created
                    temporary folder that will be deleted at process exit"""

    def _setpgrp(next=None):
        def __setpgrp():
            # Move this process into a process group whose ID is identical to
            # this process's PID (yes, this really is a single function call
            # with no arguments)
            os.setpgrp()
            if next:
                next()
        return __setpgrp
    if kill_group:
        kwargs["preexec_fn"] = _setpgrp(kwargs.get("preexec_fn"))

    temp_dir = None
    if isolate_tmp:
        temp_dir = tempfile.TemporaryDirectory()
        temp_path = temp_dir.name
        kwargs["env"] = kwargs.get("env", os.environ) | dict(
                TMP=temp_path, TMPDIR=temp_path, TEMP=temp_path)

    out, err = None, None
    with subprocess.Popen(args, **kwargs) as process:
        try:
            out, err = process.communicate(input, timeout)
        except subprocess.TimeoutExpired:
            (os.killpg(process.pid, signal.SIGKILL)
                    if kill_group else process.kill())
            # We only need to take responsibility for our immediate child
            # process -- init will reap anything else
            o2, e2 = process.communicate()
            raise subprocess.TimeoutExpired(
                    args, timeout, output=o2, stderr=e2)
        except Exception:
            (os.killpg(process.pid, signal.SIGKILL)
                    if kill_group else process.kill())
            raise
        finally:
            if temp_dir:
                temp_dir.cleanup()

    cp = subprocess.CompletedProcess(
            args=args,
            returncode=process.poll(),
            stdout=out, stderr=err)
    if check:
        cp.check_returncode()
    return cp
