"""
Module `publish_message`
=========================

Defines the `QOS` enum for setting Quality of Service levels in message delivery,
ranging from no guarantee (`AT_MOST_ONCE`) to reliable, duplicate-free delivery
(`EXACTLY_ONCE`). Used to configure message reliability based on application needs.
"""

from dataclasses import dataclass
from typing import Optional, Union

from .qos import QOS


__all__ =["PublishMessage"]


@dataclass
class PublishMessage:
    """
    Represents a message to be published in a messaging system.

    This class is used to encapsulate the details of a message that will be
    published to a specific topic in a messaging system such as MQTT. It
    includes the topic, message payload, quality of service (QoS) level,
    retain flag, and an optional string representation of the payload.

    :ivar topic: The topic to which the message will be published.
    :type topic: str
    :ivar payload: The message payload, which can be either a string or a dictionary.
    :type payload: Union[str, dict]
    :ivar qos: The quality of service level for message delivery.
    :type qos: QOS
    :ivar retain: A flag indicating whether the message should be retained by the broker.
    :type retain: bool
    :ivar payload_str: An optional string representation of the message payload, used internally
                       in message_publisher.
    :type payload_str: Optional[str]
    """
    topic: str
    payload: Union[str, dict]
    qos: QOS
    retain: bool
    payload_str: Optional[str] = None
