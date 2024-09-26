#include "LogicAnalyzer_Board_Settings.h"
#ifndef __ANALYZER_CAPTURE__
#define __ANALYZER_CAPTURE__

#if defined(BUILD_PICO_2)
#include <RP2350.h>
#endif

typedef enum
{
    MODE_8_CHANNEL,
    MODE_16_CHANNEL,
    MODE_24_CHANNEL

} CHANNEL_MODE;

bool StartCaptureSimple(uint32_t freq, uint32_t preLength, uint32_t postLength, uint8_t loopCount, uint8_t measureBursts, const uint8_t* capturePins, uint8_t capturePinCount, uint8_t triggerPin, bool invertTrigger, CHANNEL_MODE captureMode);
bool StartCaptureBlast(uint32_t freq, uint32_t length, const uint8_t* capturePins, uint8_t capturePinCount, uint8_t triggerPin, bool invertTrigger, CHANNEL_MODE captureMode);
#ifdef SUPPORTS_COMPLEX_TRIGGER
bool StartCaptureComplex(uint32_t freq, uint32_t preLength, uint32_t postLength, const uint8_t* capturePins, uint8_t capturePinCount, uint8_t triggerPinBase, uint8_t triggerPinCount, uint16_t triggerValue, CHANNEL_MODE captureMode);
bool StartCaptureFast(uint32_t freq, uint32_t preLength, uint32_t postLength, const uint8_t* capturePins, uint8_t capturePinCount, uint8_t triggerPinBase, uint8_t triggerPinCount, uint16_t triggerValue, CHANNEL_MODE captureMode);
#endif
void StopCapture();
bool IsCapturing();
uint8_t* GetBuffer(uint32_t* bufferSize, uint32_t* firstSample, CHANNEL_MODE* captureMode);
volatile uint32_t* GetTimestamps(uint8_t* length);
void check_fast_interrupt();

#endif