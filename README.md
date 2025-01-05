# **MQRoute**

`MQRoute` is a Python MQTT routing library designed to simplify working with MQTT topics by abstracting complexity. It supports advanced topic matching (including wildcards and parameterized topics), allows easy registration of callbacks using decorators, and provides scalable asynchronous callback handling.

Whether you're building an IoT platform or a messaging service, `MQRoute` makes it easy to manage MQTT subscriptions, streamline message processing, and publish messages to MQTT topics with minimal effort.

---

## **Features**
- **Flexible Publishing:**  
  Easily publish messages to MQTT topics with simple method calls. Supports both JSON and raw payloads.

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

You can install MQRoute simply by using pip:

```shell
pip install mqroute
```

You may also download it from GitHub, for example, when local modifications are needed. That's your call!
---

## **Getting Started**
### Publish Messages
`MQRoute` makes it simple to publish messages to any topic, and it supports JSON encoding by default. Use the `publish` method for synchronous publishing or `publish_async` for asynchronous needs.

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

### Publish to Topics

Use the `@mqtt.publish` decorator to register a specific method to publish message to topic. The return value 
that is either dict or str will be send to this topic. For more complex cases the functional interface
is also available.

```python
async def publish_reset_command(*args, **kwargs):
    # any parameters can be added to the signature
    await mqtt.async_publish_message(topic="devices/thing/command", payload="do_reset")
    
def publish_restart_command(*args, **kwargs):
    # any parameters can be added to the signature
    mqtt.publish_message(topic="devices/thing/command", payload="do_restart")

@mqtt.publish(topic="devices/thing/command")
def publish_send_status_command(*args, **kwargs):
    # any parameters can be added to the signature
    return "send_status"

@mqtt.publish(topic="devices/thing/command")
async def publish_do_factory_reset(passkey: str):
    # any parameters can be added to the signature
    return f"do_factory_reset {passkey}"


```

### Handle JSON Payloads Automatically

JSON payloads are converted automatically to dictionaries. If this behavior is not desired,
 set the `raw_payload` parameter in the decorator to `True` to receive raw data in the callback instead.
 The value of `raw_payload` defaults to `False`. Callbacks can also be marked as fallback, meaning
 they are only called if a topic doesn't match any non-fallback subscriptions. Note: Multiple fallback methods
 can be defined, and multiple fallbacks may match and thus be called.

```python
@mqtt.subscribe(topic="config/update/json")
async def handle_config_update1(topic, msg, params):
    # Access the payload as a Python dictionary
    config_data_as_dict = msg.message
    print(f"Received config update: {config_data_as_dict}")

@mqtt.subscribe(topic="config/update/raw", raw_payload=True)
async def handle_config_update2(topic, msg, params):
    # Access the payload as a raw string
    config_data_as_raw = msg.message
    print(f"Received config update: {config_data_as_raw}")
    
@mqtt.subscribe(topic="config/#", raw_payload=True, fallback=True)
async def handle_config_update3(topic, msg, params):
    # Access the payload as a raw string
    config_data_as_raw = msg.message
    print(f"Received config update: {config_data_as_raw}")

```

---

### Custom signal handling for terminating application
Custom termination logic can be applied by using decorator sigstop:

```python
@mqtt.sigstop
async def sigstop_handler():
    # termination requested
    print(f"Received request to terminate application.")
```
---

## **Example: Full Client Code**
Below is an updated example that demonstrates how to use `MQRoute`:
The updated example below demonstrates how to use `MQRoute` for subscribing to and publishing MQTT messages:
```python
import asyncio
from mqroute.client import MQTTClient
from mqroute.mqtt_client import MQTTClient

mqtt = MQTTClient(host="mqtt.example.com", port=1883)


@mqtt.subscribe(topic="devices/+/status")
async def handle_device_status(topic, msg, params):
    print(f"Device {params[0]} status: {msg.message}")


@mqtt.subscribe(topic="sensors/+/status", raw_payload=True)
async def handle_sensor_status(topic, msg, params):
    sensor_id = params[0]
    print(f"Sensor {sensor_id} received raw status: {msg.message}")

@mqtt.subscribe(topic="sensors/#", fallback=True)
async def handle_sensor_data(topic, msg, params):
    print(f"Sensor data received on topic {topic}: {msg.message}")
    
@mqtt.sigstop
async def sigstop_handler():
    # termination requested
    print(f"Received request to terminate application.")

    
async def handle_green_light_status(topic, msg, params):
    print(f"Green sensor status: {msg.message}")

async def handle_green_light_status(topic, msg, params):
    print(f"Green sensor status: {msg.message}")

async def publish_example():
    # Publish using JSON payload and more explicit functional interface
    await mqtt.publish(topic="devices/control", payload={"command": "restart", "timeout": 5})

@mqtt.publish(topic="raw/commands")    
async def publish_example2(data: str):
    # Publish using raw payload and simpler decorated interface
    return f"Raw data string with parameter '{data}'"


async def main(): 
    # callback can also be added using functional interface.
    mqtt.add_subscription(handle_green_light_status,
                          topic="sensors/green/status")
    await mqtt.run()
    
    # Include publishing example
    await publish_example()
    await publish_example2("this data")
    
    # Keep the client running
    while mqtt.running:
        await asyncio.sleep(0.1)


if __name__ == "__main__":
    asyncio.run(main())
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
- **Customization and extendability:** Allow easy means  to support for example custom payload formats
- **Demo environment**: Demo environment with mqtt router and two mqroute clients talking. This would allow
                        demo client to not depend on test.mosquitto.org
                        demo client to not depend on third-party MQTT brokers.

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