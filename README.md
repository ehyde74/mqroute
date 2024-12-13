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

You need to install MQRoute by either downloading source code from github by using it as sub repo. In the future also
pip install should be available.


Additions to your `requirements.txt` (or dependency file) should include:
```text
paho-mqtt
typeguard
```

---

## **Getting Started**

Below are the steps to start using `MQRoute`. For more advanced usage, refer to detailed examples in [the `testclient.py`](./testclient.py).

### Initialize the MQTT Client

Use the `MQTTClient` class to connect to the MQTT broker, subscribe to topics, and handle messages.

```python
import asyncio
from mqroute.mqtt_client import MQTTClient

mqtt = MQTTClient(host="test.mosquitto.org", port=1883)
asyncio.run(mqtt.run())  # Establishes connection and starts listening
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

JSON payloads are converted automatically to dictionaries. In case this is not desired
 `convert_json` parameter in the decorator can be set to `False` to receive raw data in callback instead.
 The value of `convert_json` defaults to `True`.

```python
@mqtt.subscribe(topic="config/update/json", convert_json=True)
async def handle_config_update(topic, msg, params):
    # Access the payload as a Python dictionary
    config_data_as_dict = msg.message
    print(f"Received config update: {config_data_as_dict}")

@mqtt.subscribe(topic="config/update/raw", convert_json=False)
async def handle_config_update(topic, msg, params):
    # Access the payload as a raw string
    config_data_as_raw = msg.message
    print(f"Received config update: {config_data_as_raw}")

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

@mqtt.subscribe(topic="sensors/+light+/status", convert_json=True)
async def handle_light_status(topic, msg, params):
    sensor = params["light"] 
    print(f"{sensor} sensor status: {msg.message}")
    

asyncio.run(mqtt.run())
```

---

## **Advanced Features**

### 1. **Parameterized Topics**
Extract dynamic portions of a topic using parameterized syntax:
```python
@mqtt.subscribe(topic="room/+room+/device/+device+/status")
async def handle_parametrized(topic, msg, params):
    print(f"Device {params['device']} in room {params['room']} has status: {msg.message}")
```

### 2. **Custom Callback Runner**
For advanced use cases, directly manage callbacks using the `CallbackRunner` class.

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