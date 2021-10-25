import json
import pika
import time
import signal
import threading
import traceback
from sortedcontainers import SortedList

from ...utilities.backoff import run_with_backoff
from ....utils.system_utilities import json_utf8_decode
from os2datascanner.utils import pika_settings


def go_bang(k):
    exc_type, exc_value, exc_traceback, thread = k
    traceback.print_exception(exc_type, exc_value, exc_traceback)
    signal.raise_signal(signal.SIGKILL)


# We register an exception hook to make sure the main thread does not hang
# indefinitely should a problem arise in the rabbitmq-connection-thread.
threading.excepthook = go_bang


class PikaConnectionHolder:
    """A PikaConnectionHolder manages a blocking connection to a RabbitMQ
    server. (Like Pika itself, it is not thread safe.)"""

    def __init__(self, backoff=pika_settings.AMQP_BACKOFF_PARAMS, **kwargs):
        connection_params = {
            "host": pika_settings.AMQP_HOST,
            "port": pika_settings.AMQP_PORT,
            "virtual_host": pika_settings.AMQP_VHOST,
            "heartbeat": pika_settings.AMQP_HEARTBEAT,
        }
        connection_params.update(kwargs)
        credentials = pika.PlainCredentials(
            pika_settings.AMQP_USER, pika_settings.AMQP_PWD
        )
        self._parameters = pika.ConnectionParameters(
            credentials=credentials, **connection_params
        )
        self._connection = None
        self._channel = None
        self._backoff = backoff

    def make_connection(self):
        """Constructs a new Pika connection."""
        return pika.BlockingConnection(self._parameters)

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
        try:
            if self._channel:
                self._channel.close()
        except pika.exceptions.ChannelWrongStateError:
            pass
        finally:
            self._channel = None

        try:
            if self._connection:
                self._connection.close()
        except pika.exceptions.ConnectionWrongStateError:
            pass
        finally:
            self._connection = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_info, exc_tb):
        self.clear()


ANON_QUEUE = ""
"""The special value that indicates to RabbitMQ that the broker should assign
a randomly-generated unique name to a queue. (When used to identify a queue to
read from, this value refers to the last randomly-generated queue name for the
given channel.)"""


class PikaPipelineRunner(PikaConnectionHolder):
    def __init__(self, *,
                 prefetch_count=1, read=None, write=None, **kwargs):
        super().__init__(**kwargs)
        self._read = set() if read is None else set(read)
        self._write = set() if write is None else set(write)
        self._prefetch_count = prefetch_count

    def make_channel(self):
        """As PikaConnectionHolder.make_channel, but automatically declares all
        of the read and write queues used by this pipeline stage."""
        channel = super().make_channel()
        channel.basic_qos(prefetch_count=self._prefetch_count)
        for q in self._read.union(self._write):
            channel.queue_declare(
                q,
                passive=False,
                durable=True,
                exclusive=False,
                auto_delete=False)

        # RabbitMQ handles broadcast messages in a slightly convoluted way:
        # we must first declare a special "fanout" message exchange, and then
        # each client must declare a separate anonymous queue and bind it to
        # the exchange in order to receive broadcasts
        channel.exchange_declare(
            "broadcast",
            pika.spec.ExchangeType.fanout,
            passive=False,
            durable=True,
            auto_delete=False,
            internal=False)
        anon_queue = channel.queue_declare(
            ANON_QUEUE,
            passive=False,
            durable=False,
            exclusive=False,
            auto_delete=True,
            arguments={"x-max-priority": 10})
        channel.queue_bind(exchange="broadcast", queue=anon_queue.method.queue)

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
        consumer_tags.append(self.channel.basic_consume(
                ANON_QUEUE, self.handle_message_raw, exclusive=False))
        return consumer_tags

    def _basic_cancel(self, consumer_tags):
        """Cancels all of the provided consumer registrations."""
        for tag in consumer_tags:
            self.channel.basic_cancel(tag)


