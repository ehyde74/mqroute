# **MQRoute**

`MQRoute` is a Python MQTT routing library designed to simplify working with MQTT topics by abstracting complexity. It supports advanced topic matching (including wildcards and parameterized topics), allows easy registration of callbacks using decorators, and provides scalable asynchronous callback handling.

Whether you're building an IoT platform or a messaging service, `MQRoute` makes it easy to manage MQTT subscriptions and streamline message processing.

---

## **Features**

- **Dynamic Topic Matching:**  
  Supports `+` and `#` MQTT wildcards, as well as parameterized topics (`+parameter_name+`) for extracting parameters from topic strings.

- **Asynchronous by Design:**  
  Built with `asyncio` for responsive handling of incoming MQTT messages and user-defined asynchronous callbacks.

- **Decorator-Based Callbacks:**  
  Subscribe to MQTT topics effortlessly using Python decorators.

- **Type Safety:**  
  Includes type hints and validation with the `typeguard` library.

- **Extensive Logging and Debugging:**  
  Detailed logs for easy troubleshooting of MQTT operations and callbacks.

- **Customizable Payload Handling:**  
  Easy-to-use mechanisms for handling raw or JSON-formatted payloads.

---

## **Installation**

You can install `MQRoute` using `pip` (make sure to activate a virtual environment):

```bash
pip install mqroute
```

Additions to your `requirements.txt` (or dependency file) should include:
```text
mqroute
paho-mqtt
typeguard
```

---

## **Getting Started**

Below are the steps to start using `MQRoute`. For more advanced usage, refer to detailed examples in [the `testclient.py`](./testclient.py).

### Initialize the MQTT Client

Use the `MQTTClient` class to connect to the MQTT broker, subscribe to topics, and handle messages.

```python
from mqroute.mqtt_client import MQTTClient

mqtt = MQTTClient(host="test.mosquitto.org", port=1883)
mqtt.run()  # Establishes connection and starts listening
```

### Subscribe to Topics

Use the `@mqtt.subscribe` decorator to register a specific callback for a topic. The library supports `+` and `#` MQTT wildcards and parameterized topics.

```python
@mqtt.subscribe(topic="devices/+/status")
async def handle_device_status(topic, msg, params):
    print(f"Device {params[0]} status: {msg.message}")

@mqtt.subscribe(topic="sensors/+/data/+/type/#")
async def handle_sensor_data(topic, msg, params):
    print(f"Sensor {params[0]} data at {params[1]}: {msg.message}")
```

### Handle JSON Payloads Automatically

The `convert_json` parameter in the decorator can be set to `True` to automatically decode JSON payloads.

```python
@mqtt.subscribe(topic="config/update", convert_json=True)
async def handle_config_update(topic, msg, params):
    # Access the payload as a Python dictionary
    config_data = msg.message
    print(f"Received config update: {config_data}")
```

---

## **Example: Full Client Code**

Below is a complete example that demonstrates how to use `MQRoute`:

```python
import asyncio
from mqroute.mqtt_client import MQTTClient

mqtt = MQTTClient(host="test.mosquitto.org", port=1883)

@mqtt.subscribe(topic="devices/+/status")
async def handle_device_status(topic, msg, params):
    print(f"Device {params[0]} status: {msg.message}")

@mqtt.subscribe(topic="sensors/light/status", convert_json=True)
async def handle_light_status(topic, msg, params):
    print(f"Light sensor status: {msg.message}")

async def main():
    mqtt.run()

    # Keep the client running
    await asyncio.sleep(300)

asyncio.run(main())
```

---

## **Advanced Features**

### 1. **Parameterized Topics**
Extract dynamic portions of a topic using parameterized syntax:
```python
@mqtt.subscribe(topic="room/+/device/+param+/status")
async def handle_parametrized(topic, msg, params):
    print(f"Device {params[1]} in room {params[0]} has status: {msg.message}")
```

### 2. **Custom Callback Runner**
For advanced use cases, directly manage callbacks using the `CallbackRunner` class.

### 3. **Error Handling**
Integrate custom mechanisms to handle JSON decoding errors or other message processing issues.

---

## **Testing**

Integration and unit testing can be performed using `pytest`. Sample test cases are provided in the repository.

Run the tests:
```bash
pytest tests/
```

---

## **Planned Improvements**

- **Message Publishing API:** Simple methods for publishing MQTT messages.
- **Graceful Shutdowns:** Cleaning up resources (e.g., unsubscribing tasks) on application stop.
- **pip support:** Make the library installable with pip
---

## **Contributing**

Contributions and feedback are welcome! If you'd like to contribute, please follow these steps:

1. Fork the repository.
2. Create a feature branch (`git checkout -b feature-name`).
3. Commit your changes (`git commit -m 'Add new feature'`).
4. Push to the branch (`git push origin feature-name`).
5. Submit a pull request.

For major changes, please open an issue first to discuss what you'd like to improve.

---

## **License**

This project is licensed under the MIT License. See the [LICENSE](./LICENSE) file for details.

---

## **Additional Notes**

- For complete functionality and advanced examples, refer to the `testclient.py` file provided in the repository.
- MQRoute is in active development. Feel free to report bugs.