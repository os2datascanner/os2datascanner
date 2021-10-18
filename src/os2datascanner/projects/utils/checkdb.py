import logging
import sys
import time
import pprint
from django.db import connections
from django.db.utils import OperationalError

logger = logging.getLogger(__name__)


def waitdb(wait: int = 5):
    attempt = f"0/{wait}"
    for i in range(wait):
        attempt = f"{i+1:02d}/{wait:02d}"
        try:
            connections["default"].ensure_connection()
            logger.info("{0} Connected to database.".format(attempt))
            return 0
        except OperationalError:
            if i < wait - 1:
                time.sleep(1)

    logger.error(f"{attempt}. Giving up connecting to database.")

    # dont log password
    censored = connections["default"].settings_dict
    censored.update({"password": "CENSORED"})
    logger.error(f"db settings:\n{pprint.pformat(censored)}")

    sys.exit(3)
