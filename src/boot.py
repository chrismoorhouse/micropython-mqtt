from network import WLAN
import machine
import utime
import pycom

pycom.heartbeat(False)
utime.sleep(0.1)

pycom.rgbled(0x110000)

wlan = WLAN(mode=WLAN.STA)
wlan.connect("Chris's Wi-Fi Network", auth=(WLAN.WPA2, "fluffycurtain667"), timeout=5000)

while not wlan.isconnected():  
  machine.idle()
print("Connected to Wifi\n")

pycom.rgbled(0x000011)
