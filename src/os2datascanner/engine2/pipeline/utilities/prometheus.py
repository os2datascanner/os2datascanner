from prometheus_client import Summary


def prometheus_summary(*args):
    """Decorator. Records a Prometheus summary observation for every call to
    the decorated function."""
    s = Summary(*args)

    def _prometheus_summary(func):
        return s.time()(func)
    return _prometheus_summary
