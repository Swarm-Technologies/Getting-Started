import microcontroller
import json

config = None #{'mode':'ap', 'ssid':'fred', 'password':'12345678'}

def writePreferences():
    configString = json.dumps(config)
    ba = bytearray(configString, 'utf-8')
    microcontroller.nvm[0:len(ba)] = ba
    microcontroller.nvm[len(ba)] = 0

def readPreferences():
    global config
    i = 0;
    configString = ""
    while microcontroller.nvm[i] is not 0:
        configString += chr(microcontroller.nvm[i])
        i = i + 1
    config = json.loads(configString)

writeConfig()
readConfig()

print(config['mode'], config['ssid'], config['password'])