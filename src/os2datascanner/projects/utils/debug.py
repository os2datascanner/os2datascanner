#!/usr/bin/env python3

import ipaddress


def get_client_ip(request):
    """Get the clients IP address"""

    # XXX: curl -H "X-Forwarded-For: 1.2.3.4" localhost:8020 will give the IP 1.2.3.4
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


def debug_toolbar_callback(request):
    """Enable the debug toolbar if the host-ip is private"""

    # https://docs.djangoproject.com/en/3.2/ref/request-response/
    ip = ipaddress.ip_address(get_client_ip(request))
    return ip.is_private
