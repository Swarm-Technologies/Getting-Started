
#include <WiFi.h>
#include <Preferences.h>
#include "esp_wifi.h"
#include "Commandline.h"

#define OLED
//#define OLED_SSD1306
#define OLED_SH110x

// enable the OTA handler
//#define OTA_HANDLER

//#define MINIEVAL


#ifdef OLED
#include <SPI.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#ifdef OLED_SSD1306
#include <Adafruit_SSD1306.h>
#endif
#ifdef OLED_SH110x
#include <Adafruit_SH110X.h>
#endif

#ifdef OLED_SSD1306
Adafruit_SSD1306 display = Adafruit_SSD1306(128, 32, &Wire);
#endif
#ifdef OLED_SH110x
Adafruit_SH110X display = Adafruit_SH110X(64, 128, &Wire);
#endif

#if defined(ESP32)
  #define BUTTON_A 15
  #define BUTTON_B 32
  #define BUTTON_C 14
#endif  

#include "SDL_Arduino_INA3221.h"

#define BATTERY_CHANNEL 1
#define EXTERNAL_CHANNEL 2
#define THREEv3_CHANNEL 3

SDL_Arduino_INA3221 ina3221;
#endif
  
//how many clients should be able to telnet to this ESP32
#define MAX_SRV_CLIENTS 2

// version string
#define VERSION "1.15"
// port number
#define PORT 23

#ifdef OTA_HANDLER
#include <ArduinoOTA.h>
#endif // OTA_HANDLER

char ssid[65];
char password[65];

Preferences preferences;

WiFiServer server(PORT);
WiFiClient serverClients[MAX_SRV_CLIENTS];

enum
{
    WSTATE_INIT,
    WSTATE_WAITCONNECT,
    WSTATE_CONNECTED
};

int state = WSTATE_INIT;
// debug flag
bool debug = true;

// prototypes
void getssid(void);
void getpass(void);

void setup()
{
    if (debug)
    {
        // debug port
        Serial.begin(115200);
    }

    if (debug) {
      pinMode(LED_BUILTIN, OUTPUT);
#ifdef MINIEVAL
      pinMode(A1, OUTPUT);
#endif
    }

#ifdef OLED

    ina3221.begin();

#ifdef OLED_SSD1306    
    display.begin(SSD1306_SWITCHCAPVCC, 0x3C); // Address 0x3C for 128x32
#endif
#ifdef OLED_SH110x
    display.begin(0x3C, true);
#endif  
    //Serial.println("OLED begun");
  
    // Show image buffer on the display hardware.
    // Since the buffer is intialized with an Adafruit splashscreen
    // internally, this will display the splashscreen.
    display.display();
    delay(1000);
  
    // Clear the buffer.
    display.clearDisplay();
    display.display();
    display.setRotation(1);
    
    pinMode(BUTTON_A, INPUT_PULLUP);
    pinMode(BUTTON_B, INPUT_PULLUP);
    pinMode(BUTTON_C, INPUT_PULLUP);
  
    // text display tests
    display.setTextSize(1);
#ifdef OLED_SSD1306
    display.setTextColor(SSD1306_WHITE);
#endif
#ifdef OLED_SH110x
    display.setTextColor(SH110X_WHITE);
#endif
    display.setCursor(0,0);
#endif    

    // external port
    Serial2.begin(115200);
    //Serial2.setTxBufferSize(2048);
    Serial2.setRxBufferSize(2048);

    if (debug)
    {
        Serial.print("\n\nWiFi serial bridge V");
        Serial.println(VERSION);
    }
}

