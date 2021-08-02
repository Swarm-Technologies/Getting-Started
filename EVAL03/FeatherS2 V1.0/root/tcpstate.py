import wifi
import socketpool
import ipaddress
import time
#import status_led
#from secrets import secrets



TCPHOST = ""  # see below
TCPPORT = 5000
TIMEOUT = None
BACKLOG = 2
MAXBUF = 256

TCPSTATE_START = 0
TCPSTATE_LISTENING = 1
TCPSTATE_CONNECTED = 2
TCPSTATE = TCPSTATE_START
tcplistener = None
tcpconn = None


def tcpMachine():
  global TCPSTATE, tcplistener, tcpconn

  if TCPSTATE == TCPSTATE_START:
    print("Create TCP Server socket", (TCPHOST, TCPPORT))
    tcplistener = pool.socket(pool.AF_INET, pool.SOCK_STREAM)
    tcplistener.settimeout(TIMEOUT)
    tcplistener.setblocking(False)
    tcplistener.bind((TCPHOST, TCPPORT))
    tcplistener.listen(BACKLOG)
    print("Listening")
    TCPSTATE = TCPSTATE_LISTENING
  elif TCPSTATE == TCPSTATE_LISTENING:
    try:
      tcpconn, addr = tcplistener.accept()
      tcpconn.settimeout(0)
      print("Accepted from", addr)
      TCPSTATE = TCPSTATE_CONNECTED
    except:
      pass
  elif TCPSTATE == TCPSTATE_CONNECTED:
    buf = bytearray(MAXBUF)
    try:
      size = tcpconn.recv_into(buf, MAXBUF)
      if size == 0:
        tcpconn.close()
        print("Accepting connections")
        TCPSTATE = TCPSTATE_LISTENING
      else: 
        print("Received", buf[:size], size, "bytes")
        tcpconn.send(buf[:size])
        print("Sent", buf[:size], size, "bytes")
    except Exception as e:
      pass


secrets = {'ssid':'Timpani', 'password':'W!ll1amM!ncher'}

print("Connecting to Wifi")
wifi.radio.connect(secrets["ssid"], secrets["password"])

HTTPHOST = repr(wifi.radio.ipv4_address)
HTTPPORT = 80        # Port to listen on
print(HTTPHOST,HTTPPORT)

pool = socketpool.SocketPool(wifi.radio)

print("Self IP", wifi.radio.ipv4_address)
TCPHOST = str(wifi.radio.ipv4_address)
server_ipv4 = ipaddress.ip_address(pool.getaddrinfo(TCPHOST, TCPPORT)[0][4][0])
print("Server ping", server_ipv4, wifi.radio.ping(server_ipv4), "ms")


while True:
  #consoleMachine()
  #oledMachine()
  #webMailMachine()
  #tileMachine()
  tcpMachine()

