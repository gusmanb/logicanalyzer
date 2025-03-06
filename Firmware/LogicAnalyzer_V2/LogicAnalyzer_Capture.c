#include "LogicAnalyzer_Board_Settings.h"
#include "LogicAnalyzer_Capture.h"
#include "hardware/gpio.h"
#include "hardware/dma.h"
#include "hardware/irq.h"
#include "hardware/clocks.h"
#include "string.h"
#include "hardware/sync.h"
#include "hardware/exception.h"
#include "hardware/structs/syscfg.h"
#include "hardware/structs/systick.h"
#include "hardware/structs/bus_ctrl.h"
#include "LogicAnalyzer.pio.h"

//Static variables for the PIO programs
static PIO capturePIO;
static PIO triggerPIO;

static uint sm_Capture;
static uint captureOffset;

static uint sm_Trigger;
static uint triggerOffset;

//Static variables for DMA channels
static uint32_t dmaPingPong0;
static uint32_t dmaPingPong1;
static uint32_t transferCount;

//Static information of the last capture
static uint8_t lastCapturePins[MAX_CHANNELS];       //List of captured pins
static uint8_t lastCapturePinCount;                 //Count of captured pins
static uint32_t lastTriggerCapture;                 //Moment where the trigger happened inside the circular pre buffer
static uint32_t lastPreSize;                        //Pre-trigger buffer size
static uint32_t lastPostSize;                       //Post-trigger buffer size
static uint32_t lastLoopCount;                      //Number of loops
static bool lastTriggerInverted;                    //Inverted?
static uint8_t lastTriggerPin;
static uint32_t lastStartPosition;
static bool lastCaptureComplexFast;
static uint8_t lastCaptureType;
static uint8_t lastTriggerPinBase;
static uint32_t lastTriggerPinCount;
static uint32_t lastTail;
static CHANNEL_MODE lastCaptureMode = MODE_8_CHANNEL;

//Static information of the current capture
static bool captureFinished;
static bool captureProcessed;

//NEW//
static volatile uint32_t loopTimestamp[256];
static volatile uint8_t timestampIndex;
static volatile uint8_t systickLoops;
static exception_handler_t oldNMIHandler;
static exception_handler_t oldSysTickHandler;

//Pin mapping, used to map the channels to the PIO program
//COMPLEX_TRIGGER_IN_PIN is added at the end of the array to support the chained mode
//Add it at the end even if not used, you can repeat a pin in the array if needed
#if defined (BUILD_PICO)
    const uint8_t pinMap[] = {2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,26,27,28,COMPLEX_TRIGGER_IN_PIN};  
#elif defined (BUILD_PICO_2)
    const uint8_t pinMap[] = {2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,26,27,28,COMPLEX_TRIGGER_IN_PIN};  
#elif defined (BUILD_PICO_W)
    const uint8_t pinMap[] = {2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,26,27,28,COMPLEX_TRIGGER_IN_PIN};
#elif defined (BUILD_PICO_W_WIFI)
    const uint8_t pinMap[] = {2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,26,27,28,COMPLEX_TRIGGER_IN_PIN};
#elif defined (BUILD_ZERO)
    const uint8_t pinMap[] = {0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,26,27,28,29,22,23,24,25,COMPLEX_TRIGGER_IN_PIN};
#endif

//Main capture buffer, aligned at a dword boundary.
static uint8_t captureBuffer[CAPTURE_BUFFER_SIZE] __attribute__((aligned(4)));

#define CAPTURE_TYPE_SIMPLE 0
#define CAPTURE_TYPE_COMPLEX 1
#define CAPTURE_TYPE_FAST 2
#define CAPTURE_TYPE_BLAST 3

//-----------------------------------------------------------------------------
//--------------Complex trigger PIO program------------------------------------
//-----------------------------------------------------------------------------
#ifdef SUPPORTS_COMPLEX_TRIGGER

#define COMPLEX_TRIGGER_wrap_target 0
#define COMPLEX_TRIGGER_wrap 8

uint16_t COMPLEX_TRIGGER_program_instructions[] = {
            //     .wrap_target
    0x80a0, //  0: pull   block                      
    0x6020, //  1: out    x, 32                      
    0xe000, //  2: set    pins, 0                    
    0xc007, //  3: irq    nowait 7                   
    0xa0e0, //  4: mov    osr, pins                  
    0x6044, //  5: out    y, 4                       
    0x00a4, //  6: jmp    x != y, 4                  
    0xe001, //  7: set    pins, 1                    
    0x0008, //  8: jmp    8                          
            //     .wrap
};

struct pio_program COMPLEX_TRIGGER_program = {
    .instructions = COMPLEX_TRIGGER_program_instructions,
    .length = 9,
    .origin = -1,
};

static inline pio_sm_config COMPLEX_TRIGGER_program_get_default_config(uint offset) {
    pio_sm_config c = pio_get_default_sm_config();
    sm_config_set_wrap(&c, offset + COMPLEX_TRIGGER_wrap_target, offset + COMPLEX_TRIGGER_wrap);
    return c;
}
#endif
//-----------------------------------------------------------------------------
//--------------Complex trigger PIO program END--------------------------------
//-----------------------------------------------------------------------------

//-----------------------------------------------------------------------------
//--------------Fast trigger PIO program---------------------------------------
//-----------------------------------------------------------------------------
#ifdef SUPPORTS_COMPLEX_TRIGGER

#define FAST_TRIGGER_wrap_target 0
#define FAST_TRIGGER_wrap 31

uint16_t FAST_TRIGGER_program_instructions[32];

struct pio_program FAST_TRIGGER_program = {
    .instructions = FAST_TRIGGER_program_instructions,
    .length = 32,
    .origin = 0,
};

static inline pio_sm_config FAST_TRIGGER_program_get_default_config(uint offset) {
    pio_sm_config c = pio_get_default_sm_config();
    sm_config_set_wrap(&c, offset + FAST_TRIGGER_wrap_target, offset + FAST_TRIGGER_wrap);
    sm_config_set_sideset(&c, 1, false, false);
    return c;
}

//Creates the fast trigger PIO program
uint8_t create_fast_trigger_program(uint8_t pattern, uint8_t length)
{
    //This creates a 32 instruction jump table. Each instruction is a MOV PC, PINS except for the addresses that
    //match the specified pattern.

    uint8_t i;
    uint8_t mask = (1 << length) - 1; //Mask for testing address vs pattern
    uint8_t first = 255;

    for(i = 0; i < 32; i++)
    {
        if((i & mask) == pattern)
            FAST_TRIGGER_program_instructions[i] = 0x1000 | i; //JMP i SIDE 1
        else
        {
            FAST_TRIGGER_program_instructions[i] = 0xA0A0;     //MOV PC, PINS SIDE 0
            first = i;
        }
    }

    return first;
}
#endif
//-----------------------------------------------------------------------------
//--------------Fast trigger PIO program END-----------------------------------
//-----------------------------------------------------------------------------

