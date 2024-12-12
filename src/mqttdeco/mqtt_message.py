from dataclasses import dataclass
from typing import Union

__all__ = ["MQTTMessage"]

@dataclass
class MQTTMessage(object):
    """
    Represents a message communicated via MQTT.

    This class is used to encapsulate data related to an MQTT message,
    including the topic under which the message is published and the
    content of the message itself. It can handle messages in various formats,
    supporting both string-based and dictionary-based payloads.

    :ivar topic: The topic under which this message is published or
        subscribed.
    :type topic: str
    :ivar message: The actual message content. This can either be a
        dictionary (e.g., structured JSON data) or a string (e.g., plain
        text).
    :type message: Union[dict, str]
    """
    topic: str
    message: Union[dict, str]
