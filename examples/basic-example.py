import micropython
from libs.mqtt import MQTTClient


def puback_cb(msg_id):
  print('PUBACK ID = %r' % msg_id)

def suback_cb(msg_id, qos):
  print('SUBACK ID = %r, Accepted QOS = %r' % (msg_id, qos))
  
def con_cb(connected):
  if connected:
    client.subscribe('subscribe/topic')

def msg_cb(topic, pay):
  print('Received %s: %s' % (topic.decode("utf-8"), pay.decode("utf-8")))


client = MQTTClient('192.168.1.1', port=1883)

client.set_connected_callback(con_cb)
client.set_puback_callback(puback_cb)
client.set_suback_callback(suback_cb)
client.set_message_callback(msg_cb)

client.connect('my_client_id')

while True:
  if client.isconnected():
    try:
      pub_id = client.publish('publish/topic', 'payload', False)
    except Exception as e:
      print(e)

  utime.sleep_ms(1000)

