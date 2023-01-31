#include "Event_Machine.h"

//Initialize the event machine
void event_machine_init(EVENT_MACHINE* machine, EVENT_HANDLER handler, uint8_t event_size, uint8_t queue_depth)
{
    queue_init(&machine->queue, event_size, queue_depth);
    machine->handler = handler;
}

bool event_has_events(EVENT_MACHINE* machine)
{
    return &machine->queue.wptr !=  &machine->queue.rptr;
}

//Adds an event to the machine
void event_push(EVENT_MACHINE* machine, void* event)
{
    queue_add_blocking(&machine->queue, event);
}

//Processes the pending events
void event_process_queue(EVENT_MACHINE* machine, void* event_buffer, uint8_t max_events)
{
    uint8_t evt_count = 0;
    while(!queue_is_empty(&machine->queue) && evt_count++ < max_events)
    {
        queue_remove_blocking(&machine->queue, event_buffer);
        machine->handler(event_buffer);
    }
}

//Clears the stored events in the machine
void event_clear(EVENT_MACHINE* machine)
{
    machine->queue.wptr = 0;
    machine->queue.rptr = 0;
}

//Free an event machine
void event_free(EVENT_MACHINE* machine)
{
    queue_free(&machine->queue);
    machine->handler = NULL;
}