from dataclasses import dataclass
from typing import Optional


__all__ = ["MQTTSubscription"]


@dataclass
class MQTTSubscription(object):
    """
    Represents an MQTT subscription.

    This class is used to define an MQTT subscription with a specific topic and
    Quality of Service (QoS) level. Instances of this class can be passed to a
    library or framework that supports MQTT subscriptions.

    :ivar topic: The topic to which the subscription pertains.
    :ivar qos: The Quality of Service level for the subscription.
    """
    topic: str
    qos: int
