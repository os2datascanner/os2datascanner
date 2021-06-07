#!/usr/bin/env python3

"""Helper commands for monitoring the OS2datascanner pipeline."""

import logging
import click
import sys

logger = logging.getLogger(__name__)

# default time(s) to wait before giving up
_SLEEPING_TIME = 3

@click.group()
def group():
    pass


@group.command()
@click.option("--wait", default=_SLEEPING_TIME, type=float,
              help="Wait up to n seconds for rabbitmq.")
def wait_for_rabbitmq(wait):
    """Check if RabbitMQ can be reached"""
    logger.debug("checking if RabbitMQ can be reached")

    import pika
    from os2datascanner.engine2.pipeline.utilities.pika import (
        PikaConnectionHolder)

    # change backoff parameters to get different timings. These settings gives a
    # constant sleep time of @base sec.
    max_tries = 5
    base = wait / max_tries
    try:
        conn = PikaConnectionHolder(
            backoff={"count":0, "fuzz":0, "ceiling": 1, "base":base,
                     "warn_after":max_tries, "max_tries":max_tries})
        con = conn.connection
        conn.clear()
        return 0

    except pika.exceptions.AMQPConnectionError:
        sys.exit(3)



if __name__ == '__main__':
    group()
