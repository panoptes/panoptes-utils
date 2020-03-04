import re
import zmq

from .logger import logger
from .time import current_time
from .serializers import from_json
from .serializers import to_json


class PanMessaging(object):
    """Provides messaging services within a PANOPTES robotic telescope.

    Supports broadcasting messages from publishers (e.g. a POCS or
    ArduinoIO class instance) to subscribers (also typically class
    instances). The publishers and subscribers may be in the same
    process, or in separate processes. The messages all go through
    a message forwarder; this is a process which listens for messages
    from all publishers on one TCP port and forwards each message to
    all subscribers that are connected to a second TCP port.

    Do not create PanMessaging instances directly. Publishers should
    call PanMessaging.create_publisher to create an instance of
    PanMessaging, on which they can then call send_message.
    Subscribers should call PanMessaging.create_subscriber to create
    an instance of PanMessaging, on which they can then call
    receive_message.

    Messages are sent to topics, a name that can be used to allow
    a high-level partitioning of messages. A topic name may not
    include whitespace. Among the currently used topic names are:

      * PANCHAT (sent from POCS.say)
      * PAWS-CMD (sent from PAWS websockets.py)
      * POCS (sent by class POCS)
      * POCS-CMD (sent by class POCS)
      * STATUS (sent by class POCS)
      * weather (from peas/sensors.py)
      * environment (from peas/sensors.py)
      * telemetry:commands (in ArduinoIO... new)
      * camera:commands (in ArduinoIO... new)

    And some other topics are used in tests:

      * Test-Topic (test_messaging.py)
      * RUNNING (test_pocs.py)
      * POCS-CMD (test_pocs.py)

    The method receive_message will return messages from all topics;
    the caller must check the returned topic name to determine if
    the message value is of interest.

    Note: PAWS doesn't use PanMessaging, which will likely result in
    problems as we evolve PanMessaging and the set of topics.
    TODO: Figure out how to share PanMessaging with PAWS.

    The value of a message being sent may be a string (in which case it
    is wrapped in a dict(message=<value>, timestamp=<now>) or a dict,
    in which case it will be "scrubbed", i.e. the dict entries will be
    modified as necessary to so that the dict can be serialized using
    json.dumps.

    TODO Pick an encoding of strings (e.g. UTF-8) so that non-ASCII
    strings may be sent and received without corruption of the data
    or exceptions being thrown.

    ZeroMQ is used to provide the underlying pub-sub support. ZeroMQ
    supports only a very basic message format: an array of bytes.
    PanMessaging converts the provided message topic and value into
    a byte array of this format:
        <topic-name><space><serialized-value>
    """
    logger = logger

    # Topic names must consist of the characters.
    topic_name_re = re.compile('[a-zA-Z][-a-zA-Z0-9_.:]*')

    def __init__(self, **kwargs):
        """Do not call this directly."""
        # Create a new context
        self.context = zmq.Context()
        self.socket = None

    @classmethod
    def create_forwarder(cls, sub_port, pub_port, ready_fn=None, done_fn=None):
        subscriber, publisher = PanMessaging.create_forwarder_sockets(sub_port, pub_port)
        PanMessaging.run_forwarder(subscriber, publisher, ready_fn=ready_fn, done_fn=done_fn)

    @classmethod
    def create_forwarder_sockets(cls, sub_port, pub_port):
        cls.logger.info('Creating forwarder sockets for {} -> {}', sub_port, pub_port)
        subscriber = PanMessaging.create_subscriber(sub_port, bind=True, connect=False)
        publisher = PanMessaging.create_publisher(pub_port, bind=True, connect=False)
        return subscriber, publisher

    @classmethod
    def run_forwarder(cls, subscriber, publisher, ready_fn=None, done_fn=None):
        publisher.logger.info('run_forwarder')
        try:
            if ready_fn:
                ready_fn()
            publisher.logger.info('run_forwarder calling zmq.device')
            zmq.device(zmq.FORWARDER, subscriber.socket, publisher.socket)
        except KeyboardInterrupt:
            pass
        except Exception as e:
            publisher.logger.warning(e)
            publisher.logger.warning("bringing down zmq device")
        finally:
            publisher.logger.info('run_forwarder closing publisher and subscriber')
            publisher.close()
            subscriber.close()
            if done_fn:
                done_fn()

    @classmethod
    def create_publisher(cls, port, bind=False, host='localhost', connect=True):
        """ Create a publisher

        Args:
            port (int): The port (on localhost) to bind to.

        Returns:
            A ZMQ PUB socket
        """
        obj = cls()

        obj.logger.debug('Creating zmq message publisher.')

        socket = obj.context.socket(zmq.PUB)

        if bind:
            obj.logger.debug(f'Binding publisher to port {port}')
            socket.bind(f'tcp://*:{port}')
        elif connect:
            obj.logger.debug(f'Binding publisher to tcp://{host}:{port}')
            socket.connect(f'tcp://{host}:{port}')

        obj.socket = socket

        return obj

    @classmethod
    def create_subscriber(cls, port, topic='', host='localhost', bind=False, connect=True):
        """ Create a listener

        Args:
            port (int):         The port (on localhost) to bind to.
            topic (str):      Which topic or topic prefix to subscribe to.

        """
        obj = cls()
        obj.logger.debug("Creating subscriber. Port: {} \tTopic: {}".format(port, topic))

        socket = obj.context.socket(zmq.SUB)

        if bind:
            try:
                socket.bind(f'tcp://*:{port}')
            except zmq.error.ZMQError:
                obj.logger.debug('Problem binding port {}'.format(port))
        elif connect:
            obj.logger.debug(f'Connecting subscriber to tcp://{host}:{port}')
            socket.connect(f'tcp://{host}:{port}')

        socket.setsockopt_string(zmq.SUBSCRIBE, topic)

        obj.socket = socket

        return obj

    def send_message(self, topic, message):
        """ Responsible for actually sending message across a topic

        Args:
            topic(str):   Name of topic to send on. The name must
                match topic_name_re.
            message:   Message to be sent (a string or a dict).
        """
        if not isinstance(topic, str):
            raise ValueError('Topic name must be a string')
        elif not self.topic_name_re.fullmatch(topic):
            raise ValueError('Topic name ("{}") is not valid'.format(topic))

        if topic == 'PANCHAT':
            self.logger.info(f"{topic} {message}")

        if isinstance(message, str):
            message = to_json({
                "message": message,
                "timestamp": current_time(pretty=True),
            })
        elif isinstance(message, dict):
            message = to_json(message)
        else:
            raise ValueError('Message value must be a string or dict')

        # Build the full message with topic
        full_message = f'{topic} {message}'

        # Send the message
        # self.socket.send_string(full_message, flags=zmq.NOBLOCK)
        self.socket.send_string(full_message)

    def receive_message(self, blocking=True, flags=0, timeout_ms=0):
        """Receive a message

        Receives a message for the current subscriber. Blocks by default, pass
        `flags=zmq.NOBLOCK` for non-blocking.

        Args:
            blocking (bool, optional): If True, blocks until message
                received or timeout__ms elapsed (if timeout_ms > 0).
            flag (int, optional): Any valid recv flag, e.g. zmq.NOBLOCK
            timeout_ms (int, optional): Time in milliseconds to wait for
                a message to arrive. Only applies if blocking is True.

        Returns:
            tuple(str, dict): Tuple containing the topic and a dict
        """
        topic = None
        msg_obj = None
        if not blocking:
            flags = flags | zmq.NOBLOCK
        elif timeout_ms > 0:
            # Wait until a message is available or the timeout expires.
            # TODO(jamessynge): Remove flags=..., confirm that works with
            # the default flags value of zmq.POLLIN.
            self.socket.poll(timeout=timeout_ms, flags=(zmq.POLLIN | zmq.POLLOUT))
            # Don't block at this point, because we will have waited as long
            # as necessary.
            flags = flags | zmq.NOBLOCK

        try:
            # Ugh. So ugly with the strings.
            message = self.socket.recv_string(flags=flags)
        except Exception as e:
            self.logger.warning(f'error in receive_message: {e!r}')
        else:
            topic, msg = message.split(' ', maxsplit=1)
            try:
                msg_obj = from_json(msg)
            except Exception as e:
                self.logger.warning(f'Error parsing message: {msg} {e!r}')

        return topic, msg_obj

    def close(self):
        """Close the socket """
        self.socket.close()
        self.context.term()
