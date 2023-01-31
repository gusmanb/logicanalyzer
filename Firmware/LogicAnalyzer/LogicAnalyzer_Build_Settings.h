#ifndef __BUILD_SETTINGS__
    #define __BUILD_SETTINGS__

    //Configure the build settings

    //#define BUILD_PICO_W
    //#define ENABLE_WIFI

    /**
     * WARNING! Ensure you choose the correct cyw library in the CMakeLists.txt
     * 
     * It includes instructions on what to do
     * 
     */

    //Do not touch, simple check for sanity

    #ifdef ENABLE_WIFI
        #ifndef BUILD_PICO_W
            #error "WiFi can only be enabled if the build is for the pico W"
        #endif
    #endif

#endif


