"""
This module defines classes and functions essential for handling MQTT callbacks using
an asynchronous event-driven architecture. It focuses on processing MQTT messages,
formatting payloads, and executing user-defined callback methods. Key components include:

- `MQTTMessage`: Represents an MQTT message with its topic and payload.
- `CallbackRequest`: Encapsulates data for managing a callback request, including the
  callback function, payload format, and optional parameters.
- `PayloadFormat`: Enumeration defining supported payload formats, such as `RAW` and `JSON`.
- `CallbackRunner`: Implements a processing loop to manage and execute asynchronous callback
  requests for MQTT messages.

The module is designed to ensure flexibility and reliability when integrating with external
messaging systems, providing tools for message payload conversion and safe execution of callbacks.
"""

import asyncio
from inspect import iscoroutinefunction
import json
from logging import getLogger
from typing import Optional

from .mqtt_message import MQTTMessage
from .callback_request import CallbackRequest
from .payload_formats import PayloadFormat


logger = getLogger(__name__)


class CallbackRunner:
    """
    This class provides functionality for processing callback requests in an
    asynchronous event-driven architecture. It maintains a queue of requests
    and a processing loop to handle callbacks either as coroutines or regular
    methods.

    The class is primarily designed to integrate with asynchronous I/O
    operations and supports interaction with external messaging or event
    systems. It ensures callbacks are properly queued and executed in a
    thread-safe manner.

    :ivar __ready: Indicates if the processing loop is ready to handle
        callbacks.
    :type __ready: bool
    :ivar __loop: Event loop instance used for processing callbacks and
        queue operations.
    :type __loop: asyncio.AbstractEventLoop
    """
    __queue = asyncio.Queue()

    def __init__(self):
        """
        Represents a class that encapsulates managing an asynchronous event loop
        and an internal state indicating readiness.

        Attributes
        ----------
        __loop : Optional[asyncio.AbstractEventLoop]
            The asyncio event loop used by the class. Defaults to None when not set.
        __ready : bool
            Indicates whether the class is in a ready state. Defaults to False during
            initialization.

        """
        self.__loop: Optional[asyncio.AbstractEventLoop] = None
        self.__ready: bool = False

    @property
    def ready(self) -> bool:
        """
        Indicates whether the CallbackRunner is ready for use or not.

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
        Provides access to the 'loop' property that is asyncio loop, which returns
        the private attribute '__loop'. This property is read-only and does not
        allow modification.

        :return: The value of the private '__loop' attribute.
        :rtype: Same type as the '__loop' attribute.
        """
        return self.__loop

    @loop.setter
    def loop(self, loop: Optional[asyncio.AbstractEventLoop]):
        self.__loop = loop

    def convert_payload(self, request: CallbackRequest, payload: str):
        """
        Converts the given payload based on its specified format in the request object. This method
        transforms the payload into a Python object if the format is JSON, retains it in its raw
        string form for RAW formats, or raises an error for unrecognized formats. The method logs
        errors that occur during JSON processing and returns the payload unchanged.

        :param request: An object containing details about the callback request, including
            the expected payload format.
        :type request: CallbackRequest
        :param payload: The input payload to be converted, potentially in JSON string
            or raw string format.
        :return: Returns the converted payload as a Python object if the payload format
            is JSON, or as a string if the format is RAW.
        :rtype: Union[dict, str]

        :raises NotImplementedError: If the payload format is not recognized.
        """
        if request.payload_format == PayloadFormat.JSON:
            try:
                ret_val = json.loads(payload)
            except (json.JSONDecodeError, AttributeError, TypeError) as e:
                logger.exception("Error while decoding JSON %s", e)
                logger.error("payload=%s",payload)
                ret_val = payload
        elif request.payload_format == PayloadFormat.RAW:
            ret_val = payload
        else:
            msg = f"Unknown payload format: {request.payload_format}"
            raise NotImplementedError(msg)
        return ret_val

    async def process_callbacks(self):
        """
        Handles invocation of callback methods for queued request objects asynchronously.

        This method continuously processes requests from an internal queue. Each request
        object contains a callback method, a topic, a message, and any additional parameters.
        If the callback method specified in the request object is a coroutine function, it
        is awaited; otherwise, it is executed synchronously. The method guarantees queued
        callback methods are invoked in the order they were added to the queue.

        Method exits only after the queue has been shut down by using stop() method of the class.

        :return: None
        """
        self.__ready = True
        while True:
            try:
                request, msg = await self.__queue.get()
            except asyncio.QueueShutDown:
                break

            try:
                final_msg = MQTTMessage(topic=request.topic,
                                        message=self.convert_payload(request, msg.message))
            except Exception as e: # pylint: disable=broad-exception-caught
                logger.exception("Error while convering MQTT message:  %s", e)
                logger.debug("request.topic=%s request.message==%s",request.topic, request.message)
                continue
            try:
                if iscoroutinefunction(request.cb_method):
                    await request.cb_method(request.topic, final_msg, request.parameters)
                else:
                    request.cb_method(request.topic, final_msg, request.parameters)
            except Exception as e: # pylint: disable=broad-exception-caught

                logger.exception("Error while executing callback MQTT message: %s", e)
                logger.debug("request.topic=%s request.message==%s",request.topic, request.message)
                continue

    def stop(self):
        """
        Stops the processing by shutting down the internal queue.

        This method ensures that all resources associated with the queue are properly
        released, and no more items can be enqueued or processed. It should be
        invoked when processing is complete or the queue needs to be terminated
        gracefully.
        """
        self.__queue.shutdown()

    def run_callback(self, cb_request: CallbackRequest, msg: MQTTMessage):
        """
        Handles the execution of a callback by queuing the provided callback request and
        message for processing. Ensures that the processor is ready before queuing, and
        allows asynchronous processing if the loop is active.

        :param cb_request: The callback request object to be processed.
        :type cb_request: CallbackRequest
        :param msg: The MQTT message associated with the callback request.
        :type msg: MQTTMessage
        :return: None
        """
        while not self.__ready:
            print("Processor not ready yet.")
            return

        if self.__loop is not None:
            asyncio.run_coroutine_threadsafe(self.__queue.put((cb_request, msg)), self.__loop)
