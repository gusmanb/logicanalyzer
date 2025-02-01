#include "LogicAnalyzer_Board_Settings.h"

#ifdef WS2812_LED

    #ifndef __LOGICANALYZER_W2812__

        #define __LOGICANALYZER_W2812__

        void send_rgb(uint8_t r, uint8_t g, uint8_t b);
        void init_rgb();

    #endif

#endif