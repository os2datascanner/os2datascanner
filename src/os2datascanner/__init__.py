from . import engine2  # noqa
from . import utils  # noqa
import logging
import structlog
import os

from structlog.stdlib import LoggerFactory

__version__ = "3.15.0"
__commit__ = os.getenv("COMMIT_SHA", "")
__tag__ = os.getenv("COMMIT_TAG", __version__)
__branch__ = os.getenv("CURRENT_BRANCH", "main")

# prevent default configuration, if users do not set one specifically
logging.getLogger(__name__).addHandler(logging.NullHandler())
# This allows users of this "library" to disable all logging, simply by
# logging.getLogger('os2datascanner').propagate = False

logging.getLogger("pika").setLevel(logging.WARNING)

# prevent structlog from emitting all log-statements if no loglevel is set.
structlog.configure(logger_factory=LoggerFactory())
