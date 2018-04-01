#  Copyright (c) 2018, IAconnects Technology Limited
#  All rights reserved.

#  Redistribution and use in source and binary forms, with or without modification,
#  are permitted provided that the following conditions are met:

#  1. Redistributions of source code must retain the above copyright notice,
#     this list of conditions and the following disclaimer.

#  2. Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions and the following disclaimer in the documentation and/or
#     other materials provided with the distribution.

#  3. Neither the name of the copyright holder nor the names of its contributors may be
#     used to endorse or promote products derived from this software without specific prior
#     written permission.

#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
#  INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
#  FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
#  CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
#  OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
#  LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
#  WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
#  ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# Portions of this code are based on the micropython-lib umqtt.simple library released under the MIT License
# Copyright (c) 2013, 2014 micropython-lib contributors

from micropython import const  
import usocket as socket
import ustruct as struct
from ubinascii import hexlify
import _thread
import utime

TRACE       = const(1)
DEBUG       = const(2)
INFO        = const(3)
WARN        = const(4)
ERROR       = const(5)
DEBUG_LEVEL = const(DEBUG)

class MQTTException(Exception):
  pass

class MQTTClient:

  def __init__(self, server, port, reconnect_retry_time=10, keep_alive=5, ssl=False, ssl_params={}):
    self._client_id = None
    self._sock = None
    self._addr = socket.getaddrinfo(server, port)[0][-1]
    self._ssl = ssl
    self._ssl_params = ssl_params
    self._pub_id = 0
    self._user = None
    self._pswd = None
    self._keep_alive = keep_alive
    self._clean_session = True
    self._lw_topic = None
    self._lw_msg = None
    self._lw_qos = 0
    self._lw_retain = False
    self._message_callback = None
    self._connected_callback = None
    self._puback_callback = None
    self._suback_callback = None
    self._unsuback_callback = None
    self._isconnected = False
    self._reconnect_retry_time = reconnect_retry_time
    self._last_msg_sent_time = 0
    self._connect_thread_running = False
    self._read_thread_running = False

  def __del__():
    self._connect_thread_running = False
    self._read_thread_running = False

  def set_connected_callback(self, cb):
    self._connected_callback = cb

  def set_message_callback(self, cb):
    self._message_callback = cb

  def set_puback_callback(self, cb):
    self._puback_callback = cb

  def set_suback_callback(self, cb):
    self._suback_callback = cb

  def set_unsuback_callback(self, cb):
    self._unsuback_callback = cb

  def connect(self, client_id, user=None, password=None, clean_session=True, will_topic=None, will_qos=0, will_retain=False, will_payload=None):
    self._client_id = client_id
    self._user = user
    self._pswd = password
    self._clean_session = clean_session
    self._lw_topic = will_topic
    self._lw_qos = will_qos
    self._lw_retain = will_retain
    self._lw_msg = will_payload
    self._connect_thread_running = True
    _thread.start_new_thread(self._connect_loop, ())

  def disconnect(self):
    self._connect_thread_running = False
    if self._sock is not None:
      try:
        self._sock.write(b"\xe0\0")
        self._destroy_socket()
      except Exception as e:
        self._log(DEBUG, 'Exception caught closing MQTT socket', e)
    self._log(INFO, 'MQTT socket is disconnecting')

  def isconnected(self):
    return self._isconnected

  def publish(self, topic, payload, retain=False, qos=0):
    if qos < 0 or qos > 1:
      raise MQTTException('QOS must be 0 or 1')
    try:
      pkt = bytearray(b"\x30\0\0\0")
      pkt[0] |= qos << 1 | retain
      sz = 2 + len(topic) + len(payload)
      if qos > 0:
        sz += 2
      assert sz < 2097152
      i = 1
      while sz > 0x7f:
        pkt[i] = (sz & 0x7f) | 0x80
        sz >>= 7
        i += 1
      pkt[i] = sz
      assert self._send_packet(pkt, i + 1)
      assert self._send_str(topic)
      if qos > 0:
        self._pub_id += 1
        struct.pack_into("!H", pkt, 0, self._pub_id)
        assert self._send_packet(pkt, 2)
      assert self._send_packet(payload)
      return self._pub_id
    except Exception as e:
      self._log(ERROR, 'Exception caught publishing MQTT message', e)
      self._destroy_socket()
      raise MQTTException('Failed to publish message to topic %s' % topic)
      
  def subscribe(self, topic, qos=0):
    if qos < 0 or qos > 1:
      raise MQTTException('QOS must be 0 or 1')
    try:
      pkt = bytearray(b"\x82\0\0\0")
      self._pub_id += 1
      struct.pack_into("!BH", pkt, 1, 2 + 2 + len(topic) + 1, self._pub_id)
      assert self._send_packet(pkt)
      assert self._send_str(topic)
      assert self._send_packet(qos.to_bytes(1, 'little'))
      return self._pub_id
    except Exception as e:
      self._log(ERROR, 'Exception caught subscribing to MQTT topic', e)
      self._destroy_socket()
      raise MQTTException('Failed to subscribe to topic %s' % topic)

  def unsubscribe(self, topic):
    try:
      pkt = bytearray(b"\xA2\0\0\0")
      self._pub_id += 1
      struct.pack_into("!BH", pkt, 1, 2 + 2 + len(topic), self._pub_id)
      assert self._send_packet(pkt)
      assert self._send_str(topic)
      return self._pub_id
    except Exception as e:
      self._log(ERROR, 'Exception caught unsubscribing from MQTT topic', e)
      self._destroy_socket()
      raise MQTTException('Failed to unsubscribe from topic %s' % topic)

  def _connect_loop(self):
    last_reconnect_attempt_time = self._reconnect_retry_time * -1
    while self._connect_thread_running:
      try:
        if not self._isconnected:
          if utime.time() > last_reconnect_attempt_time + self._reconnect_retry_time:
            last_reconnect_attempt_time = utime.time()
            self._log(INFO, 'Connecting to MQTT broker....')
            self._isconnected = self._reconnect()
            assert self._isconnected
            if self._connected_callback is not None:
              self._connected_callback(self._isconnected)
            self._read_thread_running = True
            _thread.start_new_thread(self._read_socket_loop, ())
        else:
          if utime.time() > self._last_msg_sent_time + self._keep_alive:
            assert self._send_ping()
      except Exception as e:
        self._destroy_socket()
      finally:
        utime.sleep(1)

  def _log(self, level, message, e=None):
    if level >= DEBUG_LEVEL:
      if e is None:
        print('%s' % (message))
      else:
        print('%s: %r' % (message, e))

  def _reconnect(self):
    # create and open a socket and wrap with SSL if required
    try:
      self._sock = socket.socket()
      self._sock.connect(self._addr)
      self._sock.setblocking(True)
    except OSError as e:
      self._log(DEBUG, 'Exception caught opening MQTT socket', e)
      return False
    try:
      if self._ssl:
        import ussl
        self._sock = ussl.wrap_socket(self._sock, **self._ssl_params)
    except OSError as e:
      self._log(DEBUG, 'Exception caught wrapping MQTT socket in SSL', e)
      return False
    try:
      # build the connect message
      msg = bytearray(b"\x10\0\0\x04MQTT\x04\x02\0\0")
      msg[1] = 10 + 2 + len(self._client_id)
      msg[9] = self._clean_session << 1
      if self._user is not None:
        msg[1] += 2 + len(self._user) + 2 + len(self._pswd)
        msg[9] |= 0xC0
      if self._keep_alive:
        msg[10] |= self._keep_alive >> 8
        msg[11] |= self._keep_alive & 0x00FF
      if self._lw_topic:
        msg[1] += 2 + len(self._lw_topic) + 2 + len(self._lw_msg)
        msg[9] |= 0x4 | (self._lw_qos & 0x1) << 3 | (self._lw_qos & 0x2) << 3
        msg[9] |= self._lw_retain << 5
      # send the connect packet
      assert self._send_packet(msg)
      # send the client ID
      assert self._send_str(self._client_id)
      # send the last will packet
      if self._lw_topic:
        assert self._send_str(self._lw_topic)
        assert self._send_str(self._lw_msg)
      if self._user is not None:
        assert self._send_str(self._user)
        assert self._send_str(self._pswd)
      # check the connection response
      resp = self._sock.read(4)
      assert resp[0] == 0x20 and resp[1] == 0x02
      if resp[3] == 1:
        self._log(WARN, 'Connection refused, wrong protocol version')
      elif resp[3] == 2:
        self._log(WARN, 'Connection refused, client ID rejected')
      elif resp[3] == 3:
        self._log(WARN, 'Connection refused, server unavailable')
      elif resp[3] == 4:
        self._log(WARN, 'Connection refused, bad username or password')
      elif resp[3] == 5:
        self._log(WARN, 'Connection refused, not authorised')
      assert resp[3] == 0
      self._log(INFO, 'Connected to MQTT broker')
      return True
    except AssertionError as e:
      self._log(ERROR, 'Exception caught sending MQTT connection packet', e)
      return False

  def _destroy_socket(self):
    try:
      self._sock.close()
    except Exception as e:
      self._log(DEBUG, 'Exception caught closing MQTT socket', e)
    try:
      del self._sock
    except Exception as e:
      self._log(DEBUG, 'Exception caught destroying MQTT socket', e)
    finally:
      self._read_thread_running = False
      was_connected = self._isconnected
      self._isconnected = False
      if was_connected:
        self._log(INFO, 'MQTT socket destroyed')
        if self._connected_callback is not None:
          self._connected_callback(self._isconnected)

  def _send_packet(self, packet, l=0):
    try:
      if l == 0:
        self._sock.write(packet)
      else:
        self._sock.write(packet, l)
      self._last_msg_sent_time = utime.time()
      return True
    except Exception as e:
      self._log(ERROR, 'Exception caught sending MQTT packet', e)
      return False

  def _send_str(self, s):
    if self._send_packet(struct.pack("!H", len(s))):
      return self._send_packet(s)
    else:
      return False

  def _send_ping(self):
    self._log(TRACE, 'Sending ping message')
    return self._send_packet(b"\xc0\0")

  def _recv_len(self, start):
    if not start & 0x80:
      return start
    n = start
    sh = 0
    while 1:
      b = self._sock.read(1)[0]
      n |= (b & 0x7f) << sh
      assert n < 0x7fffffff
      if not b & 0x80:
        return n
      sh += 7

  def _read_socket_loop(self):
    self._sock.setblocking(True)
    while self._read_thread_running:
      try:
        hdr = self._sock.read(2)
        if hdr != None and hdr != b'':
          if hdr[0] & 0xf0 != 0x30:
            if hdr[0] == 0xd0 and hdr[1] == 0x00: # PING response
              self._log(TRACE, "Received MQTT ping response")
            if hdr[0] == 0x40 and hdr[1] == 0x02: # PUBACK response
              msg_data = self._sock.read(2)
              if self._puback_callback is not None:
                self._puback_callback(msg_data[0] << 8 | msg_data[1])
            if hdr[0] == 0x90 and hdr[1] == 0x03: # SUBACK response
              msg_data = self._sock.read(3)
              if self._suback_callback is not None:
                self._suback_callback(msg_data[0] << 8 | msg_data[1], msg_data[2])
            if hdr[0] == 0xB0 and hdr[1] == 0x02: # UNSUBACK response
              msg_data = self._sock.read(2)
              if self._unsuback_callback is not None:
                self._unsuback_callback(msg_data[0] << 8 | msg_data[1])
          elif hdr[0] & 0xf0 == 0x30: # PUBLISH message
            sz = self._recv_len(hdr[1])
            topic_len = self._sock.read(2)
            topic_len = (topic_len[0] << 8) | topic_len[1]
            topic = self._sock.read(topic_len)
            sz -= topic_len + 2
            if hdr[0] & 6:
              pid = self._sock.read(2)
              pid = pid[0] << 8 | pid[1]
              sz -= 2
            pay = self._sock.read(sz)
            if self._message_callback is not None:
              self._message_callback(topic, pay)
            if hdr[0] & 6 == 2:
              pkt = bytearray(b"\x40\x02\0\0")
              struct.pack_into("!H", pkt, 2, pid)
              self._send_packet(pkt)
      except Exception as e:
        self._log(DEBUG, 'Exception caught processing received message', e)

      utime.sleep_ms(50)
