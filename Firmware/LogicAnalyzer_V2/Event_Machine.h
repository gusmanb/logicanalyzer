#ifndef __EVENTMACHINE__
    #define __EVENTMACHINE__

    #include "pico/stdlib.h"
    #include "pico/util/queue.h"

    //Event handler function declaration
    typedef void(*EVENT_HANDLER)(void*);

    //Event machine struct
    typedef struct _EVENT_MACHINE
    {
        //Queue to store events
        queue_t queue;
        //Function to process the events
        EVENT_HANDLER handler;

    } EVENT_MACHINE;

    void event_machine_init(EVENT_MACHINE* machine, EVENT_HANDLER handler, uint8_t args_size, uint8_t queue_depth);
    bool event_has_events(EVENT_MACHINE* machine);
    void event_push(EVENT_MACHINE* machine, void* event);
    void event_process_queue(EVENT_MACHINE* machine, void* event_buffer, uint8_t max_events);
    void event_clear(EVENT_MACHINE* machine);
    void event_free(EVENT_MACHINE* machine);

#endif