//Find the last captured sample index
uint32_t find_capture_tail()
{
    int transferCount;

    switch(lastCaptureMode)
    {
        case MODE_8_CHANNEL:
            transferCount = CAPTURE_BUFFER_SIZE;
            break;
        case MODE_16_CHANNEL:
            transferCount = CAPTURE_BUFFER_SIZE / 2;
            break;
        case MODE_24_CHANNEL:
            transferCount = CAPTURE_BUFFER_SIZE / 4;
            break;
    }

    //Add a delay in case the transfer is still in progress (just a safety measure, should not happen)
    //This is a massive delay in comparison to the needs of the DMA channel, but hey, 5ms is not going to be noticed anywhere :D
    busy_wait_ms(5);

    int32_t transferPos = 0xFFFFFFFF;

    //First we need to determine which DMA channel is busy (in the middle of a transfer)
    if(dma_channel_is_busy(dmaPingPong0))
    {
        transferPos = dma_channel_hw_addr(dmaPingPong0)->transfer_count;
    }
    else if(dma_channel_is_busy(dmaPingPong1))
    {
        transferPos = dma_channel_hw_addr(dmaPingPong1)->transfer_count;
    }

    //No channel busy?? WTF???
    if(transferPos == 0xFFFFFFFF) 
        return 0xFFFFFFFF;
    
    //Ok, now we need to know at which transfer the DMA is. The value equals to (MAX_TRANSFERS - TRANSFERS_LEFT) - 1 (DMA channel decrements transfer_count when it starts :/).
    uint32_t transfer = (transferCount - transferPos) - 1; //TODO: CHECK

    //Our capture absolute last position
    return transfer;
}

//Disable the trigger GPIOs to avoid triggering again a chained device
void disable_gpios()
{
    #ifdef SUPPORTS_COMPLEX_TRIGGER
    gpio_deinit(COMPLEX_TRIGGER_OUT_PIN);
    gpio_deinit(COMPLEX_TRIGGER_IN_PIN); 
    #endif

    for(uint8_t i = 0; i < lastCapturePinCount; i++)
        gpio_deinit(lastCapturePins[i]);


    gpio_set_inover(lastTriggerPin, 0);
}


//DMA channel handler, not in memory to speed it up
void __not_in_flash_func(dma_handler)()
{

    //Did channel0 triggered the irq?
    if(dma_channel_get_irq0_status(dmaPingPong0))
    {
        //Clear the irq
        dma_channel_acknowledge_irq0(dmaPingPong0);
        //Rewrite the write address without triggering the channel
        dma_channel_set_write_addr(dmaPingPong0, captureBuffer, false);
    }
    else
    {
        //Clear the irq
        dma_channel_acknowledge_irq0(dmaPingPong1);
        //Rewrite the write address without triggering the channel
        dma_channel_set_write_addr(dmaPingPong1, captureBuffer, false);
    }

}

void abort_DMAs()
{
    hw_clear_bits(&dma_hw->ch[dmaPingPong0].al1_ctrl, DMA_CH0_CTRL_TRIG_EN_BITS);
    hw_clear_bits(&dma_hw->ch[dmaPingPong1].al1_ctrl, DMA_CH0_CTRL_TRIG_EN_BITS);

    //Abort any pending transfer
    dma_channel_abort(dmaPingPong0);
    dma_channel_abort(dmaPingPong1);

    //Disable IRQ0
    dma_channel_set_irq0_enabled(dmaPingPong0, false); //Enable IRQ 0
    dma_channel_set_irq0_enabled(dmaPingPong1, false); //Enable IRQ 0
    irq_set_enabled(DMA_IRQ_0, false);

    irq_remove_handler (DMA_IRQ_0, dma_handler);

    //Unclaim the channels
    dma_channel_unclaim(dmaPingPong0);
    dma_channel_unclaim(dmaPingPong1);
}

#ifdef SUPPORTS_COMPLEX_TRIGGER

//Triggered when a fast capture ends
void fast_capture_completed() 
{
    //Disable the GPIO's
    disable_gpios();

    lastTail = find_capture_tail();

    //Abort DMA channels
    abort_DMAs();

    //Clear PIO interrupt 0 and unhook handler
    pio_interrupt_clear(capturePIO, 0);

    //Stop PIO capture program and clear
    pio_sm_set_enabled(capturePIO, sm_Capture, false);
    pio_sm_unclaim(capturePIO, sm_Capture);
    
    pio_remove_program(capturePIO, &FAST_CAPTURE_program, captureOffset);

    //Stop PIO trigger program and clear
    pio_sm_set_enabled(triggerPIO, sm_Trigger, false);
    pio_sm_set_pins(triggerPIO, sm_Trigger, 0);
    pio_sm_unclaim(triggerPIO, sm_Trigger);
    
    pio_remove_program(triggerPIO, &FAST_TRIGGER_program, triggerOffset);

    //Mark the capture as finished
    captureFinished = true;
}

//Check if the capture has finished, this is done because the W messes the PIO interrupts
void check_fast_interrupt()
{
    if(lastCaptureType == CAPTURE_TYPE_FAST && capturePIO->irq & 1)
        fast_capture_completed();
}

//Triggered when a complex capture ends
void complex_capture_completed() 
{
    //Disable the GPIO's
    disable_gpios();

    lastTail = find_capture_tail();

    //Abort DMA channels
    abort_DMAs();

    //Clear PIO interrupt 0 and unhook handler
    pio_interrupt_clear(capturePIO, 0);
    irq_set_enabled(PIO0_IRQ_0, false);
    irq_remove_handler(PIO0_IRQ_0, complex_capture_completed);

    //Stop PIO capture program and clear
    pio_sm_set_enabled(capturePIO, sm_Capture, false);
    pio_sm_unclaim(capturePIO, sm_Capture);
    
    pio_remove_program(capturePIO, &COMPLEX_CAPTURE_program, captureOffset);

    //Stop PIO trigger program and clear
    pio_sm_set_enabled(capturePIO, sm_Trigger, false);
    pio_sm_set_pins(capturePIO, sm_Trigger, 0);
    pio_sm_unclaim(capturePIO, sm_Trigger);
    
    pio_remove_program(capturePIO, &COMPLEX_TRIGGER_program, triggerOffset);
    
    //Mark the capture as finished
    captureFinished = true;
}

#endif


//Triggered when a blast capture ends
void blast_capture_completed()
{
    //Clear the irq
    dma_channel_acknowledge_irq0(dmaPingPong0);

    //Not needed, left for sanity
    hw_clear_bits(&dma_hw->ch[dmaPingPong0].al1_ctrl, DMA_CH0_CTRL_TRIG_EN_BITS);

    //Disable IRQ0
    dma_channel_set_irq0_enabled(dmaPingPong0, false); //Enable IRQ 0
    irq_set_enabled(DMA_IRQ_0, false);
    irq_remove_handler (DMA_IRQ_0, blast_capture_completed);

    //Unclaim the channels
    dma_channel_unclaim(dmaPingPong0);

    //Restore DMA priority to normal
    bus_ctrl_hw->priority = 0;

    lastTail = lastPostSize; //TODO: CHECK

    //Stop PIO program and clear
    pio_sm_set_enabled(capturePIO, sm_Capture, false);
    pio_sm_unclaim(capturePIO, sm_Capture);
    
    pio_remove_program(capturePIO, &BLAST_CAPTURE_program, captureOffset);

    //Mark the capture as finished
    captureFinished = true;
}


