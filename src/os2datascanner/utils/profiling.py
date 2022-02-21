profile = None


def enable_profiling():
    """Switches cProfile profiling on. If it was already on, then the existing
    profile instance will be stopped and discarded. Returns the new profile
    instance."""

    import cProfile  # noqa

    global profile
    if profile:
        profile.disable()
        del profile
    profile = cProfile.Profile()
    profile.enable()

    return profile


def disable_profiling():
    """Switches cProfile profiling off and discards the existing profile
    instance. Returns the former profile instance for inspection and printing,
    if there is one, or None if profiling was not switched on."""
    global profile
    try:
        if profile:
            profile.disable()
        return profile
    finally:
        profile = None


def get_profile():
    """Returns the cProfile profile instance, or None if profiling was never
    switched on."""
    return profile


def print_stats(*args, silent=False, **kwargs):
    """Prints the statistics of the cProfile profile instance to standard
    output, as though by the Profile.print_stats method. If profiling was never
    switched on, and the silent flag is not set, prints a short diagnostic to
    standard output instead."""
    if profile:
        profile.print_stats(*args, **kwargs)
    elif not silent:
        print("not profiling")


__all__ = (
        "enable_profiling", "disable_profiling", "get_profile", "print_stats",)
