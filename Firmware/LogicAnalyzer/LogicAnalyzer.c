#include "LogicAnalyzer_Board_Settings.h"

#include <stdio.h>
#include <string.h>
#include "pico/stdlib.h"
#include "hardware/dma.h"
#include "hardware/pio.h"
#include "hardware/clocks.h"
#include "hardware/flash.h"
#include "pico/multicore.h"
#include "LogicAnalyzer.pio.h"
#include "LogicAnalyzer_Structs.h"
#include "tusb.h"

#ifdef WS2812_LED
    #include "LogicAnalyzer_W2812.h"
#endif

#if defined (CYGW_LED) || defined(USE_CYGW_WIFI)

    #include "pico/cyw43_arch.h"

    #ifdef USE_CYGW_WIFI

        #include "Event_Machine.h"
        #include "Shared_Buffers.h"
        #include "LogicAnalyzer_WiFi.h"
        #include "hardware/regs/usb.h"
        #include "hardware/structs/usb.h"

        bool usbDisabled = false;
        bool cywReady = false;
        bool skipWiFiData = false;
        bool dataFromWiFi = false;
        EVENT_FROM_WIFI wifiEventBuffer;
        WIFI_SETTINGS_REQUEST* wReq;

        #define MULTICORE_LOCKOUT_TIMEOUT (uint64_t)10 * 365 * 24 * 60 * 60 * 1000 * 1000

    #endif

#endif

#if defined (GPIO_LED)
    #define INIT_LED() {\
                            gpio_init(LED_IO); \
                            gpio_set_dir(LED_IO, GPIO_OUT); \
                        }
    #define LED_ON() gpio_put(LED_IO, 1)
    #define LED_OFF() gpio_put(LED_IO, 0)
#elif defined (CYGW_LED)

    #define INIT_LED() { }

    #ifdef USE_CYGW_WIFI
        #define LED_ON() {\
        EVENT_FROM_FRONTEND lonEvt;\
        lonEvt.event = LED_ON;\
        event_push(&frontendToWifi, &lonEvt);\
        }

        #define LED_OFF() {\
        EVENT_FROM_FRONTEND loffEvt;\
        loffEvt.event = LED_OFF;\
        event_push(&frontendToWifi, &loffEvt);\
        }
    #else
        #define LED_ON() cyw43_arch_gpio_put(CYW43_WL_GPIO_LED_PIN, 1)
        #define LED_OFF() cyw43_arch_gpio_put(CYW43_WL_GPIO_LED_PIN, 0)
    #endif

#elif defined (WS2812_LED)
    #define INIT_LED() init_rgb()
    #define LED_ON() send_rgb(0,32,0)
    #define LED_OFF() send_rgb(0,0,32)
#endif

//Buffer used to store received data
uint8_t messageBuffer[128];
//Position in the buffer
uint8_t bufferPos = 0;
//Capture status
bool capturing = false;
//Capture request pointer
CAPTURE_REQUEST* req;

#ifdef USE_CYGW_WIFI

/// @brief Stores a new WiFi configuration in the flash of the device
/// @param settings Settings to store
void storeSettings(WIFI_SETTINGS* settings)
{
    uint8_t buffer[FLASH_PAGE_SIZE];
    memcpy(buffer, settings, sizeof(WIFI_SETTINGS));
    //multicore_lockout_start_blocking ();
    multicore_lockout_start_timeout_us(MULTICORE_LOCKOUT_TIMEOUT);

    uint32_t intStatus = save_and_disable_interrupts();

    flash_range_erase(FLASH_SETTINGS_OFFSET, FLASH_SECTOR_SIZE);

    for(int buc = 0; buc < 1000; buc++)
    {
        asm("nop");
        asm("nop");
        asm("nop");
        asm("nop");
        asm("nop");
    }

    flash_range_program(FLASH_SETTINGS_OFFSET, buffer, FLASH_PAGE_SIZE);

    for(int buc = 0; buc < 1000; buc++)
    {
        asm("nop");
        asm("nop");
        asm("nop");
        asm("nop");
        asm("nop");
    }

    restore_interrupts(intStatus);

    bool unlocked = false;

    do {
        unlocked = multicore_lockout_end_timeout_us(MULTICORE_LOCKOUT_TIMEOUT);
    } while(!unlocked);

    sleep_ms(500);

}

#endif

