class ReentrableSection:
    """
        Provides access to a generic wrapper/decorator, that can be used to suppress
        signals. F.e. useful for import jobs, where we don't want to trigger signals for
        each object that is to be deleted.
    """

    def __init__(self):
        self._entry_count = 0

    @property
    def count(self) -> int:
        return self._entry_count

    def wrap(self, func):
        def _wrapper(*args, **kwargs):
            with self:
                return func(*args, **kwargs)
        return _wrapper

    def __bool__(self) -> bool:
        return self.count != 0

    def __enter__(self):
        self._entry_count += 1

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._entry_count -= 1


suppress_signals = ReentrableSection()
