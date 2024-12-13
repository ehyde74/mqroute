from mqroute import MQTTClient, subscribe, MqttMessage, sigkill, sigstop

from typing import Optional


#@mqttclient(host="test.mosquitto.org", port=1883, subscribe="#")
class MQTTTestClient(MQTTClient):
    @sigstop
    async def sigstop_handler(self):
        pass

    @sigkill
    async def sigkill_handler(self):
        pass

    @subscribe("homeassistant/+{sensor}+/#")
    async def handle_homeassistant_sensor(self,
                                          topic: str,
                                          msg: MqttMessage,
                                          parameters: Optional[dict[str, str]] = None):
        pass

    @subscribe("homeassistant/+{house}+/#")
    async def handle_homeassistant_house(self,
                                         topic: str,
                                         msg: MqttMessage,
                                         parameters: Optional[dict[str, str]] = None):
        pass

    @subscribe(topic="homeassistant/house/#",
               subtopic="homeassistant/house/house1")
    async def handle_homeassistant_house(self,
                                         topic: str,
                                         msg: MqttMessage,
                                         parameters: Optional[dict[str, str]] = None):
        pass


if __name__ == "__main__.py":
    client = MQTTTestClient()
    client.run()



