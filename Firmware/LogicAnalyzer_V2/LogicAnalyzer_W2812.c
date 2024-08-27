#include "LogicAnalyzer_Board_Settings.h"

#ifdef WS2812_LED

    #include "pico/stdlib.h"
    #include "LogicAnalyzer_w2812.h"

    inline void delay_cycles4(uint32_t loops)
    {
        __asm__ __volatile__(
            "mov r5, %[input_loops]\r\n"
            "1:\r\n"
            "sub r5, #1\r\n"
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
                delay_cycles4(52);
                gpio_put(LED_IO, false);
                delay_cycles4(25);
            }
            else
            {
                gpio_put(LED_IO, true);
                delay_cycles4(26);
                gpio_put(LED_IO, false);
                delay_cycles4(52);
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