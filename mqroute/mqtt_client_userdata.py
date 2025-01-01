"""
This module provides functionality for handling MQTT client interactions with userdata.

It includes methods for connecting to an MQTT broker, subscribing to topics, and processing
messages.

The module uses `paho-mqtt` for MQTT communication and is designed to facilitate user-specific
connections and processing mechanisms.

Dependencies:
- paho-mqtt
- requests

Ensure the appropriate environment setup before using this module.
"""
from dataclasses import dataclass


@dataclass
class MQTTClientUserData:
    """User data for the paho-mqtt client callbacks. Holds MQTTClient object related
    to the callback"""
    client: "MQTTClient"
