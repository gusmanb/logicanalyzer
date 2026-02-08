#include "LogicAnalyzer_Board_Settings.h"

#ifdef WS2812_LED

    #include "pico/stdlib.h"
    #include "LogicAnalyzer_W2812.h"

    #define LONG_START 52.0 * (MAX_FREQ / 100000000.0)
    #define SHORT_START 26.0 * (MAX_FREQ / 100000000.0)
    #define LONG_END 52.0 * (MAX_FREQ / 100000000.0)
    #define SHORT_END 25.0 * (MAX_FREQ / 100000000.0)

    void __attribute__ ((noinline)) delay_cycles4(uint32_t loops)
    {
        __asm__ __volatile__(
            "mov r0, %[input_loops]\r\n"
            "1:\r\n"
            "sub r0, #1\r\n"
            "bne 1b\r\n"
            :
            : [input_loops] "r" (loops)
        );
    }

    unsigned char reverse_bits(unsigned char b) {
    b = (b & 0xF0) >> 4 | (b & 0x0F) << 4;
    b = (b & 0xCC) >> 2 | (b & 0x33) << 2;
    b = (b & 0xAA) >> 1 | (b & 0x55) << 1;
    return b;
    }

    void send_rgb(uint8_t r, uint8_t g, uint8_t b)
    {
        uint32_t rgb =  reverse_bits(g) | (reverse_bits(r) << 8) | (reverse_bits(b) << 16);

        for(int buc = 0; buc < 24; buc++)
        {
            if(rgb & (1 << buc))
            {
                gpio_put(LED_IO, true);
                delay_cycles4(LONG_START);
                gpio_put(LED_IO, false);
                delay_cycles4(SHORT_END);
            }
            else
            {
                gpio_put(LED_IO, true);
                delay_cycles4(SHORT_START);
                gpio_put(LED_IO, false);
                delay_cycles4(LONG_END);
            }
        }

    }

    void init_rgb()
    {
        gpio_init(LED_IO);
        gpio_set_dir(LED_IO, true);
        gpio_put(LED_IO, true);
        sleep_us(500);
        gpio_put(LED_IO, false);
        sleep_us(500);
        send_rgb(0, 0, 0);
        sleep_ms(500);
        send_rgb(0, 0, 0);
        sleep_ms(500);
    }


#endif
