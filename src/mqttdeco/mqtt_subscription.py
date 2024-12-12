from dataclasses import dataclass
from typing import Optional


__all__ = ["MQTTSubscription"]


@dataclass
class MQTTSubscription(object):
    topic: str
    qos: int
