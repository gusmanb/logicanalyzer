#include "LogicAnalyzer_Board_Settings.h"

#ifdef USE_CYGW_WIFI

#include "Event_Machine.h"
#include "Shared_Buffers.h"
#include "LogicAnalyzer_WiFi.h"
#include "LogicAnalyzer_Structs.h"
#include <stdio.h>
#include <string.h>
#include "pico/stdlib.h"
#include "pico/cyw43_arch.h"
#include "pico/multicore.h"
#include "hardware/adc.h"
#include "hardware/gpio.h"
#include "hardware/flash.h"
#include "lwip/pbuf.h"
#include "lwip/tcp.h"

EVENT_FROM_FRONTEND frontendEventBuffer;
WIFI_STATE_MACHINE currentState = VALIDATE_SETTINGS;
ip_addr_t address;
struct tcp_pcb* serverPcb;
struct tcp_pcb* clientPcb;

bool apConnected = false;
bool boot = false;

#define LED_ON() cyw43_arch_gpio_put(CYW43_WL_GPIO_LED_PIN, 1)
#define LED_OFF() cyw43_arch_gpio_put(CYW43_WL_GPIO_LED_PIN, 0)

void getPowerStatus()
{
    EVENT_FROM_WIFI evtPower;
    evtPower.event = POWER_STATUS_DATA;
    evtPower.dataLength = sizeof(POWER_STATUS);
    POWER_STATUS* status = (POWER_STATUS*)&evtPower.data;
    
    adc_init();

    uint32_t oldInt = save_and_disable_interrupts();
    uint32_t old_pad = padsbank0_hw->io[29];
    uint32_t old_ctrl = iobank0_hw->io[29].ctrl;

    adc_gpio_init(29);
    adc_select_input(3);

    sleep_ms(100);

    const float conversion_factor = 3.3f / (1 << 12);
    status->vsysVoltage = adc_read() * conversion_factor * 3;

    gpio_init(29);

    padsbank0_hw->io[29] = old_pad;
    iobank0_hw->io[29].ctrl = old_ctrl;
    restore_interrupts(oldInt);

    status->vbusConnected = cyw43_arch_gpio_get(2);
    
    event_push(&wifiToFrontend, &evtPower);

}

void readSettings()
{
    wifiSettings = *((volatile WIFI_SETTINGS*)(FLASH_SETTINGS_ADDRESS));
}

void stopServer()
{
    if(serverPcb == NULL)
        return;

    tcp_close(serverPcb);
    serverPcb = NULL;
}

void killClient()
{
    if(clientPcb != NULL)
    {
        tcp_recv(clientPcb, NULL);
        tcp_err(clientPcb, NULL);
        tcp_close(clientPcb);
        clientPcb = NULL;
    }
    currentState = WAITING_TCP_CLIENT;
}

void sendData(uint8_t* data, uint8_t len)
{
    while(clientPcb && tcp_sndbuf(clientPcb) < len)
    {
        cyw43_arch_poll();
        sleep_ms(1);
    }

    if(tcp_write(clientPcb, data, len, TCP_WRITE_FLAG_COPY))
    {
        killClient();
        EVENT_FROM_WIFI evt;
        evt.event = DISCONNECTED;
        event_push(&wifiToFrontend, &evt);
    }
    
}

void serverError(void *arg, err_t err)
{
    killClient();

    EVENT_FROM_WIFI evt;
    evt.event = DISCONNECTED;
    event_push(&wifiToFrontend, &evt);
}

err_t serverReceiveData(void *arg, struct tcp_pcb *tpcb, struct pbuf *p, err_t err)
{
    EVENT_FROM_WIFI evt;

    //Client disconnected
    if(!p || p->tot_len == 0)
    {
        if(p)
            pbuf_free(p);
            
        killClient();
        evt.event = DISCONNECTED;
        event_push(&wifiToFrontend, &evt);
        return ERR_ABRT;
    }

    uint16_t left = p->tot_len;
    uint16_t pos = 0;

    while(left)
    {
        uint8_t copy = left > 128 ? 128 : left;
        evt.event = DATA_RECEIVED;
        evt.dataLength = copy;
        pbuf_copy_partial(p, evt.data, copy, pos);
        event_push(&wifiToFrontend, &evt);
        pos += copy;
        left -= copy;
    }

    pbuf_free(p);

    return ERR_OK;

}

