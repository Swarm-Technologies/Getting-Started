# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Copyright (C) 2021, Swarm Technologies, Inc.  All rights reserved.  #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
VERSION = '1.3'
import board
import displayio
import digitalio
import terminalio
import busio
import time
import neopixel
from adafruit_display_text import label
import adafruit_displayio_sh1107
from barbudor_ina3221 import *
import supervisor
import sys
import microcontroller
import json
from binascii import hexlify
from microcontroller import watchdog as w
from watchdog import WatchDogMode
from adafruit_debouncer import Debouncer
import gc

ina3221 = None
tile = None
tileLine = bytearray(800)
tilePtr = 0

global DEVTAG
DEVTAG = "TILE"


TILE_STATE_UNKNOWN = 0
TILE_STATE_REBOOTING = 1
TILE_STATE_2 = 2
TILE_STATE_3 = 3
TILE_STATE_4 = 4
TILE_STATE_5 = 5
TILE_STATE_6 = 6  # M138 or TILE
TILE_STATE_CONFIGURED = 7

tileStateTable = [('$FV',   '$FV 20',              4, TILE_STATE_2, TILE_STATE_REBOOTING),  # 0 state
                  ('$RS',   f'${DEVTAG} BOOT,RUNNING', 30, TILE_STATE_2, TILE_STATE_REBOOTING),  # 1 state
                  ('$DT 5', '$DT OK',              4, TILE_STATE_3, TILE_STATE_REBOOTING),  # 2 state
                  ('$GS 5', '$GS OK',              4, TILE_STATE_4, TILE_STATE_REBOOTING),  # 3 state
                  ('$GN 5', '$GN OK',              4, TILE_STATE_5, TILE_STATE_REBOOTING),  # 4 state
                  ('$RT 5', '$RT OK',              4, TILE_STATE_6, TILE_STATE_REBOOTING),  # 5 state
                  ('$CS', '$CS DI=',               4, TILE_STATE_CONFIGURED, TILE_STATE_REBOOTING),  # 5 state
                  (None,     None,                 0, TILE_STATE_CONFIGURED, TILE_STATE_CONFIGURED)]  # 6 state
tileTimeout = 0.0
tileState = TILE_STATE_UNKNOWN

tcpLine = bytearray(800)
tcpPtr = 0
i2c = None

TCPHOST = ""
TCPPORT = 23
TIMEOUT = None
BACKLOG = 2
MAXBUF = 256
TCPSTATE_LISTENING = 1
TCPSTATE_CONNECTED = 2
TCPSTATE = TCPSTATE_LISTENING
tcplistener = None
tcpconn = None
pool = None

HTTPHOST = None
HTTPPORT = 80
web_app = None
wsgiServer = None


config = None
display = None
displayLines = []
inaChannel = 1
inaConnected = False
inaData = {1: (None, None), 2: (None, None), 3: (None, None)}

switchA = None
switchC = None

accumulate = ""
inaTime = 0

global RSSI_RED, RSSI_GREEN
# These values are default for DN=TILE
RSSI_RED = -91
RSSI_GREEN = -95
pixels = neopixel.NeoPixel(board.IO38, 2, bpp=4, pixel_order=neopixel.GRBW)


mdata = []
lastGN = None
lastDT = None
lastRSSI = None
nextGPSTime = 0
gpsCount = 0

helpMessage = '''
@set mode <ap, sta>
Set wifi mode to access point or station mode.

@set wifi <enabled, disabled>
Enable or disable wifi functionality.

@set ssid <ssid>
Set the ssid to connect to in station mode or to create when in ap mode.

@set pw <password>
Set the password to connect to in station mode or to create when in ap mode.

@set interval <minutes>
Set the interval for gps location updating. 0 is never. 15-720 minutes.

@show
Print the wifi mode, ssid, password, and interval to be commited.

@show <battery, 3v3, solar>
Print the battery, 3v3, and solar voltage and current.

@reset
Restart the feather.

You must @reset for changes to take effect.\n\nVersion ''' + VERSION


