# Getting-Started with Swarm Evaluation Kit

All Eval Kit and additional information can be found in the [Eval Kit Quickstart Guide](https://swarm.space/wp-content/uploads/2021/04/Swarm-Eval-Kit-Quickstart-Guide.pdf) or in our [Developer Tools.](https://swarm.space/developertools/)

Simple examples can be found in the [Examples]() folder

## Things you'll need 
Things you'll need for getting started with the Dev Kit. 

1. Phillips-head #1 screwdriver
2. [NMEA Checksum Calculator](https://nmeachecksum.eqth.net/)
3. Computer with a network connection and USB port 
4. Your favorite terminal emulator with serial monitor and for TCP Connection (we prefer [ZOC](https://www.emtec.com/zoc/index.html))
5.  [USB-UART](https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers) Driver if not recognized by PC

## Additional helpful links

[Swarm Pass Checker](https://kube.tools.swarm.space/pass-checker/)\
[HIVE Login](https://bumblebee.hive.swarm.space/hive/ui/login)\
[Tile Product Manual](https://swarm.space/wp-content/uploads/2021/04/Swarm-Tile-Product-Manual.pdf)\
[API Integration Guide](https://swarm.space/wp-content/uploads/2021/05/Swarm-Hive-1.0-API-Integration-Guide.pdf)

## Common Mistakes

1. SSID and password are case sensitive ***AND spaces are not allowed.***

## FAQ

***Q:*** How do I stop the RSSI-Background from repeating?\
***A:*** Send `$RT 0*16` via Telnet connection

***Q:*** How do I calculate the checksum?\
***A:*** For test you can use the [NMEA Checksum Calculator](https://nmeachecksum.eqth.net/) or for integration you can use the following C code found on pg. 34 of the [manual](https://swarm.space/wp-content/uploads/2021/04/Swarm-Tile-Product-Manual.pdf).
### Implementation of NMEA checksum in C
```
uint8_t nmeaChecksum (const char *sz, size_t len){
    size_t i = 0;
    uint8_t cs;

    if (sz [0] == '$')
        i++;

    for (cs = 0; (i < len) && sz [i]; i++)
        cs ^= ((uint8_t) sz [i]);
        
    return cs;
}
```