//Triggered when a simple capture ends
void simple_capture_completed() 
{
    //Disable the GPIO's
    disable_gpios();

    lastTail = find_capture_tail();

    //Abort DMA channels
    abort_DMAs();

    //Clear PIO interrupt 0 and unhook handler
    pio_interrupt_clear(capturePIO, 0);
    irq_set_enabled(PIO0_IRQ_0, false);
    irq_remove_handler(PIO0_IRQ_0, simple_capture_completed);

    //Clear PIO interrupt 1, disable NMI and reset systick
    pio_interrupt_clear (capturePIO, 1);
    pio_set_irq1_source_enabled(capturePIO, pis_interrupt1, false);

    if(timestampIndex)
    {
#if defined(BUILD_PICO_2)
        EPPB->NMI_MASK0 = 0;
#else
        syscfg_hw->proc0_nmi_mask = 0;
#endif
        exception_restore_handler(NMI_EXCEPTION, oldNMIHandler);
        systick_hw->csr = 0;
        exception_restore_handler(SYSTICK_EXCEPTION, oldSysTickHandler);
    }

    //Stop PIO program and clear
    pio_sm_set_enabled(capturePIO, sm_Capture, false);
    pio_sm_unclaim(capturePIO, sm_Capture);
    
    if(lastTriggerInverted)
        pio_remove_program(capturePIO, &POSITIVE_CAPTURE_program, captureOffset);
    else
        pio_remove_program(capturePIO, &NEGATIVE_CAPTURE_program, captureOffset);

    //Mark the capture as finished
    captureFinished = true;

}

//TODO: HERE
void configureBlastDMA(CHANNEL_MODE channelMode, uint32_t length)
{
    enum dma_channel_transfer_size transferSize;
    dma_channel_config dmaConfig;

    switch(channelMode)
    {
        case MODE_8_CHANNEL:
            transferSize = DMA_SIZE_8;
            break;
        case MODE_16_CHANNEL:
            transferSize = DMA_SIZE_16;
            break;
        case MODE_24_CHANNEL:
            transferSize = DMA_SIZE_32;
            break;
    }

    dmaPingPong0 = dma_claim_unused_channel(true);

    //Configure first capture DMA
    dmaConfig = dma_channel_get_default_config(dmaPingPong0);
    channel_config_set_read_increment(&dmaConfig, false); //Do not increment read address
    channel_config_set_write_increment(&dmaConfig, true); //Increment write address
    channel_config_set_transfer_data_size(&dmaConfig, transferSize); //Transfer size is based on capture mode
    channel_config_set_dreq(&dmaConfig, pio_get_dreq(capturePIO, sm_Capture, false)); //Set DREQ as RX FIFO
    channel_config_set_enable(&dmaConfig, true); //Enable the channel

    dma_channel_set_irq0_enabled(dmaPingPong0, true); //Enable IRQ 0

    //Set interrupt handler and enable it
    irq_set_exclusive_handler(DMA_IRQ_0, blast_capture_completed);
    irq_set_enabled(DMA_IRQ_0, true);
    irq_set_priority(DMA_IRQ_0, 0);

    //Full priority to the DMA
    bus_ctrl_hw->priority = BUSCTRL_BUS_PRIORITY_DMA_W_BITS | BUSCTRL_BUS_PRIORITY_DMA_R_BITS;

    dma_channel_configure(dmaPingPong0, &dmaConfig, captureBuffer, &capturePIO->rxf[sm_Capture], length, true); //Configure the channel and trigger it
   
}

//Configure the two DMA channels
void configureCaptureDMAs(CHANNEL_MODE channelMode)
{

    enum dma_channel_transfer_size transferSize;
    dma_channel_config dmaPingPong0Config;
    dma_channel_config dmaPingPong1Config;

    switch(channelMode)
    {
        case MODE_8_CHANNEL:
            transferSize = DMA_SIZE_8;
            transferCount = CAPTURE_BUFFER_SIZE;
            break;
        case MODE_16_CHANNEL:
            transferSize = DMA_SIZE_16;
            transferCount = CAPTURE_BUFFER_SIZE / 2;
            break;
        case MODE_24_CHANNEL:
            transferSize = DMA_SIZE_32;
            transferCount = CAPTURE_BUFFER_SIZE / 4;
            break;
    }

    dmaPingPong0 = dma_claim_unused_channel(true);
    dmaPingPong1 = dma_claim_unused_channel(true);

    //Configure first capture DMA
    dmaPingPong0Config = dma_channel_get_default_config(dmaPingPong0);
    channel_config_set_read_increment(&dmaPingPong0Config, false); //Do not increment read address
    channel_config_set_write_increment(&dmaPingPong0Config, true); //Increment write address
    channel_config_set_transfer_data_size(&dmaPingPong0Config, transferSize); //Transfer size is based on capture mode
    channel_config_set_chain_to(&dmaPingPong0Config, dmaPingPong1); //Chain to the second dma channel
    channel_config_set_dreq(&dmaPingPong0Config, pio_get_dreq(capturePIO, sm_Capture, false)); //Set DREQ as RX FIFO
    channel_config_set_enable(&dmaPingPong0Config, true); //Enable the channel

    dma_channel_set_irq0_enabled(dmaPingPong0, true); //Enable IRQ 0

    //Configure second capture DMA
    dmaPingPong1Config = dma_channel_get_default_config(dmaPingPong1);
    channel_config_set_read_increment(&dmaPingPong1Config, false); //Do not increment read address
    channel_config_set_write_increment(&dmaPingPong1Config, true); //Increment write address
    channel_config_set_transfer_data_size(&dmaPingPong1Config, transferSize); //Transfer size is based on capture mode
    channel_config_set_chain_to(&dmaPingPong1Config, dmaPingPong0); //Chain to the first dma channel
    channel_config_set_dreq(&dmaPingPong1Config, pio_get_dreq(capturePIO, sm_Capture, false)); //Set DREQ as RX FIFO
    channel_config_set_enable(&dmaPingPong1Config, true); //Enable the channel

    dma_channel_set_irq0_enabled(dmaPingPong1, true); //Enable IRQ 0

    //Set interrupt handler and enable it
    irq_set_exclusive_handler(DMA_IRQ_0, dma_handler);
    irq_set_enabled(DMA_IRQ_0, true);
    irq_set_priority(DMA_IRQ_0, 0);

    dma_channel_configure(dmaPingPong1, &dmaPingPong1Config, captureBuffer, &capturePIO->rxf[sm_Capture], transferCount, false); //Configure the channel but don't trigger it
    dma_channel_configure(dmaPingPong0, &dmaPingPong0Config, captureBuffer, &capturePIO->rxf[sm_Capture], transferCount, true); //Configure the and trigger it

}

