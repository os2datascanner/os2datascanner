_context_filters = []


def add_context_filter(func):
    """Registers a filter function for contexts. All contexts returned by the
    make_context function will be passed through this function first.

    Context filters are called in the order in which they're added."""
    _context_filters.append(func)


def make_context(match, text, func=None):
    """Returns the (optionally postprocessed) context surrounding a match."""
    if isinstance(match, tuple):
        low, high = match
    else:
        low, high = match.span()
    ctx_low, ctx_high = max(low - 50, 0), high + 50
    # Extract context, remove newlines and tabs for better representation
    match_context = " ".join(text[ctx_low:ctx_high].split())

    for f in _context_filters + ([func] if func else []):
        match_context = f(match_context)

    return {
        "offset": low,
        "context": match_context,
        "context_offset": low - ctx_low
    }
