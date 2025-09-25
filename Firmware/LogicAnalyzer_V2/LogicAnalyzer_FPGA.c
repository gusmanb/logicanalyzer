#include "LogicAnalyzer_FPGA.h"

#ifdef BUILD_PICO_ICE

#include "hardware/gpio.h"
#include "hardware/pio.h"
#include "hardware/clocks.h"
#include "pico/time.h"
#include "fpga_clock.pio.h"

// PIO instance for FPGA clock generation (avoid conflicts with logic analyzer)
static PIO fpga_pio = pio1;
static int fpga_sm = -1;
static uint fpga_clock_offset = 0;

// Use generated PIO program (fpga_clock_program)

bool fpga_init(void)
{
    // Initialize all FPGA control pins
    
    // Configure ICE_RESET pin (active-low) - start with FPGA in reset
    gpio_init(PIN_FPGA_CRESETN);
    gpio_set_dir(PIN_FPGA_CRESETN, GPIO_OUT);
    gpio_put(PIN_FPGA_CRESETN, 0);  // Hold FPGA in reset initially
    
    // Configure CDONE pin (input, no pulls) - FPGA asserts this when configuration complete
    gpio_init(PIN_FPGA_CDONE);
    gpio_set_dir(PIN_FPGA_CDONE, GPIO_IN);
    gpio_disable_pulls(PIN_FPGA_CDONE);
    
    // Leave sysCONFIG SPI pins high-Z so FPGA can self-configure from flash
    gpio_init(PIN_ICE_SI);  gpio_set_dir(PIN_ICE_SI, GPIO_IN);  gpio_disable_pulls(PIN_ICE_SI);
    gpio_init(PIN_ICE_SO);  gpio_set_dir(PIN_ICE_SO, GPIO_IN);  gpio_disable_pulls(PIN_ICE_SO);
    gpio_init(PIN_ICE_SCK); gpio_set_dir(PIN_ICE_SCK, GPIO_IN); gpio_disable_pulls(PIN_ICE_SCK);
    gpio_init(PIN_ICE_SSN); gpio_set_dir(PIN_ICE_SSN, GPIO_IN); gpio_disable_pulls(PIN_ICE_SSN);
    
    // Ensure PSRAM SS is also high-Z during config
    gpio_init(PIN_RAM_SS); gpio_set_dir(PIN_RAM_SS, GPIO_IN); gpio_disable_pulls(PIN_RAM_SS);
    
    // Configure clock output pin (will be controlled by PIO)
    gpio_init(PIN_CLOCK);
    gpio_set_dir(PIN_CLOCK, GPIO_OUT);
    gpio_put(PIN_CLOCK, 0);  // Start low
    
    // Small delay to ensure pins are stable
    sleep_ms(10);
    
    // Release FPGA from reset to start configuration from flash
    gpio_put(PIN_FPGA_CRESETN, 1);  // This should make GPIO27 go HIGH
    
    // Wait for FPGA configuration to complete (CDONE assertion)
    // Timeout after 1000ms - allow time for flash configuration
    uint32_t timeout_count = 0;
    const uint32_t timeout_limit = 1000; // 1000ms timeout
    
    while (!gpio_get(PIN_FPGA_CDONE) && timeout_count < timeout_limit) {
        sleep_ms(1);
        timeout_count++;
    }
    
    if (timeout_count >= timeout_limit) {
        // FPGA configuration failed - keep reset HIGH and report failure silently
        return false;
    }

    // Start the 10 MHz clock after configuration completes
    if (!fpga_start_clock()) {
        return false;  // Clock generation failed
    }

    return true;
}

bool fpga_start_clock(void)
{
    // Clear any previous program to free space (only our clock on pio1)
    // Note: avoid clearing pio0 which capture uses.
    // Load program
    if (!pio_can_add_program(fpga_pio, &fpga_clock_program)) {
        // try reclaiming a SM and proceed anyway
    }

    fpga_clock_offset = pio_add_program(fpga_pio, &fpga_clock_program);

    // Get a free state machine
    fpga_sm = pio_claim_unused_sm(fpga_pio, true);

    // Configure SM for sideset pin
    pio_sm_config c = fpga_clock_program_get_default_config(fpga_clock_offset);
    sm_config_set_sideset_pins(&c, PIN_CLOCK);

    // Prepare the pin
    pio_gpio_init(fpga_pio, PIN_CLOCK);
    pio_sm_set_consecutive_pindirs(fpga_pio, fpga_sm, PIN_CLOCK, 1, true);

    // Each loop is 2 instructions; with sideset toggling each instr, period = 2 cycles
    // f_out = f_sys / (clkdiv * 2) => clkdiv = f_sys / (f_out*2)
    float system_freq = (float)clock_get_hz(clk_sys);
    float target_freq = 10000000.0f;  // 10 MHz
    float clkdiv = system_freq / (target_freq * 2.0f);
    sm_config_set_clkdiv(&c, clkdiv);

    // Initialize and start SM
    pio_sm_init(fpga_pio, fpga_sm, fpga_clock_offset, &c);
    pio_sm_set_enabled(fpga_pio, fpga_sm, true);

    return true;
}

void fpga_stop_clock(void)
{
    if (fpga_sm >= 0) {
        pio_sm_set_enabled(fpga_pio, fpga_sm, false);
        pio_sm_unclaim(fpga_pio, fpga_sm);
        fpga_sm = -1;
    }
    if (fpga_clock_offset) {
        pio_remove_program(fpga_pio, &fpga_clock_program, fpga_clock_offset);
        fpga_clock_offset = 0;
    }
    
    // Set clock pin low
    gpio_init(PIN_CLOCK);
    gpio_set_dir(PIN_CLOCK, GPIO_OUT);
    gpio_put(PIN_CLOCK, 0);
}

bool fpga_is_configured(void)
{
    return gpio_get(PIN_FPGA_CDONE);
}

void fpga_reset(void)
{
    // Stop clock during reset
    fpga_stop_clock();
    
    // Pull reset low
    gpio_put(PIN_FPGA_CRESETN, 0);
    sleep_ms(10);  // Hold reset for 10ms
    
    // Release reset
    gpio_put(PIN_FPGA_CRESETN, 1);
    
    // Wait for configuration to complete
    uint32_t timeout_count = 0;
    const uint32_t timeout_limit = 100;
    
    while (!gpio_get(PIN_FPGA_CDONE) && timeout_count < timeout_limit) {
        sleep_ms(1);
        timeout_count++;
    }
    
    // Restart clock if configuration succeeded
    if (gpio_get(PIN_FPGA_CDONE)) {
        fpga_start_clock();
    }
}

#endif // BUILD_PICO_ICE