void StopCapture()
{
    if(!captureFinished)
    {
        //Ensure the DMA channels are stopped, else they will overrun the buffer when the interrupts are disabled
        hw_clear_bits(&dma_hw->ch[dmaPingPong0].al1_ctrl, DMA_CH0_CTRL_TRIG_EN_BITS);
        hw_clear_bits(&dma_hw->ch[dmaPingPong1].al1_ctrl, DMA_CH0_CTRL_TRIG_EN_BITS);

        uint32_t int_status = save_and_disable_interrupts();

        #ifdef SUPPORTS_COMPLEX_TRIGGER

        if(lastCaptureType == CAPTURE_TYPE_SIMPLE)
            simple_capture_completed();
        else if(lastCaptureType == CAPTURE_TYPE_COMPLEX)
            complex_capture_completed();
        else if(lastCaptureType == CAPTURE_TYPE_FAST)
            fast_capture_completed();
        else if(lastCaptureType == CAPTURE_TYPE_BLAST)
            blast_capture_completed();

        #else

        if(lastCaptureType == CAPTURE_TYPE_SIMPLE)
            simple_capture_completed();
        else if(lastCaptureType == CAPTURE_TYPE_BLAST)
            blast_capture_completed();

        #endif

        restore_interrupts(int_status);
    }
}

#ifdef SUPPORTS_COMPLEX_TRIGGER

bool StartCaptureFast(uint32_t freq, uint32_t preLength, uint32_t postLength, const uint8_t* capturePins, uint8_t capturePinCount, uint8_t triggerPinBase, uint8_t triggerPinCount, uint16_t triggerValue, CHANNEL_MODE captureMode)
{
    
    //ABOUT THE FAST TRIGGER
    //
    //The fast trigger is an evolution of the complex trigger.
    //Like the complex trigger this is a sepparate program that checks for a pattern to trigger the capture program second stage.
    //
    //The main difference is the maximum length of the pattern to match and the sampling speed. This fast trigger
    //can only use a pattern up to 5 bits, but it captures at maximum speed of 100Msps (it could even sample up to 200Mhz but to match the
    //maximum speed of the sampling it is limited to 100Msps).
    //To achieve this the program occupies all 32 instructions of a PIO module, this is basically a jump table, each
    //instruction moves the pin values to the program counter except for the ones that match the pattern, which activate the
    //trigger pin using the side pins and create an infinite loop jumping to itself (basically a JMP currentpc SIDE 1).
    //
    //This solves the speed and latency problem, the speed reaches 100Msps and the latency is reduced to a maximum of 2 cycles, but
    //still can glitch on low speeds and also occupies a complete PIO module (but we have one unused, so its not a problem)


    int maxSamples;

    switch(captureMode)
    {
        case MODE_8_CHANNEL:
            maxSamples = CAPTURE_BUFFER_SIZE;
            break;
        case MODE_16_CHANNEL:
            maxSamples = CAPTURE_BUFFER_SIZE / 2;
            break;
        case MODE_24_CHANNEL:
            maxSamples = CAPTURE_BUFFER_SIZE / 4;
            break;
    }

    //Too many samples requested?
    if(preLength + postLength > maxSamples)
        return false;

    //Frequency too high?
    if(freq > MAX_FREQ)
        return false;

    //Incorrect pin count?
    if(capturePinCount < 1 || capturePinCount > MAX_CHANNELS)
        return false;

    //Bad trigger?
    if(triggerPinBase > 15 || triggerPinCount > 5 || triggerPinCount < 1 || triggerPinCount + triggerPinBase > 16)
        return false;

    //Clear capture buffer (to avoid sending bad data if the trigger happens before the presamples are filled)
    memset(captureBuffer, 0, sizeof(captureBuffer));

    //Store info about the capture
    lastPreSize = preLength;
    lastPostSize = postLength;
    lastLoopCount = 0;
    lastCapturePinCount = capturePinCount;
    lastCaptureComplexFast = true;
    lastCaptureMode = captureMode;

    //Map channels to pins
    for(uint8_t i = 0; i < capturePinCount; i++)
        lastCapturePins[i] = pinMap[capturePins[i]];

    //Store trigger info
    triggerPinBase = pinMap[triggerPinBase];
    lastTriggerPinBase = triggerPinBase;

    //Calculate clock divider based on frequency, it generates a clock 2x faster than the capture freequency
    float clockDiv = (float)clock_get_hz(clk_sys) / (float)(freq * 2);

    //Store the PIO units and clear program memory
    capturePIO = pio1; //Cannot clear it in PIO1 because the W uses PIO1 to transfer data
    triggerPIO = pio0;

    pio_clear_instruction_memory(triggerPIO);

    //Configure 24 + 2 IO's to be used by the PIO (24 channels + 2 trigger pins)
    pio_gpio_init(triggerPIO, COMPLEX_TRIGGER_OUT_PIN);
    pio_gpio_init(capturePIO, COMPLEX_TRIGGER_IN_PIN);

    for(uint8_t i = 0; i < 24; i++)
        pio_gpio_init(capturePIO, pinMap[i]);

    //Configure capture SM
    sm_Capture = pio_claim_unused_sm(capturePIO, true); 
    pio_sm_clear_fifos(capturePIO, sm_Capture);
    pio_sm_restart(capturePIO, sm_Capture);
    captureOffset = pio_add_program(capturePIO, &FAST_CAPTURE_program);

    //Modified for the W
    for(int i = 0; i < 24; i++)
        pio_sm_set_consecutive_pindirs(capturePIO, sm_Capture, pinMap[i], 1, false);

    //Configure state machines
    pio_sm_config smConfig = FAST_CAPTURE_program_get_default_config(captureOffset);

    //Inputs start at pin INPUT_PIN_BASE
    sm_config_set_in_pins(&smConfig, INPUT_PIN_BASE);

    //Set clock to 2x required frequency
    sm_config_set_clkdiv(&smConfig, clockDiv);

    //Autopush per 29 bits
    sm_config_set_in_shift(&smConfig, false, true, 29);

    //Configure fast trigger pin (COMPLEX_TRIGGER_IN_PIN) as JMP pin.
    sm_config_set_jmp_pin(&smConfig, COMPLEX_TRIGGER_IN_PIN);

    //Configure interrupt 0
    pio_interrupt_clear (capturePIO, 0);

    //Reset timestamp index
    timestampIndex = 0;

    //Initialize state machine
    pio_sm_init(capturePIO, sm_Capture, captureOffset, &smConfig);

    //Configure trigger SM
    sm_Trigger = pio_claim_unused_sm(triggerPIO, true);
    pio_sm_clear_fifos(triggerPIO, sm_Trigger);
    pio_sm_restart(triggerPIO, sm_Trigger);

    //Create trigger program
    uint8_t triggerFirstInstruction = create_fast_trigger_program(triggerValue, triggerPinCount);

    //Configure trigger state machine
    triggerOffset = pio_add_program(triggerPIO, &FAST_TRIGGER_program);
    pio_sm_set_consecutive_pindirs(triggerPIO, sm_Trigger, COMPLEX_TRIGGER_OUT_PIN, 1, true); //Pin COMPLEX_TRIGGER_OUT_PIN as output (connects to Pin COMPLEX_TRIGGER_IN_PIN, to trigger capture)
    pio_sm_set_consecutive_pindirs(triggerPIO, sm_Trigger, triggerPinBase, triggerPinCount, false); //Trigger pins start at triggerPinBase

    smConfig = FAST_TRIGGER_program_get_default_config(triggerOffset);

    sm_config_set_in_pins(&smConfig, triggerPinBase); //Trigger input starts at pin base
    sm_config_set_set_pins(&smConfig, COMPLEX_TRIGGER_OUT_PIN, 1); //Trigger output is a set pin
    sm_config_set_sideset_pins(&smConfig, COMPLEX_TRIGGER_OUT_PIN); //Trigger output is a side pin
    sm_config_set_clkdiv(&smConfig, 1); //Trigger always runs at max speed
    
    //Configure DMA's
    configureCaptureDMAs(captureMode);

    //Enable capture state machine
    pio_sm_set_enabled(capturePIO, sm_Capture, true);

    //Write capture length to post program
    pio_sm_put_blocking(capturePIO, sm_Capture, postLength - 1);

    //Initialize trigger state machine
    pio_sm_init(triggerPIO, sm_Trigger, triggerOffset, &smConfig);
    
    //Enable trigger state machine
    pio_sm_set_enabled(triggerPIO, sm_Trigger, true);

    //Finally clear capture status and process flags
    captureFinished = false;
    captureProcessed = false;
    lastCaptureType = CAPTURE_TYPE_FAST;

    //We're done
    return true;
}

