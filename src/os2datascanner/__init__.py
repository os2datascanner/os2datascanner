from . import engine2  # noqa
from . import utils  # noqa
import logging
import structlog
from structlog.stdlib import LoggerFactory

__version__ = "3.14.2"

# prevent default configuration, if users do not set one specifically
logging.getLogger(__name__).addHandler(logging.NullHandler())
# This allows users of this "library" to disable all logging, simply by
# logging.getLogger('os2datascanner').propagate = False

logging.getLogger("pika").setLevel(logging.WARNING)

# prevent structlog from emitting all log-statements if no loglevel is set.
structlog.configure(logger_factory=LoggerFactory())
