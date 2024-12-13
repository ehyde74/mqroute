import asyncio
import json
import socket
import threading
import time
from functools import singledispatchmethod
from logging import getLogger
from random import randint, uniform
from typeguard import typechecked, check_type
from typing import Any, Callable, Optional

from paho.mqtt import client as mqtt

from .callback_runner import CallbackRunner
from .mqtt_client_userdata import MQTTClientUserData
from .mqtt_message import MQTTMessage
from .mqtt_subscription import MQTTSubscription
from .qos import QOS

__all__ = ["MQTTClient"]

from .callback_resolver import CallbackResolver

logger = getLogger(__name__)


class MQTTClient(object):
    @typechecked
    def __init__(self, *, host: str, port: int = 1883, paho_logs = False):
        """
        Initializes an MQTTClient instance with essential configurations such as host, port, and optional logging.
        This class configures the client's callbacks and prepares it to handle MQTT network operations, including
        connection, subscription, messaging, publishing, and logging.

        :param host: Hostname or IP address of the MQTT broker to connect to.
        :type host: str
        :param port: Port number of the MQTT broker for connection. If not provided, defaults to 1883.
        :type port: int
        :param paho_logs: Optional parameter to enable or disable Paho MQTT client logs. Defaults to False.
        :type paho_logs: bool
        """
        self.__host: str = host
        self.__port: int = port

        self.__backoff_time = 1

        self.__subscriptions: list[MQTTSubscription] = []

        self.__msg_callbacks: CallbackResolver = CallbackResolver()
        self.__cb_runner = CallbackRunner()
        self.__cb_runner_task = None

        client_host_name = socket.gethostname()
        client_id = f"{client_host_name}-{randint(0, 1_000_000):x}"

        logger.info(f"Initializing MQTTClient: {client_id=}, {host=}, {port=}")
        self.__client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
        userdata = MQTTClientUserData(self)
        self.__client.user_data_set(userdata)

        self.__client.on_connect = self.on_connect
        self.__client.on_message = self.on_message
        self.__client.on_publish = self.on_publish
        self.__client.on_subscribe = self.on_subscribe
        self.__client.on_connect_fail = self.on_connect_fail
        self.__client.on_disconnect = self.on_disconnect
        if paho_logs:
            self.__client.on_log = self.on_log
        self.__client.on_unsubscribe = self.on_unsubscribe

    @typechecked
    def subscribe(self,
                  topic: str,
                  qos: QOS = QOS.AT_MOST_ONCE,
                  raw_payload: bool = False):
        """
        The `subscribe` method facilitates MQTT topic subscription by allowing the user to create
        a decorator that processes incoming messages before invoking the decorated function.
        It provides the option to automatically convert JSON payloads to Python dictionaries.
        It also registers the callback to the specified topic and subscribes to it with the
        desired Quality of Service (QoS) level.

        Standard MQTT wildcards are supported:
           - "#" matches any topics under the current level, including multilevel matches.
           - "+" matches exactly one level.
           - If there is a need to capture the value of single level wildcard matched
             by + a parameter can be created. This is achieved by using - instead of
             single + as MQTT standard - syntax like +<parameter_name>+
             The CallbackResolver will then create a parameter <parameter_name> that is
             assigned with value found in the matched topic.

        :param topic: The MQTT topic to subscribe to.
        :param qos: The Quality of Service level for the topic subscription.
        :param raw_payload: If set to True, the message payload will not be converted from JSON.
                            Defaults to False.
        :return: A decorator function that wraps the user's callback function.
        """
        def decorator(func):
            convert_json = not raw_payload
            # In practice, this checks just that it's Callable. Maybe more one day...
            check_type(func,
                       expected_type=Callable[[str, MQTTMessage, Optional[dict[str, str]]], None])
            def wrapper(*args, **kwargs):
                if convert_json:
                    try:
                        json_dict = json.loads(args[1].message)
                        args[1].message = json_dict
                    except (json.JSONDecodeError, AttributeError, TypeError) as e:
                        logger.error(f"Failed to decode JSON payload: {e}\n"
                                     f"          faulty JSON: {args[1].message}")

                        return # just dismiss the message.

                return func(*args, **kwargs)

            rewritten_topic = self.__msg_callbacks.register(topic=topic,
                                                            callback=wrapper)
            self.subscribe_topic(rewritten_topic, qos)
            return wrapper

        return decorator

    @property
    def subscriptions(self) -> list[MQTTSubscription]:
        """
        Provides access to the list of MQTTSubscription objects that represent the
        current subscriptions. The returned list contains all active subscriptions
        associated with the instance, allowing external access in a read-only manner.

        :return: A list of MQTTSubscription objects representing active subscriptions
        :rtype: list[MQTTSubscription]
        """
        return self.__subscriptions

    def connect(self):
        """
        Connects to the server using the specified host and port configuration. This method
        establishes a connection with the server by utilizing the internal messaging callbacks
        and client properties.

        Logs the current message callbacks for debugging purposes before attempting to connect
        to the specified server endpoint.

        :raises ConnectionError: If the connection attempt fails for any reason.
        """
        logger.debug(self.__msg_callbacks)
        self.__client.connect(host=self.__host,
                              port=self.__port)

    def reconnect(self):
        backoff = self.__backoff_time
        while True:
            try:
                self.connect()
                break
            except Exception as e:
                logger.warning(f"Reconnect failed: {e}. Retrying in {backoff} seconds...")
                time.sleep(self.__backoff_time)
                backoff = min(60, backoff * 2 + uniform(0, 1))  # cap at 60 seconds

    @property
    def topic_map(self) -> CallbackResolver:
        """
        Provides access to the topic map which holds the message callback
        resolvers. This property is used to retrieve the callback resolver
        that is linked with message topics to handle incoming messages.

        :return: The message callback resolver associated with topics.
        :rtype: CallbackResolver
        """
        return self.__msg_callbacks

    async def run(self):
        """
        Represents a method to initiate and maintain a connection loop for a client.

        This method establishes a connection and transitions the client to continually
        process events until explicitly stopped. It is often used in environments
        where a continuous bidirectional connection needs to persist.

        :raises Exception: If the connection fails or an error occurs during the
            looping process.

        :return: None
        """
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None,
                                   self.__client.connect,
                                   self.__host,
                                   self.__port)

        self.__cb_runner.loop = loop
        self.__cb_runner_task = asyncio.create_task(self.__cb_runner.process_callbacks())

        while True:
            # Periodically call the client loop method
            self.__client.loop(timeout=1.0)
            await asyncio.sleep(0.1)

    @singledispatchmethod
    def subscribe_topic(self, subscription: MQTTSubscription) -> MQTTSubscription:
        """
        Subscribe to a topic by adding the given subscription to the list of current
        subscriptions and returns it. The method is a dispatch function for handling
        varied input arguments based on the type.

        :param subscription: The MQTT subscription to be added to the list of
            subscriptions.
        :return: The MQTT subscription that was successfully subscribed.
        """
        self.__subscriptions.append(subscription)
        return subscription

    @subscribe_topic.register
    def _(self, topic: str, qos: QOS) -> MQTTSubscription:
        """
        Subscribes to a specific MQTT topic with a designated quality of service (QoS) level
        and registers the subscription. This method allows managing MQTT subscriptions
        by adding them to an internal list and returning the created subscription object.

        :param topic: The MQTT topic to subscribe to.
        :type topic: str
        :param qos: Quality of Service level for the subscription (0, 1, or 2).
        :type qos: QOS
        :return: An `MQTTSubscription` object representing the subscription with the
                 specified topic and QoS level.
        :rtype: MQTTSubscription
        """
        subscription = MQTTSubscription(topic=topic, qos=qos.value)
        self.__subscriptions.append(subscription)
        return subscription

    def on_connect(self,
                   client: mqtt.Client,
                   userdata: MQTTClientUserData,
                   _: dict[str, Any],  # connect_flags
                   reason_code: mqtt.ReasonCodes,
                   __: mqtt.Properties):              # properties
        """
        Handles the connection of the MQTT client to the server. This method is invoked
        when the client establishes a connection to the broker. It logs the connection
        reason code and processes any subscriptions defined in the client's userdata.
        If subscriptions are present, it sends the subscription requests and stores
        them. If no subscriptions are found, a warning is logged and the current
        subscriptions list is cleared.

        :param client: The MQTT client instance that represents the connection to the broker.
        :param userdata: User-defined data of type MQTTClientUserData, which typically holds
            application-specific information, including client's subscriptions.
        :param _: A dictionary representing the connection flags in MQTT protocol.
        :param reason_code: The reason code for the connection result as provided by the MQTT broker.
        :param __: MQTT properties that are associated with the connection establishment.
        :return: None
        """
        logger.debug(f"Connected with reason code '{reason_code}'")
        subscriptions = [ (s.topic, s.qos)  for s in userdata.client.subscriptions]
        if subscriptions:
            logger.debug(f" => Subscribing {subscriptions}")
            client.subscribe(subscriptions)
        else:
            logger.warning(" => Nothing to subscribe")



    def on_message(self,
                   _: mqtt.Client,                # client
                   userdata: MQTTClientUserData,
                   message: mqtt.MQTTMessage):
        """
        This function is a callback for handling incoming MQTT messages. It is triggered
        whenever a message is published on a topic the MQTT client is subscribed to. The
        function processes the incoming message, decodes its payload, and invokes the
        appropriate registered callbacks for the topic using the topic map stored in the
        user data.

        :param _: The MQTT client instance that received the message.
        :type _: mqtt.Client
        :param userdata: The user-defined data passed to the callbacks, typically an
            instance containing metadata or configurations such as a topic-to-callback
            mapping.
        :type userdata: MQTTClientUserData
        :param message: The MQTT message received, containing topic, payload, and
            other metadata.
        :type message: mqtt.MQTTMessage
        :return: None
        """
        topic = message.topic
        topic_map = userdata.client.topic_map
        msg = MQTTMessage(topic=message.topic,
                          message=message.payload.decode('utf-8'))
        for cb in topic_map.callbacks(topic):
             #cb.cb_method(cb.topic, msg, cb.parameters)
             self.__cb_runner.run_callback(cb, msg)



    def on_publish(self,
                   client: mqtt.Client,
                   userdata: MQTTClientUserData,
                   mid: int,
                   reason_code: mqtt.ReasonCodes,
                   properties: mqtt.Properties):
        pass

    def on_subscribe(self,
                     _: mqtt.Client,  # client
                     userdata: MQTTClientUserData,  # userdata
                     __: int,  # mid
                     reason_code_list: list[mqtt.ReasonCodes],
                     ___: mqtt.Properties):                          # properties
        """
        Handle the MQTT client subscription event.

        This method is triggered when the client has successfully completed a
        subscription request. It logs the subscriptions along with their
        corresponding reason codes.

        :param _: The MQTT client instance.
        :param userdata: An instance of MQTTClientUserData used to track client-specific
            data throughout the connection's context.
        :param __: Message identifier (mid), which helps in tracking subscription
            requests.
        :param reason_code_list: A list of reason codes detailing outcomes for each subscribed
            topic.
        :param ___: An instance of mqtt.Properties containing additional properties related
            to the subscription.
        :return: None
        """
        logger.debug(f"Subscriptions completed with following reason codes:")

        for sub, reason in zip(userdata.client.subscriptions, reason_code_list):
            logger.debug(f"    {sub.topic}: '{reason}'")

    def on_connect_fail(self,
                        client: mqtt.Client,
                        userdata: MQTTClientUserData,
                        mid: int,
                        reason_code_list: list[mqtt.ReasonCodes],
                        properties: mqtt.Properties):
        pass

    def on_disconnect(self,
                      _: mqtt.Client,
                      userdata: MQTTClientUserData,
                      __: mqtt.DisconnectFlags,
                      reason_code: mqtt.ReasonCodes,
                      ___: mqtt.Properties):
        """
        Handles client disconnection event from the MQTT broker. Clears the
        current subscriptions, logs the disconnection reason, and attempts
        to reconnect to the broker.

        :param _: An instance of `mqtt.Client` representing the client that
            encountered the disconnect event.
        :param userdata: An instance of `MQTTClientUserData` holding application-
            specific user data associated with the MQTT client.
        :param __: An instance of `mqtt.DisconnectFlags` providing additional flags
            describing the reason for the disconnection.
        :param reason_code: A value of `mqtt.ReasonCodes` enum indicating the
            reason for the disconnect as specified by the MQTT protocol.
        :param ___: An instance of `mqtt.Properties` containing additional
            properties and metadata related to the disconnection.
        :return: None
        """
        logger.warning(f"Disconnected with reason {reason_code}")
        logger.info("Trying to reconnect")
        userdata.client.reconnect()




    def on_log(self,
               _: mqtt.Client,  # client
               __: MQTTClientUserData,  # userdata
               level: int,
               buf: str):
        """
        Handles MQTT logging events for the client. This function is triggered
        whenever an MQTT log event occurs during the client's runtime.

        :param _: The MQTT client instance for the session.
        :param __: User-defined data of type ``MQTTClientUserData`` passed to the
            client during initial configuration.
        :param level: An integer representing the severity level of the log
            event. Higher values typically indicate more severe issues.
        :param buf: A string containing the log message generated by the MQTT
            client or library.

        :return: None. This function does not return any value.
        """
        logger.debug(msg=f"mqtt-client: ({level}): {buf}")


    def on_unsubscribe(self,
                       client: mqtt.Client,
                       userdata: MQTTClientUserData,
                       disconnect_flags: mqtt.DisconnectFlags,
                       reason_code: mqtt.ReasonCodes,
                       properties: mqtt.Properties):
        pass