def displayInit():
  displayio.release_displays()
  display_bus = displayio.I2CDisplay(i2c, device_address=0x3C)

  WIDTH = 128
  HEIGHT = 64
  BORDER = 0

  display = adafruit_displayio_sh1107.SH1107(display_bus, width=WIDTH, height=HEIGHT)

  # SWARM LOGO
  splash = displayio.Group(max_size=10)
  splash.y = 16
  display.show(splash)
  color_palette = displayio.Palette(1)
  color_palette[0] = 0xFFFFFF

  image_file = open("swarm.bmp", "rb")
  image = displayio.OnDiskBitmap(image_file)
  image_sprite = displayio.TileGrid(image, pixel_shader=image.pixel_shader)
  splash.append(image_sprite)
  time.sleep(3)
  splash.pop()
  STRING = "      Swarm  Eval\n" + VERSION.center(24)
  text_area2 = label.Label( terminalio.FONT, text=STRING, scale=1, color=0xFFFFFF, x=0, y=3)
  splash.append(text_area2)
  time.sleep(3)
  splash.pop()
  # SWARM LOGO

  splash = displayio.Group(max_size=10)
  display.show(splash)


  color_bitmap = displayio.Bitmap(WIDTH, HEIGHT, 1)
  color_palette = displayio.Palette(1)
  color_palette[0] = 0xFFFFFF  # White

  bg_sprite = displayio.TileGrid(color_bitmap, pixel_shader=color_palette, x=0, y=0)
  splash.append(bg_sprite)

  inner_bitmap = displayio.Bitmap(WIDTH - BORDER * 2, HEIGHT - BORDER * 2, 1)
  inner_palette = displayio.Palette(1)
  inner_palette[0] = 0x000000  # Black
  inner_sprite = displayio.TileGrid(inner_bitmap, pixel_shader=inner_palette, x=BORDER, y=BORDER)
  splash.append(inner_sprite)

  LINEHEIGHT = 11
  LINESTART = 4
  for line in range(0, 6):
    text_area = label.Label(terminalio.FONT, text=20*" ", color=0xFFFFFF, x=0, y=LINESTART + line*LINEHEIGHT)
    displayLines.append(text_area)
    splash.append(text_area)


def displayLine(line, text):
  displayLines[line].text = text


def makeTileCmd(cmd):
  cbytes = cmd.encode()
  cs = 0
  for c in cbytes[1:]:
    cs = cs ^ c
  return cbytes + b'*%02X\n'%cs


def wifiInit():
  if config['wifi'] == 'disabled':
    displayLine(0, "Wifi Disabled")
    return
  global pool, TCPHOST
  try:
    if config['mode'] == 'sta':
      displayLine(0, "Connecting to AP...")
      wifi.radio.connect(config["ssid"], config["password"])
      print("Self IP", wifi.radio.ipv4_address)
      displayLine(0, "ST: " + str(wifi.radio.ipv4_address))
      pool = socketpool.SocketPool(wifi.radio)
      TCPHOST = str(wifi.radio.ipv4_address)
    else:
      displayLine(0, "Starting AP...")
      if(config['ssid'] == 'swarm'): config['ssid'] = 'swarm-' + '%02x%02x'%(wifi.radio.mac_address[4], wifi.radio.mac_address[5])
      wifi.radio.start_ap(config["ssid"], config["password"])
      displayLine(0, "AP: " + str(wifi.radio.ipv4_address_ap))
      TCPHOST = str(wifi.radio.ipv4_address_ap)
      pool = socketpool.SocketPool(wifi.radio)
  except Exception as e:
    displayLine(0, "Can't Connect")


def tileCheck(line):
  global tileTimeout
  if  tileStateTable[tileState][1] in line:
    tileTimeout = -1.0


def tileStart():
  global tileState, tileTimeout
  displayLine(0, "Connecting to tile...")
  tileState = TILE_STATE_UNKNOWN
  while tileState != TILE_STATE_CONFIGURED:
    tile.write(b'\n' + makeTileCmd(tileStateTable[tileState][0]))
    tileTimeout = time.monotonic() + tileStateTable[tileState][2]
    while (tileTimeout > 0.0) and (tileTimeout > time.monotonic()):
      tilePoll()
      serialPoll()
      w.feed()
    if tileTimeout  < 0.0:
      # Success from state table?
      tileState = tileStateTable[tileState][3]
    else:
      tileState = tileStateTable[tileState][4]


