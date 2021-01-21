from abc import ABC, abstractmethod
from sys import stderr
import json
import pika

from ...utilities.backoff import run_with_backoff
from ....utils.system_utilities import json_utf8_decode
from os2datascanner.utils import pika_settings


class PikaConnectionHolder(ABC):
    """A PikaConnectionHolder manages a blocking connection to a RabbitMQ
    server. (Like Pika itself, it is not thread safe.)"""

    def __init__(self, **kwargs):
        credentials = pika.PlainCredentials(pika_settings.AMQP_USER,
                                            pika_settings.AMQP_PWD)
        self._parameters = pika.ConnectionParameters(credentials=credentials,
                                                     host=pika_settings.AMQP_HOST,
                                                     **kwargs)
        self._connection = None
        self._channel = None

    def make_connection(self):
        """Constructs a new Pika connection."""
        conn_string_tpl = '{0}://{1}:{2}@{3}:{4}/{5}?heartbeat=6000'
        conn_string = conn_string_tpl.format(pika_settings.AMQP_SCHEME, 
                                             pika_settings.AMQP_USER, 
                                             pika_settings.AMQP_PWD, 
                                             pika_settings.AMQP_HOST,
                                             pika_settings.AMQP_PORT,
                                             pika_settings.AMQP_VHOST.lstrip('/'))
        params = pika.URLParameters(conn_string)
        return pika.BlockingConnection(params)

    @property
    def connection(self):
        """Returns the managed Pika connection, creating one if necessary."""
        if not self._connection:
            self._connection, _ = run_with_backoff(
                self.make_connection,
                pika.exceptions.AMQPConnectionError,
                **pika_settings.AMQP_BACKOFF_PARAMS,
            )
        return self._connection

    def make_channel(self):
        """Constructs a new Pika channel."""
        return self.connection.channel()

    @property
    def channel(self):
        """Returns the managed Pika channel, creating one (and a backing
        connection) if necessary."""
        if not self._channel:
            self._channel = self.make_channel()
        return self._channel

    def clear(self):
        """Closes the managed Pika connection, if there is one."""
        if self._connection:
            try:
                self._connection.close()
            except pika.exceptions.ConnectionWrongStateError:
                pass
        self._channel = None
        self._connection = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_info, exc_tb):
        self.clear()


RECOVERABLE_PIKA_ERRORS = (
        pika.exceptions.StreamLostError,
        pika.exceptions.ChannelWrongStateError,
        pika.exceptions.ConnectionWrongStateError)
"""The exceptions that PikaPipelineRunner should treat as transient faults and
silently consume."""


class PikaPipelineRunner(PikaConnectionHolder):
    def __init__(self, *,
            read=set(), write=set(), source_manager=None, **kwargs):
        super().__init__(**kwargs)
        self._read = set(read)
        self._write = set(write)
        self._pending = []

        self.source_manager = source_manager

    def make_channel(self):
        """As PikaConnectionHolder.make_channel, but automatically declares all
        of the read and write queues used by this pipeline stage."""
        channel = super().make_channel()
        channel.basic_qos(prefetch_count=1)
        for q in self._read.union(self._write):
            channel.queue_declare(q, passive=False,
                    durable=True, exclusive=False, auto_delete=False)
        return channel

    @abstractmethod
    def handle_message(self, message_body, *, channel=None):
        """Responds to the given message by yielding zero or more (queue name,
        JSON-serialisable object) pairs to be sent as new messages."""

    def dispatch_pending(self, *, expected: int):
        """Sends all pending messages.

        This method does not attempt to handle Pika exceptions, but a message
        will not be removed from the pending list if an exception is raised
        while it's being processed."""
        outstanding = len(self._pending)
        if outstanding > expected:
            print(("PikaPipelineRunner.dispatch_pending:"
                    " unexpectedly long queue length {0},"
                    " dispatching").format(outstanding), file=stderr)
        while self._pending:
            self.publish_message(*self._pending[0])
            # If we got here, then basic_publish succeeded and we can safely
            # remove the message from the head of the pending queue
            self._pending = self._pending[1:]

    def publish_message(self, routing_key, message):
        self.channel.basic_publish(
                exchange='',
                routing_key=routing_key,
                body=json.dumps(message).encode())

    def run_consumer(self):
        """Runs the Pika channel consumer loop in another loop. Transient
        faults in the Pika loop are silently handled without dropping any
        messages."""

        def _queue_callback(channel, method, properties, body):
            """Handles an AMQP message by calling the handle_message function
            and sending everything that it yields as a new message.

            If a transient fault is produced when sending a message (for
            example, if handle_message takes too long and the underlying Pika
            connection is closed), then this function will continue to collect
            yielded messages and will schedule them to be sent when the
            connection is reopened."""
            channel.basic_ack(method.delivery_tag)
            self.dispatch_pending(expected=0)
            decoded_body = json_utf8_decode(body)
            if decoded_body:
                failed = False
                for routing_key, message in self.handle_message(
                        decoded_body, channel=method.routing_key):
                    # Try to dispatch messages as soon as they're generated,
                    # but store them for later if the connection is dropped
                    self._pending.append((routing_key, message))
                    if not failed:
                        try:
                            self.dispatch_pending(expected=1)
                        except RECOVERABLE_PIKA_ERRORS:
                            failed = True

        while True:
            consumer_tags = []
            try:
                for queue in self._read:
                    consumer_tags.append(
                            self.channel.basic_consume(queue, _queue_callback))
                self.dispatch_pending(expected=0)
                self.channel.start_consuming()
            except RECOVERABLE_PIKA_ERRORS:
                # Flush the channel and connection and continue the loop
                self._channel = None
                self._connection = None
                pass
            except:
                for tag in consumer_tags:
                    self.channel.basic_cancel(tag)
                self.channel.stop_consuming()
                raise


class PikaPipelineSender(PikaPipelineRunner):
    def handle_message(self, message_body, *, channel=None):
        yield from []
