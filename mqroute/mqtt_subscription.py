"""
This module provides functionality for managing MQTT subscriptions, including subscribing to topics
with configurable QoS (Quality of Service) levels and handling incoming messages as specified by the
MQTT protocol.

Quality of Service (QoS) levels:
- `AT_MOST_ONCE`: Guarantees a best-effort delivery, with no acknowledgment or retries.
- `AT_LEAST_ONCE`: Guarantees that messages will be delivered at least once, using acknowledgments
  to ensure delivery.
- `EXACTLY_ONCE`: Ensures that messages are delivered exactly once, with a handshake mechanism for
  duplication mitigation.

The module is designed as part of an MQTT client implementation to effectively manage topic-based
subscriptions, message dispatching, and related configurations.
"""

from dataclasses import dataclass



__all__ = ["MQTTSubscription"]

from .qos import QOS


@dataclass
class MQTTSubscription:
    """
    Represents an MQTT subscription.

    This class is used to define an MQTT subscription with a specific topic and
    Quality of Service (QoS) level. Instances of this class can be passed to a
    library or framework that supports MQTT subscriptions.

    :ivar topic: The topic to which the subscription pertains.
    :ivar qos: The Quality of Service level for the subscription.
    """
    topic: str
    qos: QOS
