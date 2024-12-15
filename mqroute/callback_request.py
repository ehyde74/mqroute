from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional

from .mqtt_message import MQTTMessage


__all__ = ["CallbackRequest"]


@dataclass
class CallbackRequest(object):
    """
    This class is used to encapsulate data related to an MQTT callback request. It defines
    the callback method, additional parameters, and the topic to which the callback applies.

    The class is built to handle data in scenarios where MQTT messages are processed, offering
    flexibility in defining custom callbacks with optional parameters and topic specification.

    :ivar cb_method: Function to be executed for the callback when an MQTT message
        is received. It should accept a topic as a string, the received MQTT message,
        and an optional dictionary of parameters.
    :type cb_method: Callable[[str, MQTTMessage, Optional[dict[str, str]]], None]
    :ivar payload_format: Expected payload format for payload (default is JSON).
        The type is any Enum type in order to allow customization of supported payload formats.
    :type payload_format: Enum
    :ivar parameters: Optional parameters to provide additional context or metadata to
        the callback method. Default is an empty dictionary.
    :type parameters: Optional[dict[str, str]]
    :ivar topic: Specific MQTT subscription topic for which the callback should be executed.
        If not specified, the callback may be triggered for all topics.
    :type topic: Optional[str]
    """
    cb_method: Callable[[str, MQTTMessage, Optional[dict[str, str]]], None]
    payload_format: Enum
    parameters: Optional[dict[str, str]] = field(default_factory=dict)
    topic: Optional[str] = None