void loop()
{
    if (debug)
    {
        static uint32_t currentTime = 0;
        static uint32_t onTime = 0;

        // every 3 seconds turn on the LED
        if (millis() - currentTime > 3000)
        {
            currentTime = millis();
            onTime = currentTime;
            digitalWrite(LED_BUILTIN, HIGH);
#ifdef MINIEVAL            
            digitalWrite(A1, LOW);
#endif            
        }

        // if on, turn off after 50mS
        if (digitalRead(LED_BUILTIN) && (millis() - onTime > 50))
        {
            digitalWrite(LED_BUILTIN, LOW);
#ifdef MINIEVAL            
            digitalWrite(A1, HIGH);
#endif            
        }
    }
    
#ifdef OTA_HANDLER
    if (WiFi.status() == WL_CONNECTED)
        ArduinoOTA.handle();
#endif // OTA_HANDLER

    if (getCommandLineFromSerialPort(CommandLine))
    {
        DoMyCommand(CommandLine);
    }

    switch (state)
    {
    case WSTATE_INIT:
        getssid();
        getpass();

        WiFi.mode(WIFI_STA);

        if (debug)
        {
            uint8_t mac[6];
            char _hostname[20];

            WiFi.disconnect();
            //WiFi.config(INADDR_NONE, INADDR_NONE, INADDR_NONE);
            
            WiFi.macAddress(mac);
            snprintf(_hostname, 20, "esp32-%02x%02x%02x", mac[3], mac[4], mac[5]);
            
            WiFi.setHostname(_hostname);
            
            Serial.print("\nHostname: "); Serial.println(_hostname);
            Serial.print("Connecting to ");
            Serial.print(ssid);
            Serial.print(" (pw = " + String(password) + ") ");
        }

        WiFi.begin(ssid, password);

        // change some defaults to use max output and no PS in STA mode
        esp_wifi_set_max_tx_power(82); // max WiFi Power
        esp_wifi_set_ps(WIFI_PS_NONE); // turn off Power saving        
      
#ifdef OTA_HANDLER
        ArduinoOTA
            .onStart([]() {
                String type;

                if (ArduinoOTA.getCommand() == U_FLASH)
                    type = "sketch";
                else // U_SPIFFS
                    type = "filesystem";

                // NOTE: if updating SPIFFS this would be the place to unmount SPIFFS using SPIFFS.end()
                Serial.println("Start updating " + type);
            })
            .onEnd([]() {
                Serial.println("\nEnd");
            })
            .onProgress([](unsigned int progress, unsigned int total) {
                Serial.printf("Progress: %u%%\r", (progress / (total / 100)));
            })
            .onError([](ota_error_t error) {
                Serial.printf("Error[%u]: ", error);

                if (error == OTA_AUTH_ERROR)
                    Serial.println("Auth Failed");

                else if (error == OTA_BEGIN_ERROR)
                    Serial.println("Begin Failed");

                else if (error == OTA_CONNECT_ERROR)
                    Serial.println("Connect Failed");

                else if (error == OTA_RECEIVE_ERROR)
                    Serial.println("Receive Failed");

                else if (error == OTA_END_ERROR)
                    Serial.println("End Failed");
            });

        // if DNSServer is started with "*" for domain name, it will reply with
        // provided IP to all DNS request
        ArduinoOTA.begin();
#endif // OTA_HANDLER

        state = WSTATE_WAITCONNECT;
        break;

    case WSTATE_WAITCONNECT:
        if (WiFi.status() == WL_CONNECTED)
        {
            if (debug)
                Serial.println("\nStarting TCP Server");

            server.begin();
            server.setNoDelay(true);

            if (debug)
            {
                Serial.print("\nReady! Use 'telnet (or nc) ");
                Serial.print(WiFi.localIP());
                Serial.print(" ");
                Serial.print(PORT);
                Serial.println("' to connect");
            }

            state = WSTATE_CONNECTED;
        }
        else
        {
            if (debug)
            {
                Serial.print(".");
                delay(500);
            }
        }

        break;

    case WSTATE_CONNECTED:
        uint8_t i;

        if (WiFi.status() == WL_CONNECTED)
        {
            //check if there are any new clients
            if (server.hasClient())
            {
                for (i = 0; i < MAX_SRV_CLIENTS; i++)
                {
                    //find free/disconnected spot
                    if (!serverClients[i] || !serverClients[i].connected())
                    {
                        if (serverClients[i])
                            serverClients[i].stop();

                        serverClients[i] = server.available();

                        if (!serverClients[i])
                            if (debug)
                                Serial.println("available broken");

                        if (debug)
                        {
                            Serial.print("New client (");
                            Serial.print(i);
                            Serial.print("): ");
                            Serial.println(serverClients[i].remoteIP());
                       }

                        break;
                    }
                }

                if (i >= MAX_SRV_CLIENTS)
                {
                    if (debug)
                        Serial.println("no free spots - rejecting");

                    //no free/disconnected spot so reject
                    server.available().stop();
                }
            }

#ifdef OLED
            static unsigned long time_now = 0;
            if (millis() - time_now > 2000) 
            {
                time_now = millis();
                // update the OLED display
                display.clearDisplay();
                display.setCursor(0,0);
                display.print("Connected to ");
                display.println(ssid);
                display.print("IP: ");
                display.println(WiFi.localIP());
                display.print("vBatt: ");
                display.println(ina3221.getBusVoltage_V(BATTERY_CHANNEL) + (ina3221.getShuntVoltage_mV(BATTERY_CHANNEL) / 1000));
                display.print("External: ");
                display.println(ina3221.getBusVoltage_V(EXTERNAL_CHANNEL) + (ina3221.getShuntVoltage_mV(EXTERNAL_CHANNEL) / 1000));
                display.display();
            }
#endif

            //check clients for data
            for (i = 0; i < MAX_SRV_CLIENTS; i++)
            {
                if (serverClients[i] && serverClients[i].connected())
                {
                    if (serverClients[i].available())
                    {
                        //get data from the telnet client and push it to the UART
                        while (serverClients[i].available())
                            Serial2.write(serverClients[i].read());
                    }
                }
                else
                {
                    if (serverClients[i])
                    {
                        serverClients[i].stop();
                    }
                }
            }
            //check UART for data
            if (Serial2.available())
            {
                size_t len = Serial2.available();
                uint8_t sbuf[len];

                Serial2.readBytes(sbuf, len);

                //push UART data to all connected telnet clients
                for (i = 0; i < MAX_SRV_CLIENTS; i++)
                {
                    if (serverClients[i] && serverClients[i].connected())
                    {
                        serverClients[i].write(sbuf, len);
                        delay(1);
                        yield();
                    }
                }
            }
        }
        else
        {
            if (debug) {
                Serial.println("WiFi not connected!");
                Serial.println("Clearning Server");
            }
            
            for (i = 0; i < MAX_SRV_CLIENTS; i++)
            {
                if (serverClients[i])
                    serverClients[i].stop();
            }

            // end the running server
            server.end();

            if (debug)
                Serial.println("Attempting WiFi Reconnect");

            // reconnect the WiFi to the network
            WiFi.reconnect();

            // set to the waitconnect state
            state = WSTATE_WAITCONNECT;
          
            delay(1000);
        }

        break;

    default:
        break;
    }
}

void getssid(void)
{
    preferences.begin("swarm", false);

    if (preferences.getString("ssid", ssid, sizeof(ssid) - 1) == 0)
    {
        strcpy(ssid, "yourssid");
    }

    preferences.end();
}

void getpass(void)
{
    preferences.begin("swarm", false);

    if (preferences.getString("pass", password, sizeof(password) - 1) == 0)
    {
        strcpy(password, "yourpass");
    }

    preferences.end();
}

void setssid(char *ssid)
{
    preferences.begin("swarm", false);
    preferences.putString("ssid", ssid);
    preferences.end();
}

void setpass(char *pass)
{
    preferences.begin("swarm", false);
    preferences.putString("pass", pass);
    preferences.end();
}