/// @brief Sends a response message to the host application in string mode
/// @param response The message to be sent (null terminated)
/// @param toWiFi If true the message is sent to a WiFi endpoint, else to the USB connection through STDIO
void sendResponse(const char* response, bool toWiFi)
{
    #ifdef USE_CYGW_WIFI
    if(toWiFi)
    {
        EVENT_FROM_FRONTEND evt;
        evt.event = SEND_DATA;
        evt.dataLength = strlen(response);
        memset(evt.data, 0, 32);
        memcpy(evt.data, response, evt.dataLength);
        event_push(&frontendToWifi, &evt);
    }
    else
    #endif
        printf(response);
}

/// @brief Transfer a buffer of data through USB using the TinyUSB CDC functions
/// @param data Buffer of data to transfer
/// @param len Length of the buffer
void cdc_transfer(unsigned char* data, int len)
{

    int left = len;
    int pos = 0;

    while(left > 0)
    {
        int avail = (int) tud_cdc_write_available();

        if(avail > left)
            avail = left;

        if(avail)
        {
            int transferred = (int) tud_cdc_write(data + pos, avail);
            tud_task();
            tud_cdc_write_flush();
            
            pos += transferred;
            left -= transferred;
        }
        else
        {
            tud_task();
            tud_cdc_write_flush();
            if (!tud_cdc_connected())
                break;
        }
    }
}