class RejectMessage(BaseException):
    """Implementations of PikaPipelineThread.handle_message can raise the
    RejectMessage exception to indicate that a message should be rejected. (By
    default, messages are acknowledged once handle_message is finished.)

    Rejected messages are by default re-enqueued for later execution; if
    requeue=False is passed to the constructor, though, messages will just be
    dropped.

    This exception is not intended to be handled by anything other than
    PikaPipelineThread, and is accordingly implemented as a BaseException
    rather than an Exception."""

    def __init__(self, *args, requeue=True, **kwargs):
        super().__init__(*args, **kwargs)
        self.requeue = requeue


class PikaPipelineThread(threading.Thread, PikaPipelineRunner):
    """Runs a Pika session in a background thread."""
    def __init__(self, *args, exclusive=False, **kwargs):
        super().__init__()
        PikaPipelineRunner.__init__(self, *args, **kwargs)
        self._incoming = SortedList(key=lambda e: -(e[1].priority or 0))
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

    def enqueue_reject(self, delivery_tag: int, requeue: bool = True):
        """Requests that the background thread reject the message with the
        given tag."""
        return self._enqueue("rej", delivery_tag, requeue)

    def enqueue_stop(self):
        """Requests that the background thread stop running.

        Note that the background thread is *not* a daemon thread: the host
        process will not terminate if this method is never called."""
        return self._enqueue("fin")

    def enqueue_message(self,
                        queue: str,
                        body: bytes,
                        exchange: str = "",
                        **basic_properties):
        """Requests that the background thread send a message."""
        if not isinstance(body, bytes):
            body = json.dumps(body).encode()
        return self._enqueue("msg", queue, body, exchange, basic_properties)

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
            if rv and self._live:
                return self._incoming.pop(0)
            else:
                return None, None, None

    def handle_message(self, routing_key, body):
        """Handles an AMQP message by yielding zero or more (queue name,
        JSON-serialisable object) pairs to be sent as new messages.

        The default implementation of this method does nothing."""
        yield from []

    def handle_message_raw(self, channel, method, properties, body):
        """(Background thread.) Collects a message and stores it for later
        retrieval by the main thread."""
        with self._condition:
            self._incoming.add((method, properties, body,))
            self._condition.notify()

    def run(self):  # noqa: CCR001, too high cognitive complexity
        """(Background thread.) Runs a loop that processes enqueued actions
        from, and collects new messages for, the main thread.

        (Note that it *is* possible, if you're careful, to call this function
        directly in order to execute a list of enqueued actions on the current
        thread.)"""
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
                        head = self._outgoing.pop(0)
                        label = head[0]
                        if label == "msg":
                            queue, body, exchange, properties = head[1:]
                            self.channel.basic_publish(
                                    exchange=exchange,
                                    routing_key=queue,
                                    properties=pika.BasicProperties(
                                            delivery_mode=2,
                                            **properties),
                                    body=body)
                        elif label == "ack":
                            delivery_tag = head[1]
                            self.channel.basic_ack(delivery_tag)
                        elif label == "rej":
                            delivery_tag, requeue = head[1:]
                            self.channel.basic_reject(
                                    delivery_tag, requeue=requeue)
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

    def run_consumer(self):  # noqa: CCR001, E501 too high cognitive complexity
        """Receives messages from the registered input queues, dispatches them
        to the handle_message function, and generates new output messages. All
        Pika API calls are performed by the background thread."""

        if threading.main_thread() != threading.current_thread():
            raise ValueError(
                    "only the main thread can call PikaPipelineThread."
                    "run_consumer(); to execute a queue of Pika actions from"
                    " an arbitrary thread, call PikaPipelineThread.run()"
                    " instead")

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
                if method == properties == body is None:
                    continue
                try:
                    for routing_key, message in self.handle_message(
                            method.routing_key, json_utf8_decode(body)):
                        self.enqueue_message(routing_key, message)
                    self.enqueue_ack(method.delivery_tag)
                except RejectMessage as ex:
                    self.enqueue_reject(method.delivery_tag, requeue=ex.requeue)
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
