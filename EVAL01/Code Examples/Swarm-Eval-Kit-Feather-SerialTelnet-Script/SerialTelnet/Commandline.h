#include <string.h>
#include <stdlib.h>

void setssid(char *ssid);
void setpass(char *pass);

//this following macro is good for debugging, e.g.  print2("myVar= ", myVar);
#define print2(x, y) (Serial.print(x), Serial.println(y))

#define CR '\r'
#define LF '\n'
#define BS '\b'
#define NULLCHAR '\0'
#define SPACE ' '

#define COMMAND_BUFFER_LENGTH 80             //length of serial buffer for incoming commands
char CommandLine[COMMAND_BUFFER_LENGTH + 1]; //Read commands into this buffer from Serial.  +1 in length for a termination char

const char *delimiters = ", \n"; //commands can be separated by return, space or comma

/*************************************************************************************************************
    getCommandLineFromSerialPort()
      Return the string of the next command. Commands are delimited by return"
      Handle BackSpace character
      Make all chars lowercase
*************************************************************************************************************/

bool getCommandLineFromSerialPort(char *commandLine)
{
    static uint8_t charsRead = 0; //note: COMAND_BUFFER_LENGTH must be less than 255 chars long
    //read asynchronously until full command input
    while (Serial.available())
    {
        char c = Serial.read();

        switch (c)
        {
        case CR: //likely have full command in buffer now, commands are terminated by CR and/or LS
        case LF:
            commandLine[charsRead] = NULLCHAR; //null terminate our command char array

            if (charsRead > 0)
            {
                charsRead = 0; //charsRead is static, so have to reset
                Serial.println(commandLine);

                return true;
            }

            break;

        case BS: // handle backspace in input: put a space in last char
            if (charsRead > 0)
            { //and adjust commandLine and charsRead
                commandLine[--charsRead] = NULLCHAR;
                Serial << byte(BS) << byte(SPACE) << byte(BS); //no idea how this works, found it on the Internet
            }

            break;

        default:
            // c = tolower(c);
            if (charsRead < COMMAND_BUFFER_LENGTH)
            {
                commandLine[charsRead++] = c;
            }

            commandLine[charsRead] = NULLCHAR;

            break;
        }
    }

    return false;
}

void DoMyCommand(char *commandLine)
{
    //  print2("\nCommand: ", commandLine);
    int result;

    char *ptrToCommandName = strtok(commandLine, delimiters);
    //  print2("commandName= ", ptrToCommandName);

    if (strcmp(ptrToCommandName, "ssid") == 0)
    {
        char *ssid = strtok(NULL, delimiters);

        Serial.println("setting ssid to " + String(ssid));
        setssid(ssid);
    }

    else if (strcmp(ptrToCommandName, "pass") == 0)
    {
        char *pass = strtok(NULL, delimiters);

        Serial.println("Setting password to " + String(pass));
        setpass(pass);
    }
    
    else if (strcmp(ptrToCommandName, "reset") == 0)
    {
        ESP.restart();
    }
}
