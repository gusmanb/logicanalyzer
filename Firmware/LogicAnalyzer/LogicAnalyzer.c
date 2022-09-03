#include <stdio.h>
#include <string.h>
#include "pico/stdlib.h"
#include "hardware/dma.h"
#include "hardware/pio.h"
#include "hardware/clocks.h"
#include "LogicAnalyzer.pio.h"

#define LED_IO 25

//Capture request issued by the host computer
typedef struct _CAPTURE_REQUEST
{
    //Indicates tthe trigger type: 0 = edge, 1 = pattern (complex), 2 = pattern (fast)
    uint8_t triggerType;
    //Trigger channel (or base channel for pattern trigger)
    uint8_t trigger;
    
    //Union of the trigger characteristics (inverted or pin count)
    union
    {
        uint8_t inverted;
        uint8_t count;
    };

    //Trigger value of the pattern trigger
    uint16_t triggerValue;
    //Channels to capture
    uint8_t channels[24];
    //Channel count
    uint8_t channelCount;
    //Sampling frequency
    uint32_t frequency;
    //Number of samples stored before the trigger
    uint32_t preSamples;
    //Number of samples stored after the trigger
    uint32_t postSamples;

}CAPTURE_REQUEST;

//Buffer used to store received data
uint8_t messageBuffer[128];
//Position in the buffer
uint8_t bufferPos = 0;
//Capture status
bool capturing = false;
//Capture request pointer
CAPTURE_REQUEST* req;

//Process USB rceived data
void processInput()
{
    //Try to get char
    uint data = getchar_timeout_us(0);

    //Timeout? Then leave
    if(data == PICO_ERROR_TIMEOUT)
        return;

    //Store char in buffer and increment position
    messageBuffer[bufferPos++] = data;
    
    //If we have stored the first byte and it is not 0x55 restart reception
    if(bufferPos == 1 && messageBuffer[0] != 0x55)
        bufferPos = 0;
    else if(bufferPos == 2 && messageBuffer[1] != 0xAA) //If we have stored the second byte and it is not 0xAA restart reception
        bufferPos = 0;
    else if(bufferPos >= 256) //Have we overflowed the buffer? then inform to the host and restart reception
    {
        printf("ERR_MSG_OVERFLOW\n");
        bufferPos = 0;
    }
    else if(bufferPos > 2) //Try to parse the data
    {
        if(messageBuffer[bufferPos - 2] == 0xAA && messageBuffer[bufferPos - 1] == 0x55) //Do we have the stop condition?
        {

            //Yes, unescape the buffer,
            int dest = 0;

            for(int src = 0; src < bufferPos; src++)
            {
                if(messageBuffer[src] == 0xF0)
                {
                    messageBuffer[dest] = messageBuffer[src + 1] ^ 0xF0;
                    src++;
                }
                else
                    messageBuffer[dest] = messageBuffer[src];

                dest++;
            }

            switch(messageBuffer[2]) //Check the command we received
            {

                case 0: //ID request

                    if(bufferPos != 5) //Malformed message?
                        printf("ERR_UNKNOWN_MSG\n");
                    else
                        printf("LOGIC_ANALYZER_V1_0\n"); //Our ID

                    break;

                case 1: //Capture request
                    
                    req = (CAPTURE_REQUEST*)&messageBuffer[3]; //Get the request pointer
                    
                    bool started = false;

                    if(req->triggerType == 1) //Start complex trigger capture
                        started = startCaptureComplex(req->frequency, req->preSamples, req->postSamples, (uint8_t*)&req->channels, req->channelCount, req->trigger, req->count, req->triggerValue);
                    else if(req->triggerType == 2) //start fast trigger capture
                        started = startCaptureFast(req->frequency, req->preSamples, req->postSamples, (uint8_t*)&req->channels, req->channelCount, req->trigger, req->count, req->triggerValue);
                    else //Start simple trigger capture
                        started = startCaptureSimple(req->frequency, req->preSamples, req->postSamples, (uint8_t*)&req->channels, req->channelCount, req->trigger, req->inverted);
                    
                    if(started) //If started successfully inform to the host
                    {
                        printf("CAPTURE_STARTED\n");
                        capturing = true;
                    }
                    else
                        printf("CAPTURE_ERROR\n"); //Else notify the error

                    break;
                
                default:

                    printf("ERR_UNKNOWN_MSG\n"); //Unknown message
                    break;

            }

            bufferPos = 0; //Reset buffer position
        }
    }

    //PROTOCOL EXPLAINED:
    //
    //The protocol is very basic, it receives binary frames and sends strings terminated by a carriage return.
    //
    //Each binary frame has a start and an end condition, being these two secuences of two bytes:
    // start condition: 0x55 0xAA
    // stop condition: 0xAA 0x55
    //
    //This kind of framing can cause problems if the packets contain the frame condition bytes, there needs to be implemented
    //a scape character to avoid this.The char 0xF0 is used as escape character. Escaping is done by XOR'ing the scape character 
    //with the scaped char. For example, if we need to send 0xAA we would send { 0xF0, 0x5A }, which is 0xAA XOR 0xF0 = 0x5A. 
    //In case of sending the scape char we would send { 0xF0, 0x00 }.
    //
    //Inside each frame we have a command byte and additional data. Based on the command a binary struct will be deserialized
    //from the buffer. Right now the protocol has only two commands: ID request and capture request. ID request does not
    //have any data, but the capture request has a CAPTURE_REQUEST struct as data.
}

int main()
{
    //Overclock Powerrrr!
    set_sys_clock_khz(200000, true);

    //Initialize USB stdio
    stdio_init_all();

    //A bit of delay, if the program tries to send data before Windows has identified the device it may crash
    sleep_ms(1000);

    //Clear message buffer
    memset(messageBuffer, 0, 128);

    //Configure led
    gpio_init(LED_IO);
    gpio_set_dir(LED_IO, GPIO_OUT);

    while(1)
    {
        //Led ON
        gpio_put(LED_IO, 1); // Set pin 25 to high

        //Are we capturing?
        if(capturing)
        {
            //Is the PIO units still working?
            if(!IsCapturing())
            {
                //Retrieve the capture buffer and get info about it.
                uint32_t length, first;
                uint8_t* buffer = (uint8_t*)GetBuffer(&length, &first);

                //Send the data to the host
                uint8_t* lengthPointer = (uint8_t*)&length;

                //Send capture length
                sleep_ms(100);

                putchar_raw(lengthPointer[0]);
                putchar_raw(lengthPointer[1]);
                putchar_raw(lengthPointer[2]);
                putchar_raw(lengthPointer[3]);

                sleep_ms(100);

                //Tanslate sample numbers to byte indexes, makes easier to send data
                length *= 4;
                first *= 4;

                //Send the samples
                for(int buc = 0; buc < length; buc++)
                {
                    putchar_raw(buffer[first++]);

                    if(first >= 32768 * 4)
                        first = 0;
                }

                //Done!
                capturing = false;
            }
            else
            {
                gpio_put(LED_IO, 0);
                sleep_ms(100);

                //Check for cancel
                uint data = getchar_timeout_us(0);

                //Any char except timeout is considered a cancel request
                if(data != PICO_ERROR_TIMEOUT)
                {
                    //Stop capture
                    stopCapture();
                    capturing = false;
                }
                else
                {
                    gpio_put(LED_IO, 1);
                    sleep_ms(100);
                }
            }
        }
        else
            processInput(); //Read USB data

        gpio_put(LED_IO, 0); // Set pin 25 to low
    }

    return 0;
}
