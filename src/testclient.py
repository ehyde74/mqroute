#from mqttdeco import MQTTClient, MQTTMessage
from mqttdeco import *

from logging import getLogger, basicConfig, DEBUG
from typing import Any

logger = getLogger()

mqtt = MQTTClient(host="test.mosquitto.org")


@mqtt.subscribe(topic="weather/+channel+/wflrealtime.txt", qos=2, raw_payload=True)
def handle_weather1(topic: str, msg: MQTTMessage, parameters: dict[str, Any]):
    payload_type = type(msg.message).__name__
    logger.info("message: ")
    logger.info(f"         topic: {topic}")
    logger.info(f"         parameters: {parameters}")
    logger.info(f"         {payload_type}: {msg.message}")

@mqtt.subscribe(topic="weather/+channel+/wflwflexpj.json", qos=2)
def handle_weather2(topic: str, msg: MQTTMessage, parameters: dict[str, Any]):
    payload_type = type(msg.message).__name__

    logger.info("message: ")
    logger.info(f"         topic: {topic}")
    logger.info(f"         parameters: {parameters}")
    logger.info(f"         {payload_type}: {msg.message}")

@mqtt.subscribe(topic="weather/#", qos=2, raw_payload=True)
def handle_weather3(topic: str, msg: MQTTMessage, _: dict[str, Any]):
    payload_type = type(msg.message).__name__
    logger.info("message: ")
    logger.info(f"         topic: {topic}")
    logger.info(f"         {payload_type}: {msg.message}")



if __name__ == "__main__":
    basicConfig(level=DEBUG)

    # mqtt_client.subscribe(MQTTSubscription(topic="weather/#",
    #                                        qos=2))
    # mqtt_client.subscribe(MQTTSubscription(topic="airpurifier/#",
    #                                        qos=2))
    mqtt.run()

