// Example testing sketch for various DHT humidity/temperature sensors
// Written by ladyada, public domain

// REQUIRES the following Arduino libraries:
// - DHT Sensor Library: https://github.com/adafruit/DHT-sensor-library
// - Adafruit Unified Sensor Lib: https://github.com/adafruit/Adafruit_Sensor

#include "DHT.h"
#include "stdlib.h"
#include "string.h"

#define DHTPIN 14     // Digital pin connected to the DHT sensor
// Feather HUZZAH ESP8266 note: use pins 3, 4, 5, 12, 13 or 14 --
// Pin 15 can work but DHT must be disconnected during program upload.

// Uncomment whatever type you're using!
//#define DHTTYPE DHT11   // DHT 11
#define DHTTYPE DHT22   // DHT 22  (AM2302), AM2321
//#define DHTTYPE DHT21   // DHT 21 (AM2301)

// Connect pin 1 (on the left) of the sensor to +5V
// NOTE: If using a board with 3.3V logic like an Arduino Due connect pin 1
// to 3.3V instead of 5V!
// Connect pin 2 of the sensor to whatever your DHTPIN is
// Connect pin 3 (on the right) of the sensor to GROUND (if your sensor has 3 pins)
// Connect pin 4 (on the right) of the sensor to GROUND and leave the pin 3 EMPTY (if your sensor has 4 pins)
// Connect a 10K resistor from pin 2 (data) to pin 1 (power) of the sensor

// Initialize DHT sensor.
// Note that older versions of this library took an optional third parameter to
// tweak the timings for faster processors.  This parameter is no longer needed
// as the current DHT reading algorithm adjusts itself to work on faster procs.
DHT dht(DHTPIN, DHTTYPE);

uint8_t nmeaChecksum (String sz, size_t len)
{
  size_t i = 0;
  uint8_t cs;

  if (sz [0] == '$')
    i++;

  for (cs = 0; (i < len) && sz [i]; i++)
  {
    cs ^= ((uint8_t) sz [i]);
  }
  return cs;
}

float h = 0;
float t = 0;
float f = 0;

void sendTempData();
void readFromTile();

void setup() {
  Serial.begin(115200);
  Serial.println(F("DHTxx test!"));

  //Start TILE serial comms
  Serial2.begin(115200);
  
  //Initialize the DHT Sensor
  dht.begin();

}

void loop() {
  // Wait a few seconds between measurements.
  delay(2000);

  // Reading temperature or humidity takes about 250 milliseconds!
  // Sensor readings may also be up to 2 seconds 'old' (its a very slow sensor)
  h = dht.readHumidity();
  // Read temperature as Celsius (the default)
  t = dht.readTemperature();
  // Read temperature as Fahrenheit (isFahrenheit = true)
  f = dht.readTemperature(true);

  // Check if any reads failed and exit early (to try again).
  if (isnan(h) || isnan(t) || isnan(f)) {
    Serial.println(F("Failed to read from DHT sensor!"));
    return;
  }

  // Compute heat index in Fahrenheit (the default)
  // float hif = dht.computeHeatIndex(f, h);
  // Compute heat index in Celsius (isFahreheit = false)
  // float hic = dht.computeHeatIndex(t, h, false);

  // Serial.print("Humidity: ");
  // Serial.print(h);
  // Serial.print("%  Temperature: ");
  // Serial.print(t);
  // Serial.print("C ");
  // Serial.print("°F  Heat index: ");
  // Serial.print(hic);
  // Serial.print("°C ");
  // Serial.print(hif);
  // Serial.println("°F");

  sendTempData();
  readFromTile();

}

void readTileFirmwareVersion(){

  Serial2.println("$FV*10");
  readFromTile();

}

void sendTempData(){

  String in = "$TD \"Hum:" + String(h) + "," + "Temp:" + String(f) +"\"";
  uint8_t checkSum = nmeaChecksum(in, in.length());

  //Sends to PC COMM PORT
  Serial.print(in + "*");
  Serial.println(checkSum,HEX);

  //Sends to TILE
  Serial2.print(in + "*");
  Serial2.println(checkSum,HEX);

}

void readFromTile(){
  
  String incomingString;

  if (Serial2.available() > 0) {
    
    incomingString = Serial2.readString();

    Serial.print("Tile Message: ");
    Serial.println(incomingString);

  }
}
