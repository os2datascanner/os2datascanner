from django import template
from django.utils.translation import gettext_lazy as _

register = template.Library()


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter
def format_timespan(seconds):
    """Return a string of the two largest time units of the time span given in seconds."""

    try:
        seconds = float(seconds)
    except ValueError as e:
        print(e)
        return seconds

    time_formats = {
        "days": {
            "single": _("day"),
            "multiple": _("days"),
            "seconds": 60*60*24
        },
        "hours": {
            "single": _("hour"),
            "multiple": _("hours"),
            "seconds": 60*60
        },
        "minutes": {
            "single": _("minute"),
            "multiple": _("minutes"),
            "seconds": 60
        },
        "seconds": {
            "single": _("second"),
            "multiple": _("seconds"),
            "seconds": 1
        },
        "milliseconds": {
            "single": _("millisecond"),
            "multiple": _("milliseconds"),
            "seconds": 1/1000
        },
    }

    formatted_string = ""
    iteration = 0

    for unit in time_formats:
        format_array = time_formats[unit]
        # Only proceed if at least one corresponding unit of time is contained in the time span.
        if unit_divisor := int(seconds//format_array["seconds"]):
            # We only want the two first units which have values greater than zero.
            iteration += 1
            # Grab the remaining seconds
            seconds = seconds % format_array["seconds"]
            # Add the unit of time to the formatted string
            formatted_string += " "+_("and")+" " if iteration == 2 else ""
            formatted_string += f"{unit_divisor} " + \
                f"{format_array['single'] if unit_divisor == 1 else format_array['multiple']}"

            if iteration == 2:
                break
    return formatted_string
