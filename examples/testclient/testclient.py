"""
Module Name: testclient

This module is designed for tasks related to testing client functionalities.
It provides tools and helpers to set up and execute client test scenarios.

Dependencies:
- docutils
- pip
- pytest
- requests
- wheel
"""

import asyncio
from logging import getLogger, basicConfig, DEBUG
from typing import Any

import mqroute

logger = getLogger()

mqtt = mqroute.MQTTClient(host="test.mosquitto.org")


@mqtt.subscribe(topic="weather/+channel+/wflrealtime.txt",
                qos=mqroute.QOS.EXACTLY_ONCE,
                raw_payload=True)
async def handle_weather1(topic: str, msg: mqroute.MQTTMessage, parameters: dict[str, Any]):
    """ Simple example method processing received MQTT messages"""
    payload_type = type(msg.message).__name__
    logger.info("message (handle_weather1): ")
    logger.info("         1 topic: %s", topic)
    logger.info("         1 parameters: %s", parameters)
    logger.info("         1 %s: %s", payload_type, msg.message )

@mqtt.subscribe(topic="weather/+channel+/wflwflexpj.json", qos=mqroute.QOS.EXACTLY_ONCE)
async def handle_weather2(topic: str, msg: mqroute.MQTTMessage, parameters: dict[str, Any]):
    """ Simple example method processing received MQTT messages"""
    payload_type = type(msg.message).__name__

    logger.info("message:  (handle_weather2)")
    logger.info("         2 topic: %s", topic)
    logger.info("         2 parameters: %s", parameters)
    logger.info("         2 %s: %s", payload_type, msg.message )

@mqtt.subscribe(topic="weather/#",
                qos=mqroute.QOS.EXACTLY_ONCE,
                raw_payload=True,
                fallback=True)
def handle_weather3(topic: str, msg: mqroute.MQTTMessage, _: dict[str, Any]):
    """ Simple example method processing received MQTT messages that have matching topic
     and are not processed by any other callback."""
    payload_type = type(msg.message).__name__
    logger.info("message:  (handle_weather3)")
    logger.info("         3 topic:%s", topic)
    logger.info("         3 %s: %s", payload_type, msg.message)
    publish_another_response("Hello")
    logger.info("Hello sent")

@mqtt.sigint
def sigint_handler():
    """ Simple example of custom SIGINT handler callback."""
    logger.info("sigint_handler called !!!!")


RESPONSE_COUNTER = 0        # pylint: disable global-statement

async def handle_weather4(topic: str, msg: mqroute.MQTTMessage, _: dict[str, Any]):
    """ Simple example method processing received MQTT messages that have matching topic
     and are not processed by any other callback."""
    global RESPONSE_COUNTER                 # pylint: disable=global-statement
                                            # for the sake of simplicity in this example...
    payload_type = type(msg.message).__name__
    logger.info("message:  (handle_weather4)")
    logger.info("         4 topic:%s", topic)
    logger.info("         4 %s: %s", payload_type, msg.message)
    mqtt.publish_message("mqroute/response",
                         {"mqroute": "response",
                          "serial": RESPONSE_COUNTER},
                          qos=mqroute.QOS.EXACTLY_ONCE)
    RESPONSE_COUNTER += 1
    await mqtt.async_publish_message("mqroute/response",
                                     {"mqroute": "response2",
                                      "serial": RESPONSE_COUNTER},
                                     qos=mqroute.QOS.EXACTLY_ONCE)
    RESPONSE_COUNTER += 1
    logger.info("              4 **RESPONSE MESSAGES SENT")


@mqtt.subscribe(topic="mqroute/response", qos=mqroute.QOS.EXACTLY_ONCE)
async def handle_mqroute_response(topic: str, msg: mqroute.MQTTMessage, _: dict[str, Any]):
    """ Simple example method processing received MQTT messages that have matching topic
     and are not processed by any other callback."""
    payload_type = type(msg.message).__name__
    logger.info("message:  (mqroute_response)")
    logger.info("         R1 topic:%s", topic)
    logger.info("         R1: %s %s", payload_type, msg.message)


@mqtt.publish(topic="mqroute/another_response")
def publish_another_response(msg: str):
    """
    Publishes a response message to a specific MQTT topic.

    This function is designed to package the provided message into a specific format
    and send it to the "mqroute/another_response" topic via the MQTT protocol.

    :param msg: The message to be sent.
    :type msg: str
    :return: A dictionary containing the formatted message text.
    :rtype: dict
    """
    return {"text": msg}

@mqtt.subscribe(topic="mqroute/another_response", qos=mqroute.QOS.EXACTLY_ONCE)
async def handle_mqroute_another_response(topic: str, msg: mqroute.MQTTMessage, _: dict[str, Any]):
    """ Simple example method processing received MQTT messages that have matching topic
     and are not processed by any other callback."""
    payload_type = type(msg.message).__name__
    logger.info("message:  (mqroute_response2)")
    logger.info("         R2 topic:%s", topic)
    logger.info("         R2: %s %s", payload_type, msg.message)


async def main():
    """ Example implementation of main running mqroute instance."""

    # register one of the handlers using functional interface (allows dynamic creation of
    # subscriptions)
    mqtt.add_subscription(handle_weather4,
                          topic="weather/vt-dev/wflwflexpj.json",
                          qos=mqroute.QOS.EXACTLY_ONCE,
                          raw_payload=False,
                          fallback=False)

    # start mqroute client
    await mqtt.run()

    # Keep the client running
    while mqtt.running:
        await asyncio.sleep(0.1)


if __name__ == "__main__":
    basicConfig(level=DEBUG)
    asyncio.run(main())
