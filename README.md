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

#### Usage
See the **basic-example.py** file in the **examples** folder for a simple example of using the **MQTTClient** class

##### `from libs.mqtt import MQTTClient`
Import the MQTTClient class

##### `client = MQTTClient('192.168.1.1', port=1883)`
Construct a new instance of the **MQTTClient** class
- Parameter: **server** - the address of the MQTT broker
  - Type: string
- Parameter: **port** - the TCP/IP port to connect to
  - Type: number
- Optional Parameter: **reconnect_retry_time** - the time in seconds between reconnect retry attempts
  - Type: number
  - Default: 10
- Optional Parameter: **keep_alive** - the time in seconds of no activity before a ping is sent to the broker
  - Type: number
  - Default: 15
- Optional Parameter: **ssl** - set True to use SSL
  - Type: boolean
  - Default: False
- Optional Parameter: **ssl_params** - the SSL parameters to use if using SSL
  - Type: object
  