def tileInit():
  global tile
  tile = busio.UART(board.TX,board.RX,baudrate=115200,receiver_buffer_size=8192,timeout=0.0)
  tileStart()


def tileParseLine(line):
  print(line)
  global lastDT, lastGN, lastRSSI
  if len(line) < 4:
    return
  if line[len(line) - 3] != '*':
    return
  cksum1 = 0
  cksum2 = int(line[-2:], 16)
  for c in line[1:-3]:
    cksum1 = cksum1 ^ ord(c)
  if cksum1 != cksum2:
    return
  if tileState != TILE_STATE_CONFIGURED:
    tileCheck(line)
    #return
  if line[0:3] == "$TD":
    if len(mdata) > 10:
      mdata.pop(0)
    mdata.append(line)
  if line[0:3] == "$DT":
    if line == "$DT OK*34":
      lastDT = None
    else:
      lastDT = line
  if line[0:3] == "$GN":
    if line == "$GN OK*2d":
        lastGN = None
    else:
        lastGN = line
  parse = line[:-3].split(' ')
  if parse[0] == "$CS":
    if ',' in parse[1]:
      cs_params = parse[1].split(',')
      for param in cs_params:
          k, v = param.split('=')
          if k == "DN":
              global DEVTAG, RSSI_RED, RSSI_GREEN
              DEVTAG = v
              # Here is where M138 vs Tile params can be set
              if DEVTAG == "TILE":
                RSSI_RED = -91
                RSSI_GREEN = -95
              elif DEVTAG == "M138":
                RSSI_RED = -87
                RSSI_GREEN = -91
  if parse[0] == '$RT':
    if 'RSSI' in parse[1]:
      if ',' in parse[1]:
        rdata = line[4:-3].split(',')
        rtdata = []
        for r in rdata:
          rtdata.append(r.split('='))
        rtdata = dict(rtdata)
        if 'T' in rtdata['TS']:
            d, t = rtdata['TS'].split('T')
        else:
            d, t = rtdata['TS'].split(' ')
        d = d.split('-')
        t = t.split(':')
        dtString = d[0][2:]+d[1]+d[2]+'T'+t[0]+t[1]+t[2]
        print(rtdata)
        displayLine(4, dtString + ' S' + rtdata['DI'][2:])
        displayLine(5, 'R:' + rtdata['RSSI'] + ' S:' + rtdata['SNR'] + ' F:' + rtdata['FDEV'])
      else:
        rssi = parse[1].split('=')
        displayLine(2, "RSSI: " + rssi[1])

        irssi = int(rssi[1])
        lastRSSI = irssi

        if config['wifi'] == 'enabled':
          if irssi > RSSI_RED: # -91 
            pixels[0] = (16, 0, 0, 0)
          elif irssi < RSSI_GREEN:  # -95
            pixels[0] = (0, 16, 0, 0)
          else:
            pixels[0] = (16, 16, 0, 0)
          pixels.write()


def tilePoll():
  global tilePtr
  chars = tile.read(20)
  if chars == None:
    return
  if tcpconn != None:
    try:
      x = tcpconn.send(chars)
    except:
      pass


  for c in chars:
    if c == 0x0A:
      tileParseLine(tileLine[:tilePtr].decode())
      tilePtr = 0
    elif c == 0x08 and tilePtr != 0:
      tilePtr = tilePtr - 1
    elif c >= 0x20 and c <= 0x7f and tilePtr < len(tileLine):
      tileLine[tilePtr] = c
      tilePtr = tilePtr + 1
  pass


def inaInit():
  global ina3221, inaConnected
  try:
    ina3221 = INA3221(i2c, shunt_resistor = (0.01, 0.01, 0.01))
    ina3221.update(reg=C_REG_CONFIG, mask=C_AVERAGING_MASK | C_VBUS_CONV_TIME_MASK | C_SHUNT_CONV_TIME_MASK | C_MODE_MASK,
                                     value=C_AVERAGING_128_SAMPLES | C_VBUS_CONV_TIME_8MS | C_SHUNT_CONV_TIME_8MS | C_MODE_SHUNT_AND_BUS_CONTINOUS)
    ina3221.enable_channel(1)
    ina3221.enable_channel(2)
    ina3221.enable_channel(3)
    inaConnected = True
  except:
    displayLine(1, "ina disconnected")
    inaConnected = False


