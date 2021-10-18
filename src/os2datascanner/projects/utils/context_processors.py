from os2datascanner import __version__

"""Custom context processors

context processor has a simple interface: It’s a Python function that takes one
argument, an HttpRequest object, and returns a dictionary that gets added to the
template context.

The 'context_processors' option in the TEMPLATES setting should point to the custom
context processor.

https://docs.djangoproject.com/en/3.2/ref/templates/api/#writing-your-own-context-processors

"""


def version(request):
    return {
        "version": __version__
    }
