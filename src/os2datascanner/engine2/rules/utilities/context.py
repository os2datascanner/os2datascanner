def make_context(match, text, postprocessor=None):
    """Returns the (optionally postprocessed) context surrounding a match."""
    if isinstance(match, tuple):
        low, high = match
    else:
        low, high = match.span()
    ctx_low, ctx_high = max(low - 50, 0), high + 50
    # Extract context, remove newlines and tabs for better representation
    match_context = " ".join(text[ctx_low:ctx_high].split())

    if postprocessor:
        match_context = postprocessor(match_context)

    return {
        "offset": low,
        "context": match_context,
        "context_offset": low - ctx_low
    }