def inaPoll():
  global inaChannel, inaTime, inaConnected, inaData
  if not inaConnected:
    inaInit()
    return
  if time.time() - inaTime > 5:
    try:
      inaChans = {1:'BAT:', 2:'SOL:', 3:'3V3:'}
      bus_voltage = ina3221.bus_voltage(inaChannel)
      current = ina3221.current(inaChannel)

      displayLine(1, "%s %6.3fV %6.3fA"%(inaChans[inaChannel], bus_voltage, current))
      inaData[inaChannel] = (bus_voltage, current)
      inaChannel = inaChannel + 1
      if inaChannel == 4:
        inaChannel = 1
    except:
      inaConnected = False
    inaTime = time.time()


def tcpInit():
  if config['wifi'] == 'disabled':
    return
  if wifi.radio.ipv4_address_ap is None and wifi.radio.ipv4_address is None:
    return
  global TCPSTATE, TCPHOST, tcplistener, tcpconn
  print("Create TCP Server socket", (TCPHOST, TCPPORT))
  tcplistener = pool.socket(pool.AF_INET, pool.SOCK_STREAM)
  tcplistener.settimeout(TIMEOUT)
  tcplistener.setblocking(False)
  tcplistener.bind((TCPHOST, TCPPORT))
  tcplistener.listen(BACKLOG)
  print("Listening")


def tcpPoll():
  if config['wifi'] == 'disabled' or (wifi.radio.ipv4_address_ap is None and wifi.radio.ipv4_address is None):
    return
  global TCPSTATE, tcplistener, tcpconn, tcpPtr
  if TCPSTATE == TCPSTATE_LISTENING:
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
        tcpconn = None
        print("Accepting connections")
        TCPSTATE = TCPSTATE_LISTENING
      else:
        print("Received", buf[:size], size, "bytes")
        for i in range(size):
          if buf[i] == 0x0A:
            if tcpLine[0] == 0x40:
              command = tcpLine[:tcpPtr].decode()
              params = command.split(' ')
              if params[0] == '@reset':
                tcpconn.send("Resetting...")
                microcontroller.reset()
              elif params[0] == '@color':
                if len(params) ==  5:
                  if config['wifi'] == 'enabled':
                    pixels[1] = (int(params[1]),int(params[2]),int(params[3]),int(params[4]))
                    pixels.write()
              elif params[0] == '@set':
                if params[1] == 'mode':
                  if params[2] in ['ap', 'sta']:
                    config['mode'] = params[2]
                    tcpconn.send(f"Successfully set mode to {params[2]}.")
                    writePreferences()
                if params[1] == 'wifi':
                  if params[2] in ['enabled', 'disabled']:
                    config['wifi'] = params[2]
                    if config['wifi'] == 'disabled':
                      pixels[0] = (0,0,0,0)
                      pixels[1] = (0,0,0,0)
                      pixels.write()
                    tcpconn.send(f"Successfully {params[2]} wifi.")
                    tcpconn.send("Resetting...")
                    microcontroller.reset()
                    writePreferences()
                if params[1] == 'ssid':
                  config['ssid'] = command[10:].strip()
                  tcpconn.send(f"Successfully set ssid to {config['ssid']}.")
                  writePreferences()
                if params[1] == 'pw':
                  config['password'] = command[8:].strip()
                  tcpconn.send(f"Successfully set password to {config['password']}.")
                  writePreferences()
                if params[1] == 'interval':
                  if int(params[2]) == 0 or (int(params[2]) >= 15 and int(params[2]) <= 720):
                    if int(params[2]) == 0 and config['interval'] > 0:
                      config['interval'] = config['interval'] * -1
                      tcpconn.send(f"Successfully set interval to off.")
                    else:
                      config['interval'] = int(params[2])
                      tcpconn.send(f"Successfully set interval to {config['interval']}.")
                    gpsInit()
                    writePreferences()
                  else:
                    tcpconn.send("Interval can only be 0 or 15-720 minutes.")
              elif params[0] == '@show':
                if len(params) == 2:
                  if params[1] == 'battery':
                    tcpconn.send('BAT: ' + str(inaData[1][0]) + 'V ' + str(inaData[1][1]) + 'A')
                  if params[1] == '3v3':
                    tcpconn.send('3V3: ' + str(inaData[3][0]) + 'V ' + str(inaData[3][1]) + 'A')
                  if params[1] == 'solar':
                    tcpconn.send('SOL: ' + str(inaData[2][0]) + 'V ' + str(inaData[2][1]) + 'A')
                else:
                  tcpconn.send('wifi mode:' + config['mode'] + '\n')
                  tcpconn.send('wifi:' + config['wifi'] + '\n')
                  tcpconn.send('wifi ssid:' + config['ssid'] + '\n')
                  tcpconn.send('wifi pw:  ' + config['password'] + '\n')
                  tcpconn.send('gps interval: ' + (str(config['interval']), 'OFF')[config['interval'] <= 0] + '\n')
              elif params[0] == '@factory':
                microcontroller.nvm[0] = 0
                tcpconn.send("Cleared NVM and Resetting...")
                microcontroller.reset()
              elif params[0] == '@help':
                tcpconn.send(helpMessage)
              else:
                tcpconn.send("Invalid command. Type @help for help.")
              print("", end='')
            tile.write(tcpLine[:tcpPtr])
            tile.write(bytearray([0x0a]))
            tcpPtr = 0
          elif buf[i] == 0x08 and tcpPtr != 0:
            tcpPtr = tcpPtr - 1
          elif buf[i] >= 0x20 and buf[i] <= 0x7f and tcpPtr < len(tcpLine):
            tcpLine[tcpPtr] = buf[i]
            tcpPtr = tcpPtr + 1
    except Exception as e:
      pass


