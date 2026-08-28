#ifndef __LOGICANALYZER_BOARD_SETTINGS__

    #define __LOGICANALYZER_BOARD_SETTINGS__

    #include "pico/stdlib.h"
    //#include "LogicAnalyzer_Build_Settings.h"

    //Board definitions

    //This defines the name sent to the software
    //#define BOARD_NAME "PICO"

    //If defined the device supports complex, fast and external triggers
    //#define SUPPORTS_COMPLEX_TRIGGER
    
    //Stablishes the channel base GPIO
    //#define INPUT_PIN_BASE 2
    
    //Complex/fast/ext trigger output pin
    //#define COMPLEX_TRIGGER_OUT_PIN 0
    
    //Complex/fast/ext trigger input pin
    //#define COMPLEX_TRIGGER_IN_PIN 1
    
    //If defined, the onboard led is a led connected to a GPIO
    //#define GPIO_LED
    
    //If defined, the onboard led is a led connected to a CYGW module (for the Pico W)
    //#define CYGW_LED
    
    //If defined, the onboard led is a RGB led connected to a GPIO
    //#define WS2812_LED
    
    //If defined, the board has no LED
    //#define NO_LED
    
    //Defines the used GPIO used for the GPIO and WS2812 led types
    //#define LED_IO 25
    
    //If defined enables the Pico W WiFi module
    //#define USE_CYGW_WIFI
    
    //Defines the pin map for the PIO
    //Include ALWAYS an entry for the COMPLEX_TRIGGER_IN_PIN even if not used, you can repeat a pin if needed
    //If COMPLEX_TRIGGER is supported remember to set the first 16 channels to be consecutive
    //#define PIN_MAP {2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,26,27,28,COMPLEX_TRIGGER_IN_PIN}
    
    //Defines the maximum capture buffer size
    //#define CAPTURE_BUFFER_SIZE (128 * 1024)
    
    //Defines the maximum number of channels
    //#define MAX_CHANNELS 24
    
    //Defines the maximum frequency for the capture in normal mode
    //#define MAX_FREQ 200000000
    
    //Defines the maximum frequency for the capture in blast mode
    //#define MAX_BLAST_FREQ 400000000
    
    //If the board supports TURBO mode (400Mhz overclock) then you can define two sets of frequencies using
    //#ifdef TURBO_MODE / #else / #endif
    
    #if defined (BUILD_PICO)

        #define BOARD_NAME "PICO"
        #define SUPPORTS_COMPLEX_TRIGGER
        #define INPUT_PIN_BASE 2
        #define COMPLEX_TRIGGER_OUT_PIN 0
        #define COMPLEX_TRIGGER_IN_PIN 1
        #define GPIO_LED
        #define LED_IO 25
        #define PIN_MAP {2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,26,27,28,COMPLEX_TRIGGER_IN_PIN}

        #ifdef TURBO_MODE
            #define MAX_FREQ 200000000
            #define MAX_BLAST_FREQ 400000000
        #else
            #define MAX_FREQ 100000000
            #define MAX_BLAST_FREQ 200000000
        #endif
        #define CAPTURE_BUFFER_SIZE (128 * 1024)
        #define MAX_CHANNELS 24

    #elif defined (BUILD_PICO_2)

        #define BOARD_NAME "PICO_2"
        #define SUPPORTS_COMPLEX_TRIGGER
        #define INPUT_PIN_BASE 2
        #define COMPLEX_TRIGGER_OUT_PIN 0
        #define COMPLEX_TRIGGER_IN_PIN 1
        #define GPIO_LED
        #define LED_IO 25
        #define PIN_MAP {2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,26,27,28,COMPLEX_TRIGGER_IN_PIN}

        #ifdef TURBO_MODE
            #define MAX_FREQ 200000000
            #define MAX_BLAST_FREQ 400000000
        #else
            #define MAX_FREQ 100000000
            #define MAX_BLAST_FREQ 200000000
        #endif
        #define CAPTURE_BUFFER_SIZE (128 * 3 * 1024)
        #define MAX_CHANNELS 24

    #elif defined (BUILD_PICO_W)

        #define BOARD_NAME "W"
        #define SUPPORTS_COMPLEX_TRIGGER
        #define INPUT_PIN_BASE 2
        #define COMPLEX_TRIGGER_OUT_PIN 0
        #define COMPLEX_TRIGGER_IN_PIN 1
        #define CYGW_LED
        #define PIN_MAP {2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,26,27,28,COMPLEX_TRIGGER_IN_PIN}

        #define MAX_FREQ 100000000
        #define MAX_BLAST_FREQ 200000000
        #define CAPTURE_BUFFER_SIZE (128 * 1024)
        #define MAX_CHANNELS 24

    #elif defined (BUILD_PICO_W_WIFI)

        #define BOARD_NAME "WIFI"
        #define SUPPORTS_COMPLEX_TRIGGER
        #define INPUT_PIN_BASE 2
        #define COMPLEX_TRIGGER_OUT_PIN 0
        #define COMPLEX_TRIGGER_IN_PIN 1
        #define CYGW_LED
        #define USE_CYGW_WIFI
        #define PIN_MAP {2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,26,27,28,COMPLEX_TRIGGER_IN_PIN}
        #define MAX_FREQ 100000000
        #define MAX_BLAST_FREQ 200000000
        #define CAPTURE_BUFFER_SIZE (128 * 1024)
        #define MAX_CHANNELS 24
        
    #elif defined (BUILD_PICO_2_W)

        #define BOARD_NAME "2_W"
        #define SUPPORTS_COMPLEX_TRIGGER
        #define INPUT_PIN_BASE 2
        #define COMPLEX_TRIGGER_OUT_PIN 0
        #define COMPLEX_TRIGGER_IN_PIN 1
        #define CYGW_LED
        #define PIN_MAP {2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,26,27,28,COMPLEX_TRIGGER_IN_PIN}

        #define MAX_FREQ 100000000
        #define MAX_BLAST_FREQ 200000000
        #define CAPTURE_BUFFER_SIZE (128 * 3 * 1024)
        #define MAX_CHANNELS 24

    #elif defined (BUILD_PICO_2_W_WIFI)

        #define BOARD_NAME "2_WIFI"
        #define SUPPORTS_COMPLEX_TRIGGER
        #define INPUT_PIN_BASE 2
        #define COMPLEX_TRIGGER_OUT_PIN 0
        #define COMPLEX_TRIGGER_IN_PIN 1
        #define CYGW_LED
        #define USE_CYGW_WIFI
        #define PIN_MAP {2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,26,27,28,COMPLEX_TRIGGER_IN_PIN}
        #define MAX_FREQ 100000000
        #define MAX_BLAST_FREQ 200000000
        #define CAPTURE_BUFFER_SIZE (128 * 3 * 1024)
        #define MAX_CHANNELS 24

    #elif defined (BUILD_ZERO)

        #define BOARD_NAME "ZERO"
        #define SUPPORTS_COMPLEX_TRIGGER
        #define INPUT_PIN_BASE 0
        #define COMPLEX_TRIGGER_OUT_PIN 17
        #define COMPLEX_TRIGGER_IN_PIN 18
        #define WS2812_LED
        #define LED_IO 16
        #define PIN_MAP {0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,26,27,28,29,22,23,24,25,COMPLEX_TRIGGER_IN_PIN}

        #ifdef TURBO_MODE
            #define MAX_FREQ 200000000
            #define MAX_BLAST_FREQ 400000000
        #else
            #define MAX_FREQ 100000000
            #define MAX_BLAST_FREQ 200000000
        #endif
        #define CAPTURE_BUFFER_SIZE (128 * 1024)
        #define MAX_CHANNELS 24
        
    #elif defined (BUILD_INTERCEPTOR)

        #define BOARD_NAME "INTERCEPTOR"
        #define SUPPORTS_COMPLEX_TRIGGER
        #define INPUT_PIN_BASE 2
        #define COMPLEX_TRIGGER_OUT_PIN 0
        #define COMPLEX_TRIGGER_IN_PIN 1
        #define NO_LED
        #define PIN_MAP {6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,2,3,4,5,COMPLEX_TRIGGER_IN_PIN}

        #ifdef TURBO_MODE
            #define MAX_FREQ 200000000
            #define MAX_BLAST_FREQ 400000000
        #else
            #define MAX_FREQ 100000000
            #define MAX_BLAST_FREQ 200000000
        #endif
        #define CAPTURE_BUFFER_SIZE (128 * 1024)
        #define MAX_CHANNELS 28

    #endif

#endif