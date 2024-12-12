from functools import singledispatchmethod

from  paho.mqtt import client as mqtt
import socket
import json
from random import randint
from typing import Any, Callable, Optional

from logging import getLogger

from .mqtt_subscription import MQTTSubscription
from .mqtt_message import MQTTMessage
from .mqtt_client_userdata import MQTTClientUserData

__all__ = ["MQTTClient"]

from .callback_resolver import CallbackResolver

logger = getLogger(__name__)


class MQTTClient(object):
    def __init__(self, *, host: str, port: int = 1883):
        self.__host: str = host
        self.__port: int = port

        self.__subscriptions: list[MQTTSubscription] = []
        self.__current_subscriptions = []

        #self.__msg_callbacks: dict[MQTTSubscription, Callable[[str, MQTTMessage, Optional[dict[str, str]]], None]] = {}
        self.__msg_callbacks: CallbackResolver = CallbackResolver()


        client_host_name = socket.gethostname()
        client_id = f"{client_host_name}-{randint(0, 1024**4):x}"

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
        #self.__client.on_log = self.on_log
        self.__client.on_unsubscribe = self.on_unsubscribe

    def subscribe(self, topic: str, qos: int, raw_payload: bool = False):
        def decorator(func):
            convert_json = not raw_payload
            def wrapper(*args, **kwargs):
                if convert_json:
                    json_dict = json.loads(args[1].message)
                    args[1].message = json_dict

                return func(*args, **kwargs)

            rewritten_topic = self.__msg_callbacks.register(topic=topic,
                                                            callback=wrapper)
            self.subscribe_topic(rewritten_topic, qos)
            return wrapper

        return decorator

    @property
    def subscriptions(self) -> list[MQTTSubscription]:
        return self.__subscriptions

    def connect(self):
        logger.debug(self.__msg_callbacks)
        self.__client.connect(host=self.__host,
                              port=self.__port)

    @property
    def topic_map(self):
        return self.__msg_callbacks

    def run(self):
        self.connect()
        self.__client.loop_forever()

    @singledispatchmethod
    def subscribe_topic(self, subscription: MQTTSubscription) -> MQTTSubscription:
        self.__subscriptions.append(subscription)
        return subscription

    @subscribe_topic.register
    def _(self, topic: str, qos: int) -> MQTTSubscription:
        subscription = MQTTSubscription(topic=topic, qos=qos)
        self.__subscriptions.append(subscription)
        return subscription

    def on_connect(self,
                   client: mqtt.Client,
                   userdata: MQTTClientUserData,
                   _: dict[str, Any],  # connect_flags
                   reason_code: mqtt.ReasonCodes,
                   __: mqtt.Properties):              # properties

        logger.debug(f"Connected with reason code '{reason_code}'")
        subscriptions = [ (s.topic, s.qos)  for s in userdata.client.subscriptions]
        if subscriptions:
            logger.debug(f" => Subscribing {subscriptions}")
            client.subscribe(subscriptions)
            self.__current_subscriptions = subscriptions
        else:
            logger.warning(" => Nothing to subscribe")
            self.__current_subscriptions = []



    def on_message(self,
                   client: mqtt.Client,
                   userdata: MQTTClientUserData,
                   message: mqtt.MQTTMessage):
        topic = message.topic
        topic_map = userdata.client.topic_map
        msg = MQTTMessage(topic=message.topic,
                          message=message.payload.decode('utf-8'))
        for cb in topic_map.callbacks(topic):
            cb.cb_method(cb.topic, msg, cb.parameters)


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
        self.__current_subscriptions = []
        logger.warning(f"Disconnected with reason {reason_code}")
        logger.info("Trying to reconnect")
        userdata.client.connect()




    def on_log(self,
               _: mqtt.Client,  # client
               __: MQTTClientUserData,  # userdata
               level: int,
               buf: str):
        logger.debug(msg=f"mqtt-client: ({level}): {buf}")


    def on_unsubscribe(self,
                       client: mqtt.Client,
                       userdata: MQTTClientUserData,
                       disconnect_flags: mqtt.DisconnectFlags,
                       reason_code: mqtt.ReasonCodes,
                       properties: mqtt.Properties):
        pass




