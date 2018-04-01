# micropython-mqtt
Async MQTT client library with auto reconnect for MicroPython devices such as the ESP32 or Pycom devices

#### Installation
- Download the **mqtt.py** file and add it to your /libs folder

#### Features
The **MQTTClient** class is a simple lightweight MQTT client for basic MQTT pub / sub functionality. It has the following features:
- Auto reconnect to the broker when the connection is lost
- Supports QOS 0 and 1 for publish and subscribe
- Publish, subscribe and receipt of published messages are all async
- Automatically handles ping requests if no messages are sent for a period of time



