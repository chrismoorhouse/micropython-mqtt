import micropython
from libs.mqtt import MQTTClient
#from libs.mqtt import MQTTPublishException
from network import WLAN
import machine
import utime
import _thread
from machine import WDT

total = 0

def puback_cb(msg_id):
  global total
  try:
    total -= msg_id
    print('Total = %r' % total)
  except Exception as e:
    print(e)
  

def con_cb(status):
  print('CONNECTED')
  print(status)


count = 0

#wdt = WDT(timeout=5000)

client = MQTTClient('10.0.1.24', port=1882)

client.set_connected_callback(con_cb)
client.set_puback_callback(puback_cb)

client.connect('iaconnects')


while True:
  if client.isconnected():
    pay = 'Hello %r' % count
    count += 1
    try:
      pub_id = client.publish('chris', pay, False, 1)
      total += pub_id
    except Exception as e:
      print(e)
  utime.sleep_ms(50)

