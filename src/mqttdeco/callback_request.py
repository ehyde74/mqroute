from dataclasses import dataclass, field
from typing import Callable, Optional

from .mqtt_message import MQTTMessage


__all__ = ["CallbackRequest"]


@dataclass
class CallbackRequest(object):
    cb_method: Callable[[str, MQTTMessage, Optional[dict[str, str]]], None]
    parameters: Optional[dict[str, str]] = field(default_factory=dict)
    topic: Optional[str] = None