bool StartCaptureComplex(uint32_t freq, uint32_t preLength, uint32_t postLength, const uint8_t* capturePins, uint8_t capturePinCount, uint8_t triggerPinBase, uint8_t triggerPinCount, uint16_t triggerValue, CHANNEL_MODE captureMode)
{
    
    //ABOUT THE COMPLEX TRIGGER
    //
    //The complex trigger is a hack to achieve the maximum speed in the capture program.
    //To get to 100Msps with a 200Mhz clock each capture must be excuted in two instructions. For this the basic
    //capture programs (the positive and negative ones) use the JMP PIN instruction, this redirects the program flow based in the
    //state of a pin, so with an IN instruction and a JMP instruction we can create a loop that captures data until the trigger pin
    //is in the correct edge and then jumps to another subroutine that captures until the post-trigger samples are met.
    //
    //Unfortunately there is no way to jump to a subroutine based in the status of more than one pin, you can jump based in the
    //comparison of the scratch registers, but this requires more than one instruction to prepare the data.
    //So, what I have implemented here is an asynchronouss trigger, a second state machine running at máximum speed checks if the trigger
    //condition is met and then notifies to the first state machine. But... there is no way to notify of something between state machines
    //except for interrupts, and interrupts blocks the code execution (you WAIT for the interrupt) so this is not viable, so we use a hack, we
    //interconnect two pins (GPIO0 and GPIO1), one is an output from the trigger state machine and the other is the JMP PIN for the capture
    //state machine. When the trigger condition is met the output pin is set to 1 so the JMP PIN pin receives this signal and we can keep
    //our capture program to use two instructions.
    //This carries some limitations, the trigger can only work up to 66Msps but the capture can go up to 100Msps as they are independent.
    //Also, as the trigger always runs at maximum speed there may happen a glitch in the trigger signal for lower capture speeds, the
    //condition may be met but for less time than a capture cycle, so the capture machine will not sample this trigger condition.
    //Finally the trigger also has some cycles of delay, 3 instructions plus 2 cycles of propagation to the ISR, so a maximum of
    //25ns of delay can happen.

    int maxSamples;

    switch(captureMode)
    {
        case MODE_8_CHANNEL:
            maxSamples = CAPTURE_BUFFER_SIZE;
            break;
        case MODE_16_CHANNEL:
            maxSamples = CAPTURE_BUFFER_SIZE / 2;
            break;
        case MODE_24_CHANNEL:
            maxSamples = CAPTURE_BUFFER_SIZE / 4;
            break;
    }

    //Too many samples requested?
    if(preLength + postLength > maxSamples)
        return false;

    //Frequency too high?
    if(freq > MAX_FREQ)
        return false;

    //Incorrect pin count?
    if(capturePinCount < 1 || capturePinCount > MAX_CHANNELS)
        return false;

    //Bad trigger?
    if(triggerPinBase > 15 || triggerPinCount > 16 || triggerPinCount < 1 || triggerPinCount + triggerPinBase > 16)
        return false;

    //Clear capture buffer (to avoid sending bad data if the trigger happens before the presamples are filled)
    memset(captureBuffer, 0, sizeof(captureBuffer));

    //Store info about the capture
    lastPreSize = preLength;
    lastPostSize = postLength;
    lastLoopCount = 0;
    lastCapturePinCount = capturePinCount;
    lastCaptureComplexFast = true;
    lastCaptureMode = captureMode;

    //Map channels to pins
    for(uint8_t i = 0; i < capturePinCount; i++)
        lastCapturePins[i] = pinMap[capturePins[i]];

    //Store trigger info
    triggerPinBase = pinMap[triggerPinBase];
    lastTriggerPinBase = triggerPinBase;

    //Calculate clock divider based on frequency, it generates a clock 2x faster than the capture freequency
    float clockDiv = (float)clock_get_hz(clk_sys) / (float)(freq * 2);

    //Store the PIO unit and clear program memory
    capturePIO = pio0;
    pio_clear_instruction_memory(capturePIO);

    //Configure 24 + 2 IO's to be used by the PIO (24 channels + 2 trigger pins)
    pio_gpio_init(capturePIO, COMPLEX_TRIGGER_OUT_PIN);
    pio_gpio_init(capturePIO, COMPLEX_TRIGGER_IN_PIN);

    for(uint8_t i = 0; i < 24; i++)
        pio_gpio_init(capturePIO, pinMap[i]);

    //Configure capture SM
    sm_Capture = pio_claim_unused_sm(capturePIO, true);
    pio_sm_clear_fifos(capturePIO, sm_Capture);
    pio_sm_restart(capturePIO, sm_Capture);
    captureOffset = pio_add_program(capturePIO, &COMPLEX_CAPTURE_program);

    for(int i = 0; i < 24; i++)
        pio_sm_set_consecutive_pindirs(capturePIO, sm_Capture, pinMap[i], 1, false);

    //Configure state machines
    pio_sm_config smConfig = COMPLEX_CAPTURE_program_get_default_config(captureOffset);

    //Inputs start at pin INPUT_PIN_BASE
    sm_config_set_in_pins(&smConfig, INPUT_PIN_BASE);

    //Set clock to 2x required frequency
    sm_config_set_clkdiv(&smConfig, clockDiv);

    //Autopush per 29 bits
    sm_config_set_in_shift(&smConfig, false, true, 29);

    //Configure complex trigger pin (pin COMPLEX_TRIGGER_IN_PIN) as JMP pin.
    sm_config_set_jmp_pin(&smConfig, COMPLEX_TRIGGER_IN_PIN);

    //Configure interrupt 0
    pio_interrupt_clear (capturePIO, 0);
    pio_set_irq0_source_enabled(capturePIO, pis_interrupt0, true);
    irq_set_exclusive_handler(PIO0_IRQ_0, complex_capture_completed);
    irq_set_enabled(PIO0_IRQ_0, true);

    //Reset timestamp index
    timestampIndex = 0;

    //Initialize state machine
    pio_sm_init(capturePIO, sm_Capture, captureOffset, &smConfig);

    //Configure trigger SM
    sm_Trigger = pio_claim_unused_sm(capturePIO, true);
    pio_sm_clear_fifos(capturePIO, sm_Trigger);
    pio_sm_restart(capturePIO, sm_Trigger);

    //Modify trigger program to use the correct pins
    COMPLEX_TRIGGER_program_instructions[5] = 0x6040 | triggerPinCount;

    //Configure trigger state machine
    triggerOffset = pio_add_program(capturePIO, &COMPLEX_TRIGGER_program);
    pio_sm_set_consecutive_pindirs(capturePIO, sm_Trigger, COMPLEX_TRIGGER_OUT_PIN, 1, true); //Pin COMPLEX_TRIGGER_OUT_PIN as output (connects to Pin COMPLEX_TRIGGER_IN_PIN, to trigger capture)
    pio_sm_set_consecutive_pindirs(capturePIO, sm_Trigger, triggerPinBase, triggerPinCount, false); //Trigger pins start at triggerPinBase

    smConfig = COMPLEX_TRIGGER_program_get_default_config(triggerOffset);
    sm_config_set_in_pins(&smConfig, triggerPinBase); //Trigger input starts at pin base
    sm_config_set_set_pins(&smConfig, COMPLEX_TRIGGER_OUT_PIN, 1); //Trigger output is a set pin
    sm_config_set_clkdiv(&smConfig, 1); //Trigger always runs at max speed
    sm_config_set_in_shift(&smConfig, false, false, 0); //Trigger shifts left to right
    
    //Initialize trigger state machine
    pio_sm_init(capturePIO, sm_Trigger, triggerOffset, &smConfig); //Init trigger
    
    //Configure DMA's
    configureCaptureDMAs(captureMode);

    //Enable capture state machine
    pio_sm_set_enabled(capturePIO, sm_Capture, true);

    //Write capture length to post program
    pio_sm_put_blocking(capturePIO, sm_Capture, postLength - 1);

    //Enable trigger state machine
    pio_sm_set_enabled(capturePIO, sm_Trigger, true);

    //Write trigger value to trigger program
    pio_sm_put_blocking(capturePIO, sm_Trigger, triggerValue);

    //Finally clear capture status and process flags
    captureFinished = false;
    captureProcessed = false;
    lastCaptureType = CAPTURE_TYPE_COMPLEX;

    //We're done
    return true;
}

