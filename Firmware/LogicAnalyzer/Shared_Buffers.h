#include "LogicAnalyzer_Board_Settings.h"
#ifdef USE_CYGW_WIFI
    #ifndef __SHARED_BUFFERS__
        #define __SHARED_BUFFERS__
        #include "LogicAnalyzer_Structs.h"
        #include "Event_Machine.h"
        #include "hardware/flash.h"

        #define FLASH_SETTINGS_OFFSET ((2048 * 1024) - FLASH_SECTOR_SIZE)
        #define FLASH_SETTINGS_ADDRESS (XIP_BASE + FLASH_SETTINGS_OFFSET)

        volatile extern WIFI_SETTINGS wifiSettings;
        extern EVENT_MACHINE wifiToFrontend;
        extern EVENT_MACHINE frontendToWifi;
    #endif
#endif