/// @brief Processes data received from the host application
/// @param data The received data
/// @param length Length of the data
/// @param fromWiFi If true the message comes from a WiFi connection
void processData(uint8_t* data, uint length, bool fromWiFi)
{
    for(uint pos = 0; pos < length; pos++)
    {
        //Store char in buffer and increment position
        messageBuffer[bufferPos++] = data[pos];
        
        //If we have stored the first byte and it is not 0x55 restart reception
        if(bufferPos == 1 && messageBuffer[0] != 0x55)
            bufferPos = 0;
        else if(bufferPos == 2 && messageBuffer[1] != 0xAA) //If we have stored the second byte and it is not 0xAA restart reception
            bufferPos = 0;
        else if(bufferPos >= 256) //Have we overflowed the buffer? then inform to the host and restart reception
        {
            sendResponse("ERR_MSG_OVERFLOW\n", fromWiFi);
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
                            sendResponse("ERR_UNKNOWN_MSG\n", fromWiFi);
                        else
                            sendResponse("LOGIC_ANALYZER_"BOARD_NAME"_"FIRMWARE_VERSION"\n", fromWiFi);
                        break;

                    case 1: //Capture request
                        
                        req = (CAPTURE_REQUEST*)&messageBuffer[3]; //Get the request pointer
                        
                        bool started = false;

                        #ifdef SUPPORTS_COMPLEX_TRIGGER

                            if(req->triggerType == 1) //Start complex trigger capture
                                started = startCaptureComplex(req->frequency, req->preSamples, req->postSamples, (uint8_t*)&req->channels, req->channelCount, req->trigger, req->count, req->triggerValue, req->captureMode);
                            else if(req->triggerType == 2) //start fast trigger capture
                                started = startCaptureFast(req->frequency, req->preSamples, req->postSamples, (uint8_t*)&req->channels, req->channelCount, req->trigger, req->count, req->triggerValue, req->captureMode);
                            else //Start simple trigger capture
                                started = startCaptureSimple(req->frequency, req->preSamples, req->postSamples, req->loopCount, (uint8_t*)&req->channels, req->channelCount, req->trigger, req->inverted, req->captureMode);
                        
                        #else

                            if(req->triggerType == 1 || req->triggerType == 2)
                            {
                                sendResponse("CAPTURE_ERROR\n", fromWiFi);
                                break;
                            }
                            else
                                started = startCaptureSimple(req->frequency, req->preSamples, req->postSamples, req->loopCount, (uint8_t*)&req->channels, req->channelCount, req->trigger, req->inverted, req->captureMode);
                        
                        #endif

                        if(started) //If started successfully inform to the host
                        {
                            sendResponse("CAPTURE_STARTED\n", fromWiFi);
                            capturing = true;
                        }
                        else
                            sendResponse("CAPTURE_ERROR\n", fromWiFi); //Else notify the error

                        break;
                    
                    #ifdef USE_CYGW_WIFI

                    case 2: //Update WiFi settings

                        wReq = (WIFI_SETTINGS_REQUEST*)&messageBuffer[3];
                        WIFI_SETTINGS settings;
                        memcpy(settings.apName, wReq->apName, 33);
                        memcpy(settings.passwd, wReq->passwd, 64);
                        memcpy(settings.ipAddress, wReq->ipAddress, 16);
                        settings.port = wReq->port;

                        for(int buc = 0; buc < 33; buc++)
                            settings.checksum += settings.apName[buc];

                        for(int buc = 0; buc < 64; buc++)
                            settings.checksum += settings.passwd[buc];

                        for(int buc = 0; buc < 16; buc++)
                            settings.checksum += settings.ipAddress[buc];

                        settings.checksum += settings.port;

                        settings.checksum += 0x0f0f;

                        storeSettings(&settings);

                        wifiSettings = settings;

                        EVENT_FROM_FRONTEND evt;
                        evt.event = CONFIG_RECEIVED;
                        event_push(&frontendToWifi, &evt);

                        sendResponse("SETTINGS_SAVED\n", fromWiFi);

                        break;

                    case 3: //Read power status

                        if(!fromWiFi)
                            sendResponse("ERR_UNSUPPORTED\n", fromWiFi);
                        else 
                        {
                            EVENT_FROM_FRONTEND powerEvent;
                            powerEvent.event = GET_POWER_STATUS;
                            event_push(&frontendToWifi, &powerEvent);
                        }
                        
                        break;

                    #else

                    case 2:
                    case 3:

                        sendResponse("ERR_UNSUPPORTED\n", fromWiFi);
                        break;

                    #endif

                    default:

                        sendResponse("ERR_UNKNOWN_MSG\n", fromWiFi); //Unknown message
                        break;

                }

                bufferPos = 0; //Reset buffer position
            }
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

/// @brief Receive and process USB data from the host application
/// @param skipProcessing If true the received data is not processed (used for cleanup)
/// @return True if anything is received, false if not
bool processUSBInput(bool skipProcessing)
{
    //Try to get char
    uint data = getchar_timeout_us(0);

    //Timeout? Then leave
    if(data == PICO_ERROR_TIMEOUT)
        return false;

    uint8_t filteredData = (uint8_t)data;

    if(!skipProcessing)
        processData(&filteredData, 1, false);

    return true;

}

#ifdef USE_CYGW_WIFI

/// @brief Purges any pending data in the USB input
void purgeUSBData()
{
    while(getchar_timeout_us(0) != PICO_ERROR_TIMEOUT);
}

/// @brief Send a string response with the power status
/// @param status Status received from the WiFi core
void sendPowerStatus(POWER_STATUS* status)
{
    char buffer[32];
    memset(buffer, 0, 32);
    int len = sprintf(buffer, "%.2f", status->vsysVoltage);
    buffer[len++] = '_';
    buffer[len++] = status->vbusConnected ? '1' : '0';
    buffer[len] = '\n';
    sendResponse(buffer, true);
}

/// @brief Callback for the WiFi event queue
/// @param event Received event
void wifiEvent(void* event)
{
    EVENT_FROM_WIFI* wEvent = (EVENT_FROM_WIFI*)event;

    switch(wEvent->event)
    {
        case CYW_READY:
            cywReady = true;
            break;
        case CONNECTED:
            usbDisabled = true;
            //disableUSB();
            break;
        case DISCONNECTED:
            usbDisabled = false;
            purgeUSBData();
            //enableUSB();
            break;
        case DATA_RECEIVED:
            if(skipWiFiData)
                dataFromWiFi = true;
            else
                processData(wEvent->data, wEvent->dataLength, true);
            break;
        case POWER_STATUS_DATA:
            {
                POWER_STATUS status;
                memcpy(&status, wEvent->data, sizeof(POWER_STATUS));
                sendPowerStatus(&status);
            }
            break;
    }
}

/// @brief Receives and processes input from the host application (when connected through WiFi)
/// @param skipProcessing /// @param skipProcessing If true the received data is not processed (used for cleanup)
/// @return True if anything is received, false if not
bool processWiFiInput(bool skipProcessing)
{
    bool res = event_has_events(&wifiToFrontend);

    if(skipProcessing)
    {
        skipWiFiData = true;
        dataFromWiFi = false;
    }

    event_process_queue(&wifiToFrontend, &wifiEventBuffer, 8);

    skipWiFiData = false;    
    
    return dataFromWiFi;
}

#endif

/// @brief Process input data from the host application if it is available
void processInput()
{
    #ifdef USE_CYGW_WIFI
        if(!usbDisabled)
            processUSBInput(false);

        processWiFiInput(false);
    #else
        processUSBInput(false);
    #endif
}

/// @brief Processes input data from the host application to check if there is any cancel capture request
/// @return True if there was input data
bool processCancel()
{
    #ifdef USE_CYGW_WIFI
        if(!usbDisabled)
            if(processUSBInput(true))
                return true;

        return processWiFiInput(true);
    #else
        return processUSBInput(true);
    #endif
}

/// @brief Main app loop
/// @return Exit code
int main()
{
    //Overclock Powerrrr!
    set_sys_clock_khz(200000, true);

    //Initialize USB stdio
    stdio_init_all();

    #if defined (BUILD_PICO_W)
        cyw43_arch_init();
    #elif defined (BUILD_PICO_W_WIFI)
        event_machine_init(&wifiToFrontend, wifiEvent, sizeof(EVENT_FROM_WIFI), 8);
            multicore_launch_core1(runWiFiCore);
            while(!cywReady)
                event_process_queue(&wifiToFrontend, &wifiEventBuffer, 1);
    #endif

    //A bit of delay, if the program tries to send data before Windows has identified the device it may crash
    sleep_ms(1000);

    //Clear message buffer
    memset(messageBuffer, 0, 128);

    //Configure led
    INIT_LED();
    LED_ON();

    while(1)
    {
        //Are we capturing?
        if(capturing)
        {
            //Is the PIO units still working?
            if(!IsCapturing())
            {
                //Retrieve the capture buffer and get info about it.
                uint32_t length, first;
                CHANNEL_MODE mode;
                uint8_t* buffer = GetBuffer(&length, &first, &mode);

                //Send the data to the host
                uint8_t* lengthPointer = (uint8_t*)&length;

                //Send capture length
                sleep_ms(100);

                #ifdef USE_CYGW_WIFI

                    if(usbDisabled)
                    {
                        EVENT_FROM_FRONTEND evt;
                        evt.event = SEND_DATA;
                        evt.dataLength = 4;
                        memcpy(evt.data, lengthPointer, 4);
                        event_push(&frontendToWifi, &evt);
                    }
                    else
                        cdc_transfer(lengthPointer, 4);

                #else
                    cdc_transfer(lengthPointer, 4);
                #endif

                sleep_ms(100);

                //Tanslate sample numbers to byte indexes, makes easier to send data
                switch(mode)
                {
                    case MODE_16_CHANNEL:
                        length *= 2;
                        first *= 2;
                        break;
                    case MODE_24_CHANNEL:
                        length *= 4;
                        first *= 4;
                        break;
                }

                #ifdef USE_CYGW_WIFI

                    //Send the samples
                    if(usbDisabled)
                    {
                        EVENT_FROM_FRONTEND evt;
                        evt.event = SEND_DATA;

                        int pos = 0;
                        int filledData;
                        while(pos < length)
                        {
                            filledData = 0;
                            while(pos < length && filledData < 32)
                            {
                                evt.data[filledData] = buffer[first++];

                                if(first >= 131072)
                                    first = 0;

                                pos++;
                                filledData++;
                            }

                            evt.dataLength = filledData;
                            event_push(&frontendToWifi, &evt);
                        }
                    }
                    else
                    {
                        if(first + length > CAPTURE_BUFFER_SIZE)
                        {
                            cdc_transfer(buffer + first, CAPTURE_BUFFER_SIZE - first);
                            cdc_transfer(buffer, (first + length) - CAPTURE_BUFFER_SIZE);
                        }
                        else
                            cdc_transfer(buffer + first, length);
                    }
                #else

                    if(first + length > CAPTURE_BUFFER_SIZE)
                    {
                        cdc_transfer(buffer + first, CAPTURE_BUFFER_SIZE - first);
                        cdc_transfer(buffer, (first + length) - CAPTURE_BUFFER_SIZE);
                    }
                    else
                        cdc_transfer(buffer + first, length);

                #endif
                //Done!
                capturing = false;
            }
            else
            {
                LED_OFF();
                sleep_ms(1000);

                //Check for cancel request
                if(processCancel())
                {
                    //Stop capture
                    stopCapture();
                    capturing = false;
                    LED_ON();
                }
                else
                {
                    LED_ON();
                    #ifdef SUPPORTS_COMPLEX_TRIGGER
                    check_fast_interrupt();
                    #endif
                    sleep_ms(1000);
                }
            }
        }
        else
            processInput(); //Read incomming data
    }

    return 0;
}