"""Helper commands for monitoring the OS2datascanner pipeline."""

import socket
import sys
import time

import click
import pika

from os2datascanner.engine2.pipeline.utilities.pika import PikaConnectionHolder


_SLEEPING_TIME = 2


@click.group()
def group():
    pass


@group.command()
@click.option(
    "--wait",
    default=60,
    type=int,
    help="How long to attempt connecting to RabbitMQ",
)
def wait_for_rabbitmq(wait):
    """Check if RabbitMQ can be reached"""

    attempts = wait // _SLEEPING_TIME
    click.echo(f"Attempting to connect to RabbitMQ. Will attempt {attempts} times.")

    for i in range(1, attempts + 1):
        try:
            PikaConnectionHolder().make_connection()
        except (pika.exceptions.AMQPConnectionError, socket.gaierror):
            click.echo(f"RabbitMQ is unavailable - attempt {i}/{attempts}")
            if i < attempts:  # dont sleep after last failed attempt
                time.sleep(_SLEEPING_TIME)
        else:
            click.echo("Successfully connected to RabbitMQ!")
            break
    else:
        click.echo("Failed to connect to RabbitMQ")
        sys.exit(3)


if __name__ == "__main__":
    group()