err_t acceptConnection(void *arg, struct tcp_pcb *client_pcb, err_t err)
{
    if (err != ERR_OK || client_pcb == NULL || clientPcb != NULL || currentState != WAITING_TCP_CLIENT)
        return ERR_VAL;

    clientPcb = client_pcb;

    tcp_recv(clientPcb, serverReceiveData);
    tcp_err(clientPcb, serverError);

    currentState = TCP_CLIENT_CONNECTED;

    EVENT_FROM_WIFI evt;
    evt.event = CONNECTED;
    event_push(&wifiToFrontend, &evt);

    return ERR_OK;
}

bool tryStartServer()
{
    serverPcb = tcp_new_ip_type(IPADDR_TYPE_V4);
    err_t err = tcp_bind(serverPcb, &address, wifiSettings.port);

    if (err) 
        return false;

    serverPcb = tcp_listen_with_backlog(serverPcb, 1);

    if(!serverPcb)
        return false;

    tcp_accept(serverPcb, acceptConnection);
}

bool tryConnectAP()
{
    if(cyw43_arch_wifi_connect_timeout_ms((const char*)wifiSettings.apName, (const char*)wifiSettings.passwd, CYW43_AUTH_WPA2_AES_PSK, 10000))
        return false;

    ipaddr_aton((const char*)wifiSettings.ipAddress, &address);

    netif_set_ipaddr(netif_list, &address);

    apConnected = true;

    return true;
}

void disconnectAP()
{
    if(!apConnected)
        return;
        
    cyw43_wifi_leave(&cyw43_state, 0);
    apConnected = false;

}

void processWifiMachine()
{
    switch (currentState)
    {
        case VALIDATE_SETTINGS:
            {
                if(!boot)
                    readSettings();

                boot = true;

                uint16_t checksum = 0;

                for(int buc = 0; buc < 33; buc++)
                    checksum += wifiSettings.apName[buc];

                for(int buc = 0; buc < 64; buc++)
                    checksum += wifiSettings.passwd[buc];

                for(int buc = 0; buc < 16; buc++)
                    checksum += wifiSettings.ipAddress[buc];

                checksum += wifiSettings.port;

                checksum += 0x0f0f;

                if(wifiSettings.checksum == checksum)
                    currentState = CONNECTING_AP;
                else
                    currentState = WAITING_SETTINGS;
            }
            break;

        case CONNECTING_AP:
            if(tryConnectAP())
                currentState = STARTING_TCP_SERVER;
            break;
        case STARTING_TCP_SERVER:
            if(tryStartServer())
                currentState = WAITING_TCP_CLIENT;
            break;
        default:
            break;
    }
}

void frontendEvent(void* event)
{
    EVENT_FROM_FRONTEND* evt = (EVENT_FROM_FRONTEND*)event;
    switch(evt->event)
    {
        case LED_ON:
            LED_ON();
            break;

        case LED_OFF:
            LED_OFF();
            break;
        case CONFIG_RECEIVED:

            killClient();
            stopServer();
            disconnectAP();
            currentState = VALIDATE_SETTINGS;
            break;

        case SEND_DATA:
            sendData(evt->data, evt->dataLength);
            break;
        
        case GET_POWER_STATUS:
            getPowerStatus();
            break;
    }
}

void runWiFiCore()
{
    event_machine_init(&frontendToWifi, frontendEvent, sizeof(EVENT_FROM_FRONTEND), 8);
    multicore_lockout_victim_init();
    cyw43_arch_init();
    cyw43_arch_enable_sta_mode();
    EVENT_FROM_WIFI evtRdy;
    evtRdy.event = CYW_READY;
    event_push(&wifiToFrontend, &evtRdy);

    while(true)
    {
        event_process_queue(&frontendToWifi, &frontendEventBuffer, 8);
        processWifiMachine();
        if(currentState > CONNECTING_AP)
            cyw43_arch_poll();
    }
}

#endif