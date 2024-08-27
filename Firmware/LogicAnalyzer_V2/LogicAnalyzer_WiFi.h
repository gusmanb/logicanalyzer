#include "LogicAnalyzer_Board_Settings.h"

#ifdef USE_CYGW_WIFI

    #ifndef __LOGICANALYZER_WIFI__
        #define __LOGICANALYZER_WIFI__


        typedef enum
        {
            VALIDATE_SETTINGS,
            WAITING_SETTINGS,
            CONNECTING_AP,
            STARTING_TCP_SERVER,
            WAITING_TCP_CLIENT,
            TCP_CLIENT_CONNECTED

        } WIFI_STATE_MACHINE;

        void runWiFiCore();
        bool getVsysState();
    #endif

#endif