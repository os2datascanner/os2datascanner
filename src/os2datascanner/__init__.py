from . import engine2  # noqa
from . import utils  # noqa
import logging

# prevent default configuration, if users do not set one specifically
logging.getLogger(__name__).addHandler(logging.NullHandler())
# This allows users of this "library" to disable all logging, simply by
# logging.getLogger('os2datascanner').propagate = False
