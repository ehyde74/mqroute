import asyncio

from .mqtt_message import MQTTMessage
from .callback_request import CallbackRequest

from logging import getLogger
logger = getLogger(__name__)

class CallbackRunner(object):
    __queue = asyncio.Queue()

    def __init__(self):
        self.__loop = None
        self.__ready = False

    @property
    def loop(self):
        return self.__loop

    @loop.setter
    def loop(self, loop):
        self.__loop = loop

    async def process_callbacks(self):
        self.__ready = True
        while True:
            request, msg = await self.__queue.get()
            await request.cb_method(request.topic, msg, request.parameters)


    def run_callback(self, cb_request: CallbackRequest, msg: MQTTMessage):
        while not self.__ready:
            print("Processor not ready yet.")
            return
        if self.__loop is not None:
            asyncio.run_coroutine_threadsafe(self.__queue.put((cb_request, msg)), self.__loop)