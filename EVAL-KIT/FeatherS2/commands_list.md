# Introduction
### Send Messages
There is an HTTP server runing on port 80 that will open up a web gui. You can use this to send messages. When a tile has queued your message you should see `Message accepted`. When a message has been sent to a sat you should see `Message sent` Your message (including to, from, ect.) is limited to 85 characters.

### TCP Connection
There is a TCP server running on port 23 (Telnet). This has two uses: direct communication with tile and sending @commands wirelessly.

### Serial Connection
Using a wired connection over the USB-C port on the feather you can send the @commands listed below.

# Commands List
### Connect to serial or tcp to send commands.
**@set mode <ap, sta>**  
Set wifi mode to access point or station mode.
Default: ap
`@set mode sta`

**@set wifi <enabled, disabled>**  
Enable or disable wifi functionality and neopixels. It will change the mode and then immediately reset the feather.
Default: enabled
`@set wifi disabled`
  
**@set ssid \<ssid\>**  
Set the ssid to connect to in station mode or to create when in ap mode. 
Default: swarm
`@set ssid swarm`

**@set pw \<password\>**  
Set the password to connect to in station mode or to create when in ap mode.
Default: 12345678
`@set pw 12345678`
  
**@set interval \<minutes\>**  
Set the interval for gps location updating. 0 turns gps updating off. Must be within 15 to 720 minutes.
Default: 60
`set interval 120`

**@show**
Print the wifi mode, ssid, password, and interval to be committed.  
`@show`

**@show <battery, 3v3, solar>**
Print the battery, 3v3, and solar voltage and current.
`@show battery`

**@reset** 
Restart the feather.
`@reset`

**@factory**
Reset the NVM to its default state and restart the feather.
`@factory`
  
You must @reset for changes to take effect.

# OLED
### Initialization
Will display `Connecting to tile...` when connecting and setting up tile.

Will display `Connecting to AP...` when connecting to an AP. You will see this in sta mode.

Will display `Starting AP...` when creating an AP. You will see this in ap mode.

### Running
The first line will display wifi information. `Wifi Disabled` if the wifi configuration is set to disabled. `Can't Connect` if the wifi is enabled but no connection can be made. If wifi is enabled and a connection can be made or ap is created `ST: <IP Address>` or `AP: <IP Address>` will be displayed.

The second line displays energy consumption information. It will cycle between three readouts: `BAT <Voltage> <Current>` for the battery, `SOL <volatage> <current>` for the solar panel, `3V3 <voltage> <current>` for the 3.3V power supply. Will display `ina disconnected` if the feather cannot connect to the ina3221.

The third line will display the background RSSI from the tile. It will look like `RSSI: <RSSI>`

# Tile
The tile will send a $DT (date and time), $GS (gps location information), $GN (gps constilation information), $RT (RSSI) every 5 seconds.

# Buttons
The A button can be used to toggle wifi mode to enabled/disabled without using the command line. It will change the mode and then immediately reset the feather.
It can also be used to do a reset of NVM. To use press the reset button and hold the A button down. Once the feather has been reset let go of the A button. NVM will be erased and another reset of the feather will occur.

The C button can be used to turn the GPS pinger on and off without using the command line.

# Neopixel
The neopixel is an additional indicator for the RSSI. 
`RED`: RSSI greater than -91
`YELLOW`: RSSI between -91 and -95
`GREEN`: RSSI less than -95