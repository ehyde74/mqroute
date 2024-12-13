from dataclasses import dataclass


@dataclass
class MQTTClientUserData(object):
    """
    Encapsulates user data passed to an MQTT client connection.

    This class is designed to store references to an MQTT client to manage
    client-specific user data. It is useful when an MQTTClient instance
    requires associated metadata or objects to function effectively
    throughout its lifecycle.

    :ivar client: The MQTT client instance associated with this user data.
    :type client: MQTTClient
    """
    client: "MQTTClient"