def serialInit():
  print("", end='')


def serialPoll():
  global accumulate
  if supervisor.runtime.serial_bytes_available:
    accumulate += sys.stdin.read(1)
  if "\n" in accumulate:
    accumulate = accumulate[:-1]
    params = accumulate.split(' ')
    if params[0] == '@reset':
      print("Resetting...")
      microcontroller.reset()
    elif params[0] == '@color':
      if len(params) ==  5:
        if config['wifi'] == 'enabled':
          pixels[1] = (int(params[1]),int(params[2]),int(params[3]),int(params[4]))
          pixels.write()
    elif params[0] == '@set':
      if params[1] == 'mode':
        if params[2] in ['ap', 'sta']:
          config['mode'] = params[2]
          print(f"Successfully set mode to {params[2]}.")
          writePreferences()
      if params[1] == 'wifi':
        if params[2] in ['enabled', 'disabled']:
          config['wifi'] = params[2]
          if config['wifi'] == 'disabled':
            pixels[0] = (0,0,0,0)
            pixels[1] = (0,0,0,0)
            pixels.write()
          print(f"Successfully {params[2]} wifi.")
          writePreferences()
          print("Resetting...")
          microcontroller.reset()
      if params[1] == 'ssid':
        config['ssid'] = accumulate[10:].strip()
        print(f"Successfully set ssid to {config['ssid']}.")
        writePreferences()
      if params[1] == 'pw':
        config['password'] = accumulate[8:].strip()
        print(f"Successfully set password to {config['password']}.")
        writePreferences()
      if params[1] == 'interval':
        if int(params[2]) == 0 or (int(params[2]) >= 15 and int(params[2]) <= 720):
          if int(params[2]) == 0 and config['interval'] > 0:
            config['interval'] = config['interval'] * -1
            print(f"Successfully set interval to off.")
          else:
            config['interval'] = int(params[2])
            print(f"Successfully set interval to {config['interval']}.")
          gpsInit()
          writePreferences()
        else:
          print("Interval can only be 0 or 15-720 minutes.")
    elif params[0] == '@show':
      if len(params) == 2:
        if params[1] == 'battery':
          print('BAT: ' + str(inaData[1][0]) + 'V ' + str(inaData[1][1]) + 'A')
        if params[1] == '3v3':
          print('3V3: ' + str(inaData[3][0]) + 'V ' + str(inaData[3][1]) + 'A')
        if params[1] == 'solar':
          print('SOL: ' + str(inaData[2][0]) + 'V ' + str(inaData[2][1]) + 'A')
      else:
        print('wifi mode:', config['mode'])
        print('wifi:', config['wifi'])
        print('wifi ssid:', config['ssid'])
        print('wifi pw:  ', config['password'])
        print('gps interval: ' + (str(config['interval']), 'OFF')[config['interval'] <= 0] + '\n')
    elif params[0] == '@factory':
      microcontroller.nvm[0] = 0
      print("Cleared NVM and Resetting...")
      microcontroller.reset()
    elif params[0] == '@test':
      tileParseLine(' '.join(params[1:]))
    elif params[0] == '@help':
      print(helpMessage)
    else:
      print("Invalid command. Type @help for help.")
    print("", end='')
    accumulate = ""


