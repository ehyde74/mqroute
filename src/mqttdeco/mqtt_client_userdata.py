from dataclasses import dataclass


@dataclass
class MQTTClientUserData(object):
    client: "MQTTClient"
