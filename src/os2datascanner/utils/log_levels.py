import logging


logging.addLevelName(2, "TRACE")
logging.TRACE = 2


log_levels = {
    'critical': logging.CRITICAL,
    'error': logging.ERROR,
    'warn': logging.WARNING,
    'warning': logging.WARNING,
    'info': logging.INFO,
    'debug': logging.DEBUG,
    'trace': logging.TRACE
}