#endif

void __not_in_flash_func(sysTickRoll)()
{
    systickLoops++;
}

void __not_in_flash_func(loopEndHandler)()
{
    //Save timestamp
    loopTimestamp[timestampIndex++] = systick_hw->cvr | systickLoops << 24; //timestamp;
    //Clear PIO interrupt
    capturePIO->irq = (1u << 1);
}

bool StartCaptureBlast(uint32_t freq, uint32_t length, const uint8_t* capturePins, uint8_t capturePinCount, uint8_t triggerPin, bool invertTrigger, CHANNEL_MODE captureMode)
{
    int maxSamples;

    switch(captureMode)
    {
        case MODE_8_CHANNEL:
            maxSamples = CAPTURE_BUFFER_SIZE;
            break;
        case MODE_16_CHANNEL:
            maxSamples = CAPTURE_BUFFER_SIZE / 2;
            break;
        case MODE_24_CHANNEL:
            maxSamples = CAPTURE_BUFFER_SIZE / 4;
            break;
    }

    //Too many samples requested?
    if(length > maxSamples)
        return false;

    //Frequency too high?
    if(freq > MAX_BLAST_FREQ)
        return false;

    //Incorrect pin count?
    if(capturePinCount < 1 || capturePinCount > MAX_CHANNELS)
        return false;

    //Incorrect trigger pin?
    //WARNING: comparison of triggerPin and MAX_CHANNELS is correct, we exceed the maximum number of channels by 1 
    //as the complex trigger channel is added at the end of the pinMap array
    if(triggerPin < 0 || triggerPin > MAX_CHANNELS)
        return false;

    //Clear capture buffer (to avoid sending bad data if the trigger happens before the presamples are filled)
    memset(captureBuffer, 0, sizeof(captureBuffer));

    //Store info about the capture
    lastPreSize = 0;
    lastPostSize = length;
    lastLoopCount = 0;
    lastCapturePinCount = capturePinCount;
    lastTriggerInverted = invertTrigger;
    lastCaptureComplexFast = false;
    lastCaptureMode = captureMode;

    //Map channels to pins
    for(uint8_t i = 0; i < capturePinCount; i++)
        lastCapturePins[i] = pinMap[capturePins[i]];

    //Store trigger info
    triggerPin = pinMap[triggerPin];
    lastTriggerPin = triggerPin;

    //Calculate clock divider based on frequency, in blast mode it is a 1:1 clock
    float clockDiv = (float)clock_get_hz(clk_sys) / (float)(freq);
    
    //Store the PIO unit and clear program memory
    capturePIO = pio0;
    pio_clear_instruction_memory(capturePIO);

    //Configure capture SM
    sm_Capture = pio_claim_unused_sm(capturePIO, true);
    pio_sm_clear_fifos(capturePIO, sm_Capture);
    pio_sm_restart(capturePIO, sm_Capture);

    //Load program
    captureOffset = pio_add_program(capturePIO, &BLAST_CAPTURE_program);

    //Configure capture pins
    for(int i = 0; i < 24; i++)
        pio_sm_set_consecutive_pindirs(capturePIO, sm_Capture, pinMap[i], 1, false);

    for(uint8_t i = 0; i < 24; i++)
        pio_gpio_init(capturePIO, pinMap[i]);
    
    //Configure trigger pin
    pio_sm_set_consecutive_pindirs(capturePIO, sm_Capture, triggerPin, 1, false);
    pio_gpio_init(capturePIO, triggerPin);

    if(!invertTrigger)
        gpio_set_inover(triggerPin, 1);

    //Configure state machines
    pio_sm_config smConfig = BLAST_CAPTURE_program_get_default_config(captureOffset);

    //Input starts at pin INPUT_PIN_BASE
    sm_config_set_in_pins(&smConfig, INPUT_PIN_BASE);

    //Set clock to required frequency
    sm_config_set_clkdiv(&smConfig, clockDiv);

    //Autopush per dword
    sm_config_set_in_shift(&smConfig, true, true, 0);

    //Configure trigger pin as JMP pin.
    sm_config_set_jmp_pin(&smConfig, triggerPin);

    //Disable state machine
    pio_sm_set_enabled(capturePIO, sm_Capture, false);

    //Initialize state machine
    pio_sm_init(capturePIO, sm_Capture, captureOffset, &smConfig);

    //Configure DMA's
    configureBlastDMA(captureMode, length);

    //Enable state machine
    pio_sm_set_enabled(capturePIO, sm_Capture, true);
    

    //Finally clear capture status, process flags and capture type
    captureFinished = false;
    captureProcessed = false;
    lastCaptureType = CAPTURE_TYPE_BLAST;

    //We're done
    return true;
}

