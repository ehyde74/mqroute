import asyncio
from logging import getLogger, basicConfig, INFO, DEBUG
import os
import time
from typing import Any

import mqroute


stopping: bool = False

logger = getLogger()

broker_host = os.environ.get("BROKER_HOST", "localhost")
broker_port = int(os.environ.get("BROKER_PORT", 1883))

mqtt = mqroute.MQTTClient(host=broker_host,
                            port=broker_port)

@mqtt.publish(topic="test/ping")
def ping(msg: dict[str, Any]):
    logger.info("ping called")
    return msg

@mqtt.subscribe(topic="test/pong")
def pong(topic: str, msg: mqroute.MQTTMessage, _: dict[str, Any]):
    global stopping
    logger.info(msg.message)
    if not stopping:
        ping({"message": "Ping"})


@mqtt.sigint
def sigint_handler():
    global stopping
    stopping = True
    logger.info("sigstop_handler called, exiting !!!!")

async def main():
    # start mqroute client
    await mqtt.run()

    # wait until client has initialized properly
    while not mqtt.ready:
        await asyncio.sleep(1)

    ping({"message": "Ping"})


    # Keep the client running
    while mqtt.running:
        await asyncio.sleep(0.1)
        #ping({"message": "Ping"})

if __name__ == "__main__":
    basicConfig(level=DEBUG)
    asyncio.run(main())



