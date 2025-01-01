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


@mqtt.sigstop
def sigstop_handler():
    """ Simple example of custom SIGSTOP handler callback."""
    logger.info("sigstop_handler called !!!!")


async def main():
    """ Exxample implementation of main running mqroute instance."""
    await mqtt.run()

    # Keep the client running
    while mqtt.running:
        await asyncio.sleep(0.1)


if __name__ == "__main__":
    basicConfig(level=DEBUG)
    asyncio.run(main())
