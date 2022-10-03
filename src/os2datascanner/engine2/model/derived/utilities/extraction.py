"""Utilities for extraction based on configuration dictionaries."""


def should_skip_images(configuration: dict) -> bool:
    """Checks if the 'image/*' mime type is in 'skip_mime_types' for a
    configuration dict."""

    if configuration and configuration["skip_mime_types"]:
        return "image/*" in configuration["skip_mime_types"]

    return False
