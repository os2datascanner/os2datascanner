from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def param_replace(context, **kwargs):
    """
    Return encoded URL parameters that are the same as the current
    request's parameters, only with the specified GET parameters added or changed.

    It also removes any empty parameters to keep things neat,
    so you can remove a param by setting it to ``""``.

    For example, if you're on the page ``/things/?with_frosting=true&page=5``,
    then

    <a href="/things/?{% param_replace page=3 %}">Page 3</a>

    would expand to

    <a href="/things/?with_frosting=true&page=3">Page 3</a>
    """
    d = context['request'].GET.copy()
    for k, v in kwargs.items():
        d[k] = v
    for key in [k for k, v in d.items() if not v]:
        del d[key]
    return d.urlencode()


@register.simple_tag
def match_interval(document_reports, page_obj, paginate_by):
    """Used for displaying which matches are being shown."""
    curr_page = int(page_obj.number)
    pag_by = int(paginate_by)
    first_match = pag_by * curr_page - (pag_by - 1)
    last_match = first_match + document_reports.count() - 1
    return f"{first_match} - {last_match}"