def httpInit():
  if config['wifi'] == 'disabled':
    return
  if wifi.radio.ipv4_address_ap is None and wifi.radio.ipv4_address is None:
    return
  global web_app, wsgiServer, HTTPHOST
  if config['mode'] is 'ap':
    HTTPHOST = repr(wifi.radio.ipv4_address_ap)
  else:
    HTTPHOST = repr(wifi.radio.ipv4_address)
  web_app = WSGIApp()

  @web_app.route("/")
  def on_connect(request):
    f = open("index.html", "r")
    return ("200 OK", ["Content-Type: text/html"], f.read())


  @web_app.route("/logo.png")
  def on_connect(request):
    f = open("logo.png", "r")
    return ("200 OK", ["Content-Type: image/png"], f.read())


  @web_app.route("/msgsend")
  def on_msg(request):
    print(request)
    qs = request.query_params
    d = {"i": 1, "t": urlDecode(qs["user_to"]), "f": urlDecode(qs["user_from"]), "s": urlDecode(qs["user_subject"]), "m": urlDecode(qs["user_message"])}
    s = json.dumps(d)
    h = b'$TD AI=65000,' + hexlify(s.encode())
    cs = 0
    for c in h[1:]:
      cs = cs ^ c
    h = h + b'*%02X\n'%cs
    print(h)
    print(d)
    tile.write(h)
    return ("204 NO CONTENT", [], [])


  @web_app.route("/mdata")
  def on_msg(request):
    global mdata
    mdata.insert(0, '...' if lastRSSI is None else str(lastRSSI))
    response = "\n".join(mdata)
    mdata = []
    return ("200 OK", [], response)

  print(f"open this IP in your browser: http://{HTTPHOST}:{HTTPPORT}/")
  wsgiServer = server.WSGIServer(80, application=web_app)
  wsgiServer.start()


def httppoll():
  if config['wifi'] == 'disabled':
    return
  if wifi.radio.ipv4_address_ap is None and wifi.radio.ipv4_address is None:
    return
  wsgiServer.update_poll()


def urlDecode(s):
  i = 0
  r = ''
  while i < len(s):
    if s[i] == '+':
      r = r + ' '
    elif s[i] == '%':
      r = r + chr(int(s[i+1:i+3], 16))
      i = i + 2
    else:
      r = r + s[i]
    i = i + 1
  return r


def gpsInit():
  global sentQuery
  sentQuery = False
  displayLine(3, 'GPS Ping: ' + (str(config['interval']) + 'min', 'OFF')[config['interval'] <= 0])


def gpspoll():
  global nextGPSTime,gpsCount,sentQuery
  global lastGN, lastDT
  if config['interval'] > 0:
      if time.time() > nextGPSTime:
          if lastGN is not None and lastDT is not None:
              gpsObj = {}
              gn = lastGN[4:-3].split(',')
              s = lastDT
              gpsObj['d'] = 946684800 + time.mktime((int(s[4:8]), int(s[8:10]), int(s[10:12]), int(s[12:14]), int(s[14:16]), int(s[16:18]), -1, -1, -1))
              gpsObj['lt'] = float(gn[0])
              gpsObj['ln'] = float(gn[1])
              gpsObj['a'] = float(gn[2])
              gpsObj['c'] = float(gn[3])
              gpsObj['s'] = float(gn[4])
              gpsObj['n'] = gpsCount
              gpsObj['si'] = inaData[2][1]
              gpsObj['sv'] = inaData[2][0]
              gpsObj['bi'] = inaData[1][1]
              gpsObj['bv'] = inaData[1][0]
              gpsObj['ti'] = inaData[3][1]
              gpsObj['r'] = lastRSSI
              gpsCount += 1
              s = json.dumps(gpsObj)
              s = s.replace(' ', '')
              h = b'$TD AI=65535,' + hexlify(s.encode())
              cs = 0
              for c in h[1:]:
                cs = cs ^ c
              h = h + b'*%02X\n'%cs
              tile.write(h)
              nextGPSTime = config['interval'] * 60 + time.time()

              lastGN = None
              lastDT = None
              sentQuery = False  # reset query for next ping
          else:
              # Force send of $DT @ to update lastDT
              if not sentQuery:
                  tile.write(makeTileCmd("$DT @"))
                  tile.write(makeTileCmd("$GN @"))
                  sentQuery = True


