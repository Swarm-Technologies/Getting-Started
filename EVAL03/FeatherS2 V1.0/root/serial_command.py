import supervisor
import sys
import microcontroller

accumulate = ""


def pollSerial():
    global accumulate
    if supervisor.runtime.serial_bytes_available:
        accumulate += sys.stdin.read(1)
    if "\n" in accumulate:
        accumulate = accumulate[:-1]
        params = accumulate.split(' ')
        if params[0] == '@reset':
            microcontroller.reset()
        elif params[0] == '@color':
            if len(params) ==  5:
                pixels[1] = (int(params[1]),int(params[2]),int(params[3]),int(params[4]))
                pixels.write()
        elif params[0] == '@set':
            if params[1] == 'wifi':
                if params[2] in ['ap', 'sta']:
                    config['wifi'] = params[2]
            if params[1] == 'ssid':
                config['ssid'] = params[2]
            if params[1] == 'pw':
                config['pw'] = params[2]
        elif params[0] == '@commit':
            print('commit')
            preferencesStore()
        elif params[0] == '@show':
            print('wifi mode:', config['wifi'])
            print('wifi ssid:', config['ssid'])
            print('wifi pw:  ', config['pw'])
        print("\n> ", end='')
        accumulate = ""


while True:
    pollSerial()