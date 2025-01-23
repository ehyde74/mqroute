"""
This module contains the `MessagePublisher` class, which is designed for managing
the publishing of messages to an MQTT client using an asynchronous queue. It also
includes the `PublishMessage` dataclass for encapsulating message details and the
`QOS` enumeration for defining message delivery guarantees.

Classes:
- `MessagePublisher`: Handles message publishing to an MQTT client with reliability
  and asynchronous execution.
- `PublishMessage`: Represents a message to be published, including topic, payload,
  Quality of Service (QoS), and other options.
- `QOS`: Defines the levels of Quality of Service for message delivery in MQTT protocols.

Functionality:
- Manages an internal asynchronous queue to store and process messages.
- Supports setting and retrieving an asynchronous event loop for managing tasks.
- Enables publishing of messages with specified QoS and delivery options.

"""
import asyncio
import json
from logging import getLogger
from typing import Optional
from paho.mqtt.client import Client

from .publish_message import PublishMessage


logger = getLogger(__name__)


class MessagePublisher:
    """
    Handles publishing messages to an MQTT client using an asyncio queue.

    This class provides an interface for publishing messages to an MQTT client
    via an asyncio queue. It maintains an internal state to ensure message
    publishing is executed correctly. It requires an MQTT client to be passed
    during initialization. This class is designed to operate asynchronously and
    handle messages efficiently using an event loop.

    Note: A queue is used between the user of this class and the actual message publishing step
    to avoid potential deadlocks in `paho.mqtt`. This is because `paho.mqtt` does not allow direct
    publishing of messages from within message-handling callbacks.

    However, if - and when -  the `Callback_runner` is used,
    then the intermediary queue is not strictly necessary, as the callbacks will not block the
    publishing process.


    :ivar __loop: The asyncio event loop associated with the MessagePublisher,
        allowing coroutine execution.
    :type __loop: Optional[asyncio.AbstractEventLoop]
    :ivar __client: The MQTT client used for publishing messages.
    :type __client: Client
    :ivar __ready: Indicates whether the publisher is ready to accept messages.
    :type __ready: bool
    """
    __queue = asyncio.Queue()

    def __init__(self, mqtt_client: Client):
        self.__loop: Optional[asyncio.AbstractEventLoop] = None
        self.__client: Client =  mqtt_client
        self.__ready: bool = False

    @property
    def ready(self) -> bool:
        """
        Indicates whether the MessagePublisher is ready for use or not.

        This property checks the internal readiness state of the object.
        It returns a boolean value that indicates if the object has been
        appropriately initialized or is prepared to perform its functions.

        :return: The readiness state of the object.
        :rtype: bool
        """
        return self.__ready

    @property
    def loop(self) -> Optional[asyncio.AbstractEventLoop]:
        """
        Provides access to the event loop being used by the class, if any.

        This property retrieves the currently assigned asyncio event loop or
        returns None if no event loop is set. It serves as a getter for the
        private loop attribute and allows other parts of the code to access
        the event loop information in a read-only manner.

        :rtype: Optional[asyncio.AbstractEventLoop]
        :return: The currently set asyncio event loop or None if not set.
        """
        return self.__loop

    @loop.setter
    def loop(self, loop: Optional[asyncio.AbstractEventLoop]):
        self.__loop = loop

    async def execute(self):
        """
        Execute the asynchronous process for handling publish messages from the queue.

        This method continuously retrieves messages from a queue, processes them,
        and attempts to publish them via the client's publish method. If the queue is
        shut down or exceptions occur during the process, it appropriately handles
        the errors to maintain the integrity of the execution flow.

        :raises asyncio.QueueShutDown: Raised when the queue is shut down and no
            further operations can be performed on it.
        :raises Exception: Raised during the publishing process when an unexpected
            error occurs.

        :rtype: None
        """
        self.__ready = True
        while True:
            try:
                logger.debug("Waiting for message to publish")
                message: PublishMessage = await self.__queue.get()
            except asyncio.QueueShutDown:
                break
            try:
                payload = message.payload_str if message.payload_str else message.payload
                status = self.__client.publish(message.topic,
                                               payload,
                                               message.qos.value,
                                               retain=message.retain)
            except Exception as e:
                logger.error(e)
                raise
            logger.debug("Message published %s", status)

    def stop(self):
        """
        Stops the internal queue and disables further operations.

        The `stop` method is designed to manage the shutdown of the internal queue
        used within the object. Once invoked, the queue is stopped and no further
        tasks or operations will be processed.

        :return: None
        """
        self.__queue.shutdown()

    def publish(self, message: PublishMessage):
        """
        Publishes a message to the internal message queue for further processing.
        This method processes the given `message`, converting its `payload` to a
        JSON-formatted string if it is of type `dict`. If the `MessagePublisher`
        is not ready or an event loop is not set, appropriate log messages are
        generated. Otherwise, the message is asynchronously queued for
        publication.

        :param message: The message to be published. The `PublishMessage` object
            must include a payload, which will be converted to a JSON-formatted
            string if it is a dictionary.
        :type message: PublishMessage

        :return: None
        """
        if isinstance(message.payload, dict):
            message.payload_str = json.dumps(message.payload)

        if not self.__ready:
            logger.debug("MessagePublisher is not ready yet.")
            return

        if self.__loop is not None:
            asyncio.run_coroutine_threadsafe(self.__queue.put(message), self.__loop)
        else:
            logger.warning("MessagePublisher.loop is not set.")
