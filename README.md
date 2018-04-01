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

##### `set_connected_callback`
Set the callback method which is fired when the **connected** status changes. This callback is optional
- Parameter: **cb** - the callback method
  - Type: method name
  - Callback Signature: `def connected_cb(status)` where **status** is True if the client is connected or False if disconnected

##### `set_message_callback`
Set the callback method which is fired when a new MQTT message arrives. This callback is optional
- Parameter: **cb** - the callback method
  - Type: method name
  - Callback Signature: `def message_cb(topic, payload)` where **topic** is the message topic and **payload** is the message payload

##### `set_puback_callback`
Set the callback method which is fired when a publish command succeeds. This callback is optional
- Parameter: **cb** - the callback method
  - Type: method name
  - Callback Signature: `def puback_cb(msg_id)` where **msg_id** is a message ID. This can be matched with a message ID returned from the **publish** method to confirm that a publish has succeeded

##### `set_suback_callback`
Set the callback method which is fired when a subscribe command succeeds. This callback is optional
- Parameter: **cb** - the callback method
  - Type: method name
  - Callback Signature: `def suback_cb(msg_id)` where **msg_id** is a message ID. This can be matched with a message ID returned from the **subscribe** method to confirm that a subscribe has succeeded

##### `set_unsuback_callback`
Set the callback method which is fired when an ubsubscribe command succeeds. This callback is optional
- Parameter: **cb** - the callback method
  - Type: method name
  - Callback Signature: `def unsuback_cb(msg_id)` where **msg_id** is a message ID. This can be matched with a message ID returned from the **unsubscribe** method to confirm that an unsubscribe has succeeded

##### `connect`
Connect the MQTT client to the broker. This method is non-blocking and returns before the connection has completed.
- Parameter: **client_id** - the ID of this MQTT client
  - Type: string
- Optional Parameter: **user** - the username used to authenticate with the broker
  - Type: string
  - Default: None
- Optional Parameter: **password** - the password used to authenticate with the broker
  - Type: string
  - Default: None
- Optional Parameter: **clean_session** - set true to start a clean session with the broker
  - Type: boolean
  - Default: True
- Optional Parameter: **will_topic** - the last will and testament topic.
  - Type: string
  - Default: None
- Optional Parameter: **will_qos** - the last will and testament QOS. QOS values of 0, 1 and 2 are valid
  - Type: number 
  - Default: 0
- Optional Parameter: **will_retain** - the last will and testament message retain flag
  - Type: boolean 
  - Default: False
- Optional Parameter: **will_payload** - the last will and testament message payload
  - Type: string 
  - Default: None