bool StartCaptureSimple(uint32_t freq, uint32_t preLength, uint32_t postLength, uint8_t loopCount, uint8_t measureBursts, const uint8_t* capturePins, uint8_t capturePinCount, uint8_t triggerPin, bool invertTrigger, CHANNEL_MODE captureMode)
{
    int maxSamples;

    switch(captureMode)
    {
        case MODE_8_CHANNEL:
            maxSamples = CAPTURE_BUFFER_SIZE;
            break;
        case MODE_16_CHANNEL:
            maxSamples = CAPTURE_BUFFER_SIZE / 2;
            break;
        case MODE_24_CHANNEL:
            maxSamples = CAPTURE_BUFFER_SIZE / 4;
            break;
    }

    //Too many samples requested?
    if(preLength + (postLength * (loopCount + 1)) > maxSamples)
        return false;

    //Frequency too high?
    if(freq > MAX_FREQ)
        return false;

    //Incorrect pin count?
    if(capturePinCount < 1 || capturePinCount > MAX_CHANNELS)
        return false;

    //Incorrect trigger pin?
    if(triggerPin < 0 || triggerPin > MAX_CHANNELS)
        return false;

    //Clear capture buffer (to avoid sending bad data if the trigger happens before the presamples are filled)
    memset(captureBuffer, 0, sizeof(captureBuffer));

    //Store info about the capture
    lastPreSize = preLength;
    lastPostSize = postLength;
    lastLoopCount = loopCount;
    lastCapturePinCount = capturePinCount;
    lastTriggerInverted = invertTrigger;
    lastCaptureComplexFast = false;
    lastCaptureMode = captureMode;

    //Map channels to pins
    for(uint8_t i = 0; i < capturePinCount; i++)
        lastCapturePins[i] = pinMap[capturePins[i]];

    //Store trigger info
    triggerPin = pinMap[triggerPin];
    lastTriggerPin = triggerPin;

    //Calculate clock divider based on frequency, it generates a clock 2x faster than the capture freequency
    float clockDiv = (float)clock_get_hz(clk_sys) / (float)(freq * 2);
    
    //Store the PIO unit and clear program memory
    capturePIO = pio0;
    pio_clear_instruction_memory(capturePIO);

    //Configure capture SM
    sm_Capture = pio_claim_unused_sm(capturePIO, true);
    pio_sm_clear_fifos(capturePIO, sm_Capture);
    pio_sm_restart(capturePIO, sm_Capture);

    //Load correct program, depending on the trigger edge
    if(invertTrigger)
    {
        if(measureBursts)
            captureOffset = pio_add_program(capturePIO, &NEGATIVE_CAPTURE_MEASUREBURSTS_program);
        else
            captureOffset = pio_add_program(capturePIO, &NEGATIVE_CAPTURE_program);
    }
    else
    {
        if(measureBursts)
            captureOffset = pio_add_program(capturePIO, &POSITIVE_CAPTURE_MEASUREBURSTS_program);
        else
            captureOffset = pio_add_program(capturePIO, &POSITIVE_CAPTURE_program);
        
    }

    //Configure capture pins
    for(int i = 0; i < 24; i++)
        pio_sm_set_consecutive_pindirs(capturePIO, sm_Capture, pinMap[i], 1, false);

    for(uint8_t i = 0; i < 24; i++)
        pio_gpio_init(capturePIO, pinMap[i]);

    //Configure trigger pin
    pio_sm_set_consecutive_pindirs(capturePIO, sm_Capture, triggerPin, 1, false);
    pio_gpio_init(capturePIO, triggerPin);

    //Configure state machines
    pio_sm_config smConfig = measureBursts?
                                (invertTrigger?
                                NEGATIVE_CAPTURE_MEASUREBURSTS_program_get_default_config(captureOffset):
                                POSITIVE_CAPTURE_MEASUREBURSTS_program_get_default_config(captureOffset)) :
                                (invertTrigger?
                                NEGATIVE_CAPTURE_program_get_default_config(captureOffset):
                                POSITIVE_CAPTURE_program_get_default_config(captureOffset));

    //Input starts at pin INPUT_PIN_BASE
    sm_config_set_in_pins(&smConfig, INPUT_PIN_BASE);

    //Set clock to 2x required frequency
    sm_config_set_clkdiv(&smConfig, clockDiv);

    //Autopush per dword
    sm_config_set_in_shift(&smConfig, true, true, 0);

    //Configure trigger pin as JMP pin.
    sm_config_set_jmp_pin(&smConfig, triggerPin);

    //Configure interupt 0
    pio_interrupt_clear (capturePIO, 0);
    pio_set_irq0_source_enabled(capturePIO, pis_interrupt0, true);
    irq_set_exclusive_handler(PIO0_IRQ_0, simple_capture_completed);
    irq_set_enabled(PIO0_IRQ_0, true);

    //Set-up burst measure
    if(loopCount > 0 && measureBursts)
    {
        //Configure NMI to get capture timestamp
        pio_interrupt_clear (capturePIO, 1);
        pio_set_irq1_source_enabled(capturePIO, pis_interrupt1, true);
        //irq_set_exclusive_handler(PIO0_IRQ_1, loopEndHandler);
        irq_set_priority(PIO0_IRQ_1, 0);
        //irq_set_enabled(PIO0_IRQ_1, true);

        //syscfg_hw->proc0_nmi_mask = 1 << PIO0_IRQ_1;
        
#if defined(BUILD_PICO_2)
        EPPB->NMI_MASK0 = 1 << PIO0_IRQ_1;
#else
        syscfg_hw->proc0_nmi_mask = 1 << PIO0_IRQ_1;
#endif

        oldNMIHandler = exception_set_exclusive_handler(NMI_EXCEPTION, loopEndHandler);

        //Reset loop counter
        systickLoops = 0;

        //Enable systick
        oldSysTickHandler = exception_set_exclusive_handler(SYSTICK_EXCEPTION, sysTickRoll);
        systick_hw->rvr = 0x00FFFFFF;
        systick_hw->cvr = 0x00FFFFFF;
        systick_hw->csr = 0x7;

    }
    
    //Reset timestamp index
    timestampIndex = 0;

    //Initialize state machine
    pio_sm_init(capturePIO, sm_Capture, captureOffset, &smConfig);

    //Configure DMA's
    configureCaptureDMAs(captureMode);

    //Enable state machine
    pio_sm_set_enabled(capturePIO, sm_Capture, true);

    //Write loop count and capture length to post program to start the capture process
    pio_sm_put_blocking(capturePIO, sm_Capture, loopCount);
    pio_sm_put_blocking(capturePIO, sm_Capture, postLength - 1);
    

    //Finally clear capture status, process flags and capture type
    captureFinished = false;
    captureProcessed = false;
    lastCaptureType = CAPTURE_TYPE_SIMPLE;

    //We're done
    return true;
}

