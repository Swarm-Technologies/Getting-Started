# Getting-Started with Swarm Evaluation Kit

All Eval Kit and additional information can be found in the [Eval Kit Quickstart Guide](https://swarm.space/swarm-eval-kit-quickstart-guide/) or in our [Developer Tools.](https://swarm.space/developertools/)

Simple code examples can be found in the [Examples](https://github.com/Swarm-Technologies/Getting-Started/tree/main/EVAL01/Code%20Examples) folder

## Additional Helpful Links

[Swarm Pass Checker](https://kube.tools.swarm.space/pass-checker/)\
[Swarm Eval Kit Quickstart Video](https://youtu.be/zJMWd1PM13E)\
[Activating your Swarm M138 Modem](https://swarm.space/activating-your-swarm-m138-modem/)\
[HIVE Login](https://bumblebee.hive.swarm.space/hive/ui/login)\
[Swarm M138 Modem Product Manual](https://swarm.space/swarm-m138-modem-product-manual/)\
[API Integration Guide](https://swarm.space/swarm-hive-api-integration-guide/)

## FAQ

***Q:*** How do I stop the RSSI-Background from repeating?\
***A:*** Send `$RT 0*16` via Telnet connection

***Q:*** How do I calculate the checksum?\
***A:*** For testing, you can use the [NMEA Checksum Calculator](https://nmeachecksum.eqth.net/) or for integration you can use the following C code found on pg. 34 of the [manual](https://swarm.space/swarm-m138-modem-product-manual/).
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
### Implementation of NMEA checksum in Python
```
def nmea_checksum(command: str) -> int:
    i = 0
    cs = 0
    if command[0] == '$':
        i = 1

    bs = command.encode()
    for b in bs[i:]:
        cs ^= b

    return cs
```
***Q:*** There are some differences with the POWERON message between the demo Swarm Modem, and the Swarm Modem in our card. 
```
$M138 BOOT,POWERON,LPWR=n,WWDG=n,IWDG=n,SFT=Y,BOR=n,PIN=Y,OBL=n,FW=n*4e

vs. 

$M138 BOOT,POWERON,LPWR=n,WWDG=n,IWDG=n,SFT=n,BOR=Y,PIN=Y,OBL=n,FW=n*4e
```
***A:*** `SFT=Y/n and BOR=n/Y` is for internal debug and can be disregarded. You can ensure your Swarm Modem is functioning correctly.

***Q:*** What type of antenna cable do you recommend?\
***A:*** We recommend using [LMR-240-UF](https://www.timesmicrowave.com/Products/Cables/LMR_%C2%AE_High_Performance_/LMR%C2%AE_Ultra_Flex/LMR%C2%AE-240-UF/) 

## Where to find help

Email [techsupport@swarm.space](techsupport@swarm.space) with any questions!







