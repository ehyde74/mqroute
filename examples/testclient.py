import mqttdeco

from logging import getLogger, basicConfig, DEBUG
from typing import Any

logger = getLogger()

mqtt = mqttdeco.MQTTClient(host="test.mosquitto.org")


@mqtt.subscribe(topic="weather/+channel+/wflrealtime.txt", qos=mqttdeco.QOS.EXACTLY_ONCE, raw_payload=True)
def handle_weather1(topic: str, msg: mqttdeco.MQTTMessage, parameters: dict[str, Any]):
    payload_type = type(msg.message).__name__
    logger.info("message: ")
    logger.info(f"         topic: {topic}")
    logger.info(f"         parameters: {parameters}")
    logger.info(f"         {payload_type}: {msg.message}")

@mqtt.subscribe(topic="weather/+channel+/wflwflexpj.json", qos=mqttdeco.QOS.EXACTLY_ONCE)
def handle_weather2(topic: str, msg: mqttdeco.MQTTMessage, parameters: dict[str, Any]):
    payload_type = type(msg.message).__name__

    logger.info("message: ")
    logger.info(f"         topic: {topic}")
    logger.info(f"         parameters: {parameters}")
    logger.info(f"         {payload_type}: {msg.message}")

@mqtt.subscribe(topic="weather/#", qos=mqttdeco.QOS.EXACTLY_ONCE, raw_payload=True)
def handle_weather3(topic: str, msg: mqttdeco.MQTTMessage, _: dict[str, Any]):
    payload_type = type(msg.message).__name__
    logger.info("message: ")
    logger.info(f"         topic: {topic}")
    logger.info(f"         {payload_type}: {msg.message}")



if __name__ == "__main__":
    basicConfig(level=DEBUG)
    mqtt.run()