bool IsCapturing()
{
    //If you need an explanation of this, you're a fool. :P
    return !captureFinished;
}

uint8_t* GetBuffer(uint32_t* bufferSize, uint32_t* firstSample, CHANNEL_MODE* captureMode)
{
    //Compute total sample count
    uint32_t totalSamples = lastPreSize + (lastPostSize * (lastLoopCount + 1));

    //If we don't have processed the buffer...
    if(!captureProcessed)
    {
        uint32_t maxSize;

        switch(lastCaptureMode)
        {
            case MODE_8_CHANNEL:
                maxSize = CAPTURE_BUFFER_SIZE;
                break;
            case MODE_16_CHANNEL:
                maxSize = CAPTURE_BUFFER_SIZE / 2;
                break;
            case MODE_24_CHANNEL:
                maxSize = CAPTURE_BUFFER_SIZE / 4;
                break;
        }
        //Calculate start position
        if(lastTail < totalSamples - 1)
            lastStartPosition = (maxSize - totalSamples) + lastTail + 1;
        else
            lastStartPosition = lastTail - totalSamples + 1;

        uint32_t currentPos = lastStartPosition;

        switch(lastCaptureMode)
        {
            case MODE_24_CHANNEL:
                {
                    uint32_t oldValue;
                    uint32_t newValue;
                    uint32_t* buffer = (uint32_t*)captureBuffer;
                    uint8_t lastPin = 0;
                    uint32_t blastMask = 0;

                    //If the capture was in blast mode and the trigger edge was positive, invert the value
                    if(lastCaptureType == CAPTURE_TYPE_BLAST && !lastTriggerInverted)
                        blastMask = 1 << (lastTriggerPin - INPUT_PIN_BASE);

                    //Sort channels
                    //(reorder captured bits based on the channels requested)
                    for(uint32_t buc = 0; buc < totalSamples; buc++)
                    {
                        oldValue = buffer[currentPos]; //Store current value
                        newValue = 0; //New value
                        
                        //If the capture was in blast mode and the trigger edge was positive, invert the value
                        if(lastCaptureType == CAPTURE_TYPE_BLAST && !lastTriggerInverted)
                            oldValue ^= blastMask;

                        for(int pin = 0; pin < lastCapturePinCount; pin++) //For each captured channel...
                        {
                            lastPin = lastCapturePins[pin] - INPUT_PIN_BASE;
                            newValue |= (((oldValue & (1 << lastPin))) >> lastPin) << pin; //Place channel data in the correct bit
                        }

                        //Update value in the buffer
                        buffer[currentPos++] = newValue;
                        //If we reached the end of the buffer, wrap around
                        if(currentPos >= maxSize)
                            currentPos = 0;
                    }
                }
                break;
            case MODE_16_CHANNEL:
                {
                    uint16_t oldValue;
                    uint16_t newValue;
                    uint16_t* buffer = (uint16_t*)captureBuffer;
                    uint8_t lastPin = 0;
                    uint16_t blastMask = 0;

                    //If the capture was in blast mode and the trigger edge was positive, invert the value
                    if(lastCaptureType == CAPTURE_TYPE_BLAST && !lastTriggerInverted)
                        blastMask = 1 << (lastTriggerPin - INPUT_PIN_BASE);

                    //Sort channels
                    //(reorder captured bits based on the channels requested)
                    for(uint32_t buc = 0; buc < totalSamples; buc++)
                    {
                        oldValue = buffer[currentPos]; //Store current value
                        newValue = 0; //New value
                        
                        //If the capture was in blast mode and the trigger edge was positive, invert the value
                        if(lastCaptureType == CAPTURE_TYPE_BLAST && !lastTriggerInverted)
                            oldValue ^= blastMask;

                        for(int pin = 0; pin < lastCapturePinCount; pin++) //For each captured channel...
                        {
                            lastPin = lastCapturePins[pin] - INPUT_PIN_BASE;
                            newValue |= (((oldValue & (1 << lastPin))) >> lastPin) << pin; //Place channel data in the correct bit
                        }

                        //Update value in the buffer
                        buffer[currentPos++] = newValue;
                        //If we reached the end of the buffer, wrap around
                        if(currentPos >= maxSize)
                            currentPos = 0;
                    }
                }
                break;
            case MODE_8_CHANNEL:
                {
                    uint8_t oldValue;
                    uint8_t newValue;
                    uint8_t* buffer = (uint8_t*)captureBuffer;
                    uint8_t lastPin = 0;
                    uint8_t blastMask = 0;

                    //If the capture was in blast mode and the trigger edge was positive, invert the value
                    if(lastCaptureType == CAPTURE_TYPE_BLAST && !lastTriggerInverted)
                        blastMask = 1 << (lastTriggerPin - INPUT_PIN_BASE);

                    //Sort channels
                    //(reorder captured bits based on the channels requested)
                    for(uint32_t buc = 0; buc < totalSamples; buc++)
                    {
                        oldValue = buffer[currentPos]; //Store current value

                        //If the capture was in blast mode and the trigger edge was positive, invert the value
                        if(lastCaptureType == CAPTURE_TYPE_BLAST && !lastTriggerInverted)
                            oldValue ^= blastMask;

                        newValue = 0; //New value

                        for(int pin = 0; pin < lastCapturePinCount; pin++) //For each captured channel...
                        {
                            lastPin = lastCapturePins[pin] - INPUT_PIN_BASE;
                            newValue |= (((oldValue & (1 << lastPin))) >> lastPin) << pin; //Place channel data in the correct bit
                        }

                        //Update value in the buffer
                        buffer[currentPos++] = newValue;
                        //If we reached the end of the buffer, wrap around
                        if(currentPos >= maxSize)
                            currentPos = 0;
                    }
                }
                break;
        }
        captureProcessed = true;
    }
    //Return data
    *captureMode = lastCaptureMode;
    *bufferSize = totalSamples;
    *firstSample = lastStartPosition;
    return captureBuffer;
}

volatile uint32_t* GetTimestamps(uint8_t* length)
{
    *length = timestampIndex;
    return loopTimestamp;
}