def writePreferences():
  configString = json.dumps(config)
  ba = bytearray(configString, 'utf-8')
  microcontroller.nvm[0:len(ba)] = ba
  microcontroller.nvm[len(ba)] = 0


def readPreferences():
  global config
  try:
    x = microcontroller.nvm[0]
  except:
    microcontroller.nvm[0] = 0
  i = 0
  configString = ""
  while microcontroller.nvm[i] is not 0:
    configString += chr(microcontroller.nvm[i])
    i = i + 1
  if configString == "":
    configString = "{}"
  config = json.loads(configString)
  if not 'mode' in config:
    config['mode'] = 'ap'
  if not 'ssid' in config:
    config['ssid'] = 'swarm'
  if not 'password' in config:
    config['password'] = '12345678'
  if not 'interval' in config:
    config['interval'] = 60
  if not 'wifi' in config:
    config['wifi'] = "enabled"


def watchDogInit():
  w.timeout = 60
  w.mode = WatchDogMode.RESET
  w.feed()


def buttonInit():
  global switchA, switchC

  pinA = digitalio.DigitalInOut(board.D5)
  pinA.direction = digitalio.Direction.INPUT
  pinA.pull = digitalio.Pull.UP
  switchA = Debouncer(pinA)

  pinC = digitalio.DigitalInOut(board.D20)
  pinC.direction = digitalio.Direction.INPUT
  pinC.pull = digitalio.Pull.UP
  switchC = Debouncer(pinC)



def buttonPoll():
  switchA.update()
  if switchA.rose: # just released
    if config['wifi'] == "enabled":
      config['wifi'] = "disabled"
      pixels[0] = (0,0,0,0)
      pixels[1] = (0,0,0,0)
      pixels.write()
    else:
      config['wifi'] = "enabled"
    writePreferences()
    print(f"Successfully {config['wifi']} wifi.")
    print("Resetting...")
    microcontroller.reset()

  switchC.update()
  if switchC.rose:
    config['interval'] = config['interval'] * -1
    writePreferences()
    gpsInit()

  # Update wifi RSSI LED and oled
  if config['wifi'] == "enabled":
    if config['mode'] == "sta" and hasattr(wifi.radio.ap_info, "rssi"):
      rssi = wifi.radio.ap_info.rssi
      displayLine(0, "AP: " + str(wifi.radio.ipv4_address) + f" ({rssi})")
      if rssi > -45:
        pixels[1] = (0, 16, 0, 0)
      elif rssi < -67:
        pixels[1] = (16, 0, 0, 0)
      else:
        pixels[1] = (16, 16, 0, 0)
      pixels.write()


def factoryResetCheck():
  switchA.update()
  if not switchA.value:
    microcontroller.nvm[0] = 0
    while not switchA.value:
      switchA.update()
    print("Cleared NVM and Resetting...")
    microcontroller.reset()


watchDogInit()
buttonInit()
factoryResetCheck()
i2c = busio.I2C(board.SCL, board.SDA, frequency=400000)
# i2c = board.I2C()
displayInit()
readPreferences()
if config['wifi'] == 'enabled':
  import wifi
  import socketpool
  import ipaddress
  import wsgiserver as server
  from adafruit_wsgi.wsgi_app import WSGIApp
inaInit()
serialInit()
tileInit()
wifiInit()
tcpInit()
httpInit()
gpsInit()

try:
  while True:
    tilePoll()
    inaPoll()
    gpspoll()
    serialPoll()
    tcpPoll()
    httppoll()
    buttonPoll()
    w.feed()
    gc.collect()
except Exception as e:
  print(e)
  print("Resetting...")
  microcontroller.reset()



