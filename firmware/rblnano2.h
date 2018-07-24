#ifndef RBLNANO2_H
#define RBLNANO2_H

#ifdef __cplusplus
extern "C" {
#endif

#include "nrf_gpio.h"

// LEDs definitions for RBL NANO 2
#define LEDS_NUMBER    1

#define LED_OB         11
#define LED_START      LED_OB
#define LED_STOP       LED_OB
   
#define LEDS_ACTIVE_STATE 0

#define BSP_LED_0	     LED_OB

#define LEDS_LIST      { LED_OB }
#define BSP_LED_0_MASK (1<<BSP_LED_0)
#define LEDS_MASK      (BSP_LED_0)
#define LEDS_INV_MASK  LEDS_MASK	

#define BUTTONS_NUMBER 0

#define RX_PIN_NUMBER  30
#define TX_PIN_NUMBER  29
#define CTS_PIN_NUMBER 28
#define RTS_PIN_NUMBER 2
#define HWFC           true

#ifdef __cplusplus
}
#endif

#endif // RBLNANO2_H
