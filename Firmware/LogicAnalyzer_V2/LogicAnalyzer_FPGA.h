#ifndef __LOGICANALYZER_FPGA__
#define __LOGICANALYZER_FPGA__

#include "pico/stdlib.h"
#include "LogicAnalyzer_Board_Settings.h"

#ifdef BUILD_PICO_ICE

/**
 * @brief Initialize the FPGA subsystem for pico-ice
 * 
 * This function performs the complete FPGA initialization sequence:
 * 1. Configure all FPGA control pins
 * 2. Release ICE_RESET to start FPGA configuration from flash
 * 3. Wait for CDONE to be asserted
 * 4. Start the 10MHz clock generation using PIO
 * 
 * @return true if initialization successful, false if failed
 */
bool fpga_init(void);

/**
 * @brief Start the 10MHz clock output to the FPGA
 * 
 * Uses PIO to generate a precise 10MHz clock signal on PIN_CLOCK (GPIO24).
 * The frequency can be adjusted by modifying the divider calculation.
 * 
 * @return true if clock started successfully, false if failed
 */
bool fpga_start_clock(void);

/**
 * @brief Stop the FPGA clock output
 * 
 * Stops the PIO clock generation and sets the clock pin to low.
 */
void fpga_stop_clock(void);

/**
 * @brief Check if FPGA configuration is complete
 * 
 * @return true if CDONE is asserted (FPGA configured), false otherwise
 */
bool fpga_is_configured(void);

/**
 * @brief Reset the FPGA
 * 
 * Pulls ICE_RESET low, waits briefly, then releases it to restart
 * the FPGA configuration process.
 */
void fpga_reset(void);

#endif // BUILD_PICO_ICE

#endif // __LOGICANALYZER_FPGA__