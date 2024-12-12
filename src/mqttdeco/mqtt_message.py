from dataclasses import dataclass
from typing import Union

__all__ = ["MQTTMessage"]

@dataclass
class MQTTMessage(object):
    topic: str
    message: Union[dict, str]
