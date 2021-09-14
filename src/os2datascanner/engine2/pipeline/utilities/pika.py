from abc import ABC, abstractmethod
from sys import stderr
import json
import pika
import time
import signal
import threading

from ...utilities.backoff import run_with_backoff
from ....utils.system_utilities import json_utf8_decode
from os2datascanner.utils import pika_settings


class PikaConnectionHolder(ABC):
    """A PikaConnectionHolder manages a blocking connection to a RabbitMQ
    server. (Like Pika itself, it is not thread safe.)"""

    def __init__(self,
                 backoff=pika_settings.AMQP_BACKOFF_PARAMS,
                 **kwargs):
        credentials = pika.PlainCredentials(pika_settings.AMQP_USER,
                                            pika_settings.AMQP_PWD)
        self._parameters = pika.ConnectionParameters(credentials=credentials,
                                                     host=pika_settings.AMQP_HOST,
                                                     **kwargs)
        self._connection = None
        self._channel = None
        self._backoff = backoff

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
                **self._backoff,
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


class PikaPipelineRunner(PikaConnectionHolder):
    def __init__(self, *,
            read=set(), write=set(), **kwargs):
        super().__init__(**kwargs)
        self._read = set(read)
        self._write = set(write)

    def make_channel(self):
        """As PikaConnectionHolder.make_channel, but automatically declares all
        of the read and write queues used by this pipeline stage."""
        channel = super().make_channel()
        channel.basic_qos(prefetch_count=1)
        for q in self._read.union(self._write):
            channel.queue_declare(q, passive=False,
                    durable=True, exclusive=False, auto_delete=False)
        return channel

    def handle_message_raw(self, channel, method, properties, body):
        """Handles an AMQP message.

        The default implementation of this method acknowledges the message and
        otherwise does nothing."""
        self.channel.basic_ack(method.delivery_tag)

    def _basic_consume(self, *, exclusive=False):
        """Registers this PikaPipelineRunner to receive messages directed to
        its read queues. (Be sure to call _basic_cancel with the return value
        of this function to cancel this registration.)"""
        consumer_tags = []
        for queue in self._read:
            consumer_tags.append(self.channel.basic_consume(
                    queue, self.handle_message_raw,
                    exclusive=exclusive))
        return consumer_tags

    def _basic_cancel(self, consumer_tags):
        """Cancels all of the provided consumer registrations."""
        for tag in consumer_tags:
            self.channel.basic_cancel(tag)


class PikaPipelineThread(threading.Thread, PikaPipelineRunner):
    """Runs a Pika session in a background thread."""
    def __init__(self, *args, exclusive=False, **kwargs):
        super().__init__()
        PikaPipelineRunner.__init__(self, *args, **kwargs)
        self._incoming = []
        self._outgoing = []
        self._live = None
        self._condition = threading.Condition()
        self._exclusive = exclusive

        self._shutdown_exception = None

    def _enqueue(self, label: str, *args):
        """Enqueues a request for the background thread.

        Requests consist of a label that specifies the desired action and a
        number of action-specific parameters. This is an implementation detail:
        clients should use the enqueue_* methods instead."""
        with self._condition:
            self._outgoing.append((label, *args))

    def enqueue_ack(self, delivery_tag: int):
        """Requests that the background thread acknowledge receipt of the
        message with the given tag."""
        return self._enqueue("ack", delivery_tag)

    def enqueue_stop(self):
        """Requests that the background thread stop running.

        Note that the background thread is *not* a daemon thread: the host
        process will not terminate if this method is never called."""
        return self._enqueue("fin")

    def enqueue_message(self, queue: str, body: bytes):
        """Requests that the background thread send a message."""
        return self._enqueue("msg", queue, body)

    def await_message(self, timeout: float = None):
        """Returns a message collected by the background thread; the return
        value is the (method, properties, body) 3-tuple normally returned by
        BlockingConnection.basic_get. This method will return immediately if
        the background thread isn't running; otherwise, it will block until a
        message is  available or until the given timeout elapses."""
        with self._condition:

            def waiter():
                return not self._live or len(self._incoming) > 0
            rv = self._condition.wait_for(waiter, timeout)
            if rv == True and self._live:
                head, self._incoming = self._incoming[0], self._incoming[1:]
                return head
            else:
                return (None, None, None)

    def handle_message(self, routing_key, body):
        """Handles an AMQP message by yielding zero or more (queue name,
        JSON-serialisable object) pairs to be sent as new messages.

        The default implementation of this method does nothing."""
        yield from []

    def handle_message_raw(self, channel, method, properties, body):
        """(Background thread.) Collects a message and stores it for later
        retrieval by the main thread."""
        with self._condition:
            self._incoming.append((method, properties, body,))
            self._condition.notify()

    def run(self):
        """(Background thread.) Runs a loop that processes enqueued actions
        from, and collects new messages for, the main thread."""
        with self._condition:
            self._live = True
            self._condition.notify()
        consumer_tags = self._basic_consume(exclusive=self._exclusive)
        try:
            running = True
            while running:
                with self._condition:
                    # Process all of the enqueued actions
                    while self._outgoing:
                        head, self._outgoing = (
                                self._outgoing[0], self._outgoing[1:])
                        label = head[0]
                        if label == "msg":
                            queue, body = head[1:]
                            self.channel.basic_publish(
                                    exchange='',
                                    routing_key=queue,
                                    properties=pika.BasicProperties(
                                            delivery_mode=2),
                                    body=json.dumps(body).encode())
                        elif label == "ack":
                            delivery_tag = head[1]
                            self.channel.basic_ack(delivery_tag)
                        elif label == "fin":
                            running = False
                            break

                # Dispatch any waiting timer (heartbeats) and channel (calls to
                # our handle_message_raw method) callbacks...
                self.connection.process_data_events(0)
                # ... and then sleep for a moment to avoid overburdening the
                # system
                time.sleep(0.1)
        except BaseException as ex:
            self._shutdown_exception = ex
            raise
        finally:
            self._basic_cancel(consumer_tags)
            with self._condition:
                self._live = False
                self._condition.notify()

    def run_consumer(self):
        running = True

        def _handler(signum, frame):
            nonlocal running
            running = False
            self.enqueue_stop()
        old_handler = signal.signal(signal.SIGTERM, _handler)

        self.start()
        try:
            while running and self.is_alive():
                method, properties, body = self.await_message()
                if method == properties == body == None:
                    continue
                for routing_key, message in self.handle_message(
                        method.routing_key, json_utf8_decode(body)):
                    self.enqueue_message(routing_key, message)
                self.enqueue_ack(method.delivery_tag)
        finally:
            self.enqueue_stop()
            self.join()
            signal.signal(signal.SIGTERM, old_handler)

            # Discard any requests that weren't processed (under the condition
            # lock for consistency's sake, but we are the only thread at this
            # point)
            with self._condition:
                self._incoming.clear()

        if self._shutdown_exception:
            raise Exception("Worker thread died unexpectedly") from (
                    self._shutdown_exception)
