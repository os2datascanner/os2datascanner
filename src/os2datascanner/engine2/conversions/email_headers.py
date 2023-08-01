import email

from .types import OutputType
from .registry import conversion


@conversion(OutputType.EmailHeaders,
            "message/rfc822")
def headers_processor(r, **kwargs):
    with r.make_stream() as fp:
        message = email.message_from_binary_file(
                fp, policy=email.policy.default)
    return dict((k.lower(), v) for k, v in message.items())
