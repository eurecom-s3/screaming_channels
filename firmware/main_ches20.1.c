/**
 * Copyright (c) 2014 - 2017, Nordic Semiconductor ASA
 *
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without modification,
 * are permitted provided that the following conditions are met:
 *
 * 1. Redistributions of source code must retain the above copyright notice, this
 *    list of conditions and the following disclaimer.
 *
 * 2. Redistributions in binary form, except as embedded into a Nordic
 *    Semiconductor ASA integrated circuit in a product or a software update for
 *    such product, must reproduce the above copyright notice, this list of
 *    conditions and the following disclaimer in the documentation and/or other
 *    materials provided with the distribution.
 *
 * 3. Neither the name of Nordic Semiconductor ASA nor the names of its
 *    contributors may be used to endorse or promote products derived from this
 *    software without specific prior written permission.
 *
 * 4. This software, with or without modification, must only be used with a
 *    Nordic Semiconductor ASA integrated circuit.
 *
 * 5. Any software provided in binary form under this license must not be reverse
 *    engineered, decompiled, modified and/or disassembled.
 *
 * THIS SOFTWARE IS PROVIDED BY NORDIC SEMICONDUCTOR ASA "AS IS" AND ANY EXPRESS
 * OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
 * OF MERCHANTABILITY, NONINFRINGEMENT, AND FITNESS FOR A PARTICULAR PURPOSE ARE
 * DISCLAIMED. IN NO EVENT SHALL NORDIC SEMICONDUCTOR ASA OR CONTRIBUTORS BE
 * LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
 * CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE
 * GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
 * HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
 * LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
 * OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 *
 */
/** @file
*
* @defgroup nrf_radio_test_example_main main.c
* @{
* @ingroup nrf_radio_test_example
* @brief Radio Test Example Application main file.
*
* This file contains the source code for a sample application using the NRF_RADIO, and is controlled through the serial port.
*
*/


#include <stdint.h>
#include <stdbool.h>
#include <stdio.h>
#include "bsp.h"
#include "nrf.h"
#include "nrf_delay.h"
#include "radio_test.h"
#include "app_uart.h"
#include "app_error.h"
#include "nordic_common.h"
#include "aes.h"

// masked aes implementations from https://github.com/coron/htable
#include "aes_masked/aes_unmasked.h"
#include "aes_masked/aes_share.h"
#include "aes_masked/aes_htable.h"
#include "aes_masked/aes_rp.h"

/*
 * Poor man's hexdump
 *
 * Only for byte arrays! We sleep a bit for longer arrays to make sure that
 * we're not faster than the serial port. Also, newlines every now and then seem
 * to be necessary to flush a buffer somewhere.
 */
#define hexdump(byte_arr)                               \
    do {                                                \
        printf("(%u bytes) ", sizeof(byte_arr));        \
        for (size_t i = 0; i < sizeof(byte_arr); ++i) { \
            if (i % 32 == 0) {                          \
                printf("\r\n");                         \
                nrf_delay_ms(10);                       \
            }                                           \
                                                        \
            printf("%02x", byte_arr[i]);                \
        }                                               \
    } while (0)

static uint8_t mode_          = RADIO_MODE_MODE_Ble_1Mbit;
static uint8_t txpower_       = RADIO_TXPOWER_TXPOWER_0dBm;
static int channel_start_     = 0;
static int channel_end_       = 80;
static int delayms_           = 10;
//static uint8_t rcounter_      = 0;

typedef enum
{
    RADIO_TEST_NOP,             /**< No test running.                                */
    RADIO_TEST_TXCC,            /**< TX constant carrier.                            */
    RADIO_TEST_TXCC_CCM,        /**< TX constant carrier with encryption.            */
    RADIO_TEST_TXCC_CCM_DELAY,  /**< TX constant carrier with encryption and delays. */
    RADIO_TEST_TXMC,            /**< TX modulated carrier.                           */
    RADIO_TEST_TXMC_CCM,        /**< TX modulated carrier with encryption.           */
    RADIO_TEST_TXSWEEP,         /**< TX sweep.                                       */
    RADIO_TEST_RXC,             /**< RX constant carrier.                            */
    RADIO_TEST_RXSWEEP,         /**< RX sweep.                                       */
    RADIO_TEST_NOISYOP,         /**< Some noisy op.                                  */
} radio_tests_t;

typedef enum
{
    AES_UNMASKED,
    AES_RIVAIN_PROUFF,
    AES_RIVAIN_PROUFF_SHARED,
    AES_RAND_TABLE,
    AES_RAND_TABLE_INC,
    AES_RAND_TABLE_WORD,
    AES_RAND_TABLE_WORD_INC,
    AES_RAND_TABLE_SHARED,
    AES_RAND_TABLE_SHARED_WORD,
    AES_RAND_TABLE_SHARED_WORD_INC,
} aes_mask_mode_t;


/* Code for using the CCM block */
typedef struct
{
    uint8_t key[16];
    uint8_t counter[5];
    uint8_t ignored[3];
    uint8_t direction;
    uint8_t iv[8];
} ccm_config_t;

static ccm_config_t ccm_config = {
    {0xaa},                     /* Key.       */
    {0},                        /* Counter.   */
    {0},                        /* Ignored.   */
    0,                          /* Direction. */
    {0}                         /* IV.        */
};

typedef struct {
    uint8_t header;
    uint8_t length;
    uint8_t reserved;
    /* The maximum overall packet length as per Section 23.3 is 258 bytes. The
     * hardware adds two bytes of checksum, and the fields above occupy 3 bytes,
     * so we have 253 bytes left. For encrypted packets, the last 4 bytes
     * contain the Message Integrity Code. */
    uint8_t payload[253];
} ccm_packet_t;

/* Section 29.9.10 specifies the required size of the scratch area to be 43
 * bytes. It lies! The online documentation contains a different statement:
 *
 * "A space of 43 bytes, or (16 + MAXPACKETSIZE) bytes, whatever is largest,
 * must be reserved in RAM."
 * (http://infocenter.nordicsemi.com/index.jsp?topic=%2Fcom.nordic.infocenter.nrf52832.ps.v1.1%2Fccm.html)
 *
 * We accidentally confirmed that small values indeed lead to overflow... */
static uint8_t ccm_scratch[271]; /* MAXPACKETSIZE <= 255 */

static ccm_packet_t ccm_data_in;
static ccm_packet_t ccm_data_out;

/** @brief Enable CCM and configure it for encryption.
 */
static void ccm_enable(uint8_t data_rate)
{
    NRF_CCM->EVENTS_ERROR  = 0;
    NRF_CCM->ENABLE        = (CCM_ENABLE_ENABLE_Enabled << CCM_ENABLE_ENABLE_Pos);

    NRF_CCM->SCRATCHPTR    = (uint32_t)ccm_scratch;
    NRF_CCM->INPTR         = (uint32_t)&ccm_data_in;
    NRF_CCM->OUTPTR        = (uint32_t)&ccm_data_out;
    NRF_CCM->CNFPTR        = (uint32_t)&ccm_config;

    /* Start encryption right after key generation. */
    NRF_CCM->SHORTS        = (CCM_SHORTS_ENDKSGEN_CRYPT_Enabled << CCM_SHORTS_ENDKSGEN_CRYPT_Pos);

    /* Use 8-bit length field, work at the right data rate, encrypt. */
    NRF_CCM->MODE =
        (CCM_MODE_LENGTH_Extended << CCM_MODE_LENGTH_Pos) |
        (data_rate << CCM_MODE_DATARATE_Pos) |
        (CCM_MODE_MODE_Encryption << CCM_MODE_MODE_Pos);
}

/** @brief Disable the CCM block.
 */
static void ccm_disable(void)
{
    NRF_CCM->ENABLE = (CCM_ENABLE_ENABLE_Disabled << CCM_ENABLE_ENABLE_Pos);
    NRF_CCM->INTENCLR = (CCM_INTENCLR_ENDCRYPT_Clear << CCM_INTENCLR_ENDCRYPT_Pos);
    NRF_PPI->CHEN  &= ~PPI_CHEN_CH24_Msk;  /* hard-coded interconnect between READY and KSGEN */
    NRF_PPI->CHENCLR = (1 << 17);          /* custom connection between ENDCRYPT and KSGEN */
}

/** @brief Start the crypto block and wait for it to finish.
 *
 * We assume that the shortcut between ENDKSGEN and CRYPT has been configured,
 * as is the case when ccm_enable() is used.
 */
static void ccm_run_crypto_sync(void)
{
    NRF_CCM->EVENTS_ENDCRYPT = 0;
    NRF_CCM->TASKS_KSGEN     = 1;

    while (NRF_CCM->EVENTS_ENDCRYPT == 0) {
        /* Wait for crypto to finish. */
    }
}

/** @brief Test the CCM crypto block.
 *
 * Run a single encryption, followed by decryption, and test that the resulting
 * data is identical with the input and that the integrity check succeeded.
 */
static void ccm_test_crypto(void)
{
    const uint8_t packet_size = 200; /* arbitrary */

    /*
     * Setup
     */

    ccm_enable(CCM_MODE_DATARATE_1Mbit);
    ccm_data_in.length = packet_size;
    for (int i = 0; i < packet_size; ++i)
        ccm_data_in.payload[i] = i;

    /*
     * Encryption
     */

    ccm_run_crypto_sync();

    /*
     * Decryption
     */

    /* Make sure that we can recognize correct decryption. */
    for (int i = 0; i < packet_size; ++i)
        ccm_data_in.payload[i] = 0x42;

    /* Swap input and output. */
    NRF_CCM->INPTR  = (uint32_t)&ccm_data_out;
    NRF_CCM->OUTPTR = (uint32_t)&ccm_data_in;

    /* Let's go! */
    NRF_CCM->MODE            = (NRF_CCM->MODE & ~CCM_MODE_MODE_Msk) |
        (CCM_MODE_MODE_Decryption << CCM_MODE_MODE_Pos);
    ccm_run_crypto_sync();

    /*
     * Check results
     */
    if (NRF_CCM->MICSTATUS == CCM_MICSTATUS_MICSTATUS_CheckPassed)
        printf("Integrity check passed\r\n");
    else
        printf("Integrity check failed\r\n");

    bool data_correct = true;
    for (int i = 0; i < packet_size; ++i)
        data_correct &= (ccm_data_in.payload[i] == i);

    if (data_correct)
        printf("Data correctly decrypted\r\n");
    else
        printf("Decryption failed\r\n");

    if (NRF_CCM->EVENTS_ERROR)
    {
        printf("CCM reports an error\r\n");
        NRF_CCM->EVENTS_ERROR = 0;
    }

    ccm_disable();
}

typedef enum {
    CCM_RADIO_TX_TRANSMIT_RESULT, /* Transmit the result of the crypto operation. */
    CCM_RADIO_TX_CW,              /* Transmit a continuous wave while running crypto in a loop. */
    CCM_RADIO_TX_CW_WITH_DELAY,   /* Like CCM_RADIO_TX_CW, but delay after each crypto run. */
} ccm_radio_tx_mode_t;

/** @brief Start transmission with on-the-fly encryption.
 *
 * We follow the approach described in Sections 29.4 and 29.5 of the data sheet.
 */
static void ccm_radio_tx(uint8_t tx_power, uint8_t radio_mode, int channel, ccm_radio_tx_mode_t scenario)
{
    /*
     * Data setup
     */

    const uint8_t packet_length = 16; /* one AES block */

    ccm_data_in.length = packet_length;
    for (int i = 0; i < packet_length; ++i)
        ccm_data_in.payload[i] = 0;

    /*
     * Radio configuration
     * (see Table 52 in Section 29.4)
     */

    NRF_RADIO->SHORTS          = 0;
    NRF_RADIO->EVENTS_DISABLED = 0;
    NRF_RADIO->TASKS_DISABLE   = 1;
    while (NRF_RADIO->EVENTS_DISABLED == 0)
    {
        /* Wait for radio to shut down. */
    }
    NRF_RADIO->EVENTS_DISABLED = 0;

    if (scenario == CCM_RADIO_TX_TRANSMIT_RESULT)
        NRF_RADIO->SHORTS =
            RADIO_SHORTS_READY_START_Msk |   /* Start transmission after ramp-up. */
            RADIO_SHORTS_END_DISABLE_Msk |   /* Disable radio after transmission. */
            RADIO_SHORTS_DISABLED_TXEN_Msk;  /* Immediately transmit again after shut-down. */
    else
        NRF_RADIO->SHORTS = RADIO_SHORTS_READY_START_Msk;

    NRF_RADIO->TXPOWER   = (tx_power << RADIO_TXPOWER_TXPOWER_Pos);
    NRF_RADIO->MODE      = (radio_mode << RADIO_MODE_MODE_Pos);
    NRF_RADIO->FREQUENCY = channel;
    NRF_RADIO->PCNF0  =
        (1 << RADIO_PCNF0_S0LEN_Pos) |
        (0 << RADIO_PCNF0_S1LEN_Pos) |
        (8 << RADIO_PCNF0_LFLEN_Pos) |
        (RADIO_PCNF0_S1INCL_Include << RADIO_PCNF0_S1INCL_Pos);
    NRF_RADIO->PCNF1  =
        (RADIO_PCNF1_WHITEEN_Enabled << RADIO_PCNF1_WHITEEN_Pos) |
        (RADIO_PCNF1_ENDIAN_Big << RADIO_PCNF1_ENDIAN_Pos) |
        (3 << RADIO_PCNF1_BALEN_Pos) |
        (0 << RADIO_PCNF1_STATLEN_Pos) |
        (255 << RADIO_PCNF1_MAXLEN_Pos);
    NRF_RADIO->CRCCNF = (RADIO_CRCCNF_LEN_Three << RADIO_CRCCNF_LEN_Pos);

    /*
     * CCM configuration
     */

    /* Translate the radio mode into the correct data rate for CCM. */
    uint32_t ccm_data_rate;
    switch (radio_mode)
    {
    case RADIO_MODE_MODE_Nrf_1Mbit:
    case RADIO_MODE_MODE_Ble_1Mbit:
        ccm_data_rate = CCM_MODE_DATARATE_1Mbit;
        break;

    default:
        /* Our hardware doesn't support 250 kbit/s, so 2 Mbit/s is the only
         * other option. */
        ccm_data_rate = CCM_MODE_DATARATE_2Mbit;
    }

    ccm_enable(ccm_data_rate);

    /*
     * Wire radio and CCM together
     */

    NRF_RADIO->PACKETPTR = (uint32_t)&ccm_data_out;

    switch (scenario)
    {
    case CCM_RADIO_TX_TRANSMIT_RESULT:
        NRF_PPI->CHEN = PPI_CHEN_CH24_Msk;  /* hard-coded interconnect between READY and KSGEN */
        break;

    case CCM_RADIO_TX_CW:
        /* Restart CCM whenever it finishes. */
        NRF_PPI->CH[17].EEP = (uint32_t)&NRF_CCM->EVENTS_ENDCRYPT;
        NRF_PPI->CH[17].TEP = (uint32_t)&NRF_CCM->TASKS_KSGEN;
        NRF_PPI->CHENSET = (1 << 17);
        break;

    case CCM_RADIO_TX_CW_WITH_DELAY:
        /* Trigger an interrupt when done; the handler will sleep and restart. */
        NRF_CCM->INTENSET = (CCM_INTENSET_ENDCRYPT_Set << CCM_INTENSET_ENDCRYPT_Pos);
        break;
    }

    /*
     * Start everything
     */

    NRF_RADIO->TASKS_TXEN = 1;

    /* If we don't transmit the result, CCM is not triggered by the radio, so we
     * have to start it manually. */
    if (scenario != CCM_RADIO_TX_TRANSMIT_RESULT)
        NRF_CCM->TASKS_KSGEN = 1;
}

void CCM_AAR_IRQHandler(void)
{
    NRF_CCM->EVENTS_ENDCRYPT = 0;

    /* Sleeping in an interrupt handler is not the most elegant thing to do, but
     * since our sleeps are relatively short the solution works well enough for
     * now. If ever we run into problems we can use a timer instead. */
    nrf_delay_us(10);

    /* Start a new round of crypto. */
    NRF_CCM->TASKS_KSGEN = 1;
}


#define BELL 7 // Bell

#define UART_TX_BUF_SIZE 512                                                          /**< UART TX buffer size. */
#define UART_RX_BUF_SIZE 1                                                            /**< UART RX buffer size. */

void uart_error_handle(app_uart_evt_t * p_event)
{
    if (p_event->evt_type == APP_UART_COMMUNICATION_ERROR)
    {
        APP_ERROR_HANDLER(p_event->data.error_communication);
    }
    else if (p_event->evt_type == APP_UART_FIFO_ERROR)
    {
        APP_ERROR_HANDLER(p_event->data.error_code);
    }
}

/** @brief Function for configuring all peripherals used in this example.
*/
static void init(void)
{
    NRF_RNG->TASKS_START = 1;

    // Start 16 MHz crystal oscillator
    NRF_CLOCK->EVENTS_HFCLKSTARTED  = 0;
    NRF_CLOCK->TASKS_HFCLKSTART     = 1;

    // Wait for the external oscillator to start up
    while (NRF_CLOCK->EVENTS_HFCLKSTARTED == 0)
    {
        // Do nothing.
    }
}


/** @brief Function for outputting usage info to the serial port.
*/
static void help(void)
{
    printf("Usage:\r\n");
    printf("a: Enter start channel for sweep/channel for constant carrier\r\n");
    printf("b: Enter end channel for sweep\r\n");
    printf("c: Start TX carrier\r\n");
    printf("d: Enter time on each channel (1ms-99ms)\r\n");
    printf("e: Cancel sweep/carrier\r\n");
    printf("f: Toggle CCM power\r\n");
    printf("g: Change CCM counter\r\n");
    printf("i: Start (unmodulated) TX carrier with active CCM\r\n");
    printf("j: Start (unmodulated) TX carrier with active CCM and delays\r\n");
    printf("l: Test the crypto hardware\r\n");
    nrf_delay_ms(10);
    printf("m: Enter data rate\r\n");
    printf("o: Start modulated TX carrier\r\n");
    printf("p: Enter output power\r\n");
    printf("q: Start modulated TX carrier with encryption\r\n");
    printf("s: Print current delay, channels and so on\r\n");
    printf("r: Start RX sweep\r\n");
    printf("t: Start TX sweep\r\n");
    printf("x: Start RX carrier\r\n");
    printf("y: Start noisy operation\r\n");
    printf("z: End noisy operation\r\n");
    nrf_delay_ms(10);
    printf("n: Enter tiny_aes_128 mode\r\n");
    printf("   p: Enter plaintext\r\n");
    printf("   k: Enter key\r\n");
    printf("   e: Encrypt\r\n");
    printf("   n: Set number of repetitions\r\n");
    printf("   r: Run repeated encryption\r\n");
    printf("   q: Quit tiny_aes_128 mode\r\n");
    nrf_delay_ms(10);
    printf("v: Enter simplified power analysis mode\r\n");
    printf("   m: Enter switching mask\r\n");
    printf("   s: Switch\r\n");
    printf("   q: Quit power analysis mode\r\n");
    nrf_delay_ms(10);
    printf("u: Enter hwcrypto mode\r\n");
    printf("   p: Enter plaintext\r\n");
    printf("   k: Enter key\r\n");
    printf("   e: Encrypt\r\n");
    printf("   o: Print encrypted ciphertext\r\n");
    printf("   q: Quit hwcrypto mode\r\n");
    nrf_delay_ms(10);
    printf("w: Enter aes_masked mode\r\n");
    printf("   0: Set mask mode to UNMASKED\r\n");
    printf("   1: Set mask mode to RIVAIN-PROUFF\r\n");
    printf("   2: Set mask mode to RIVAIN-PROUFF-SHARED\r\n");
    printf("   3: Set mask mode to RAND-TABLE\r\n");
    nrf_delay_ms(10);
    printf("   4: Set mask mode to RAND-TABLE-INC\r\n");
    printf("   5: Set mask mode to RAND-TABLE-WORD\r\n");
    printf("   6: Set mask mode to RAND-TABLE-WORD-INC\r\n");
    nrf_delay_ms(10);
    printf("   7: Set mask mode to RAND-TABLE-SHARED\r\n");
    printf("   8: Set mask mode to RAND-TABLE-SHARED-WORD\r\n");
    printf("   9: Set mask mode to RAND-TABLE-SHARED-WORD-INC\r\n");
    nrf_delay_ms(10);
    printf("   p: Enter plaintext\r\n");
    printf("   k: Enter key\r\n");
    printf("   e: Encrypt\r\n");
    printf("   o: Print encrypted ciphertext\r\n");
    printf("   n: Set number of repetitions\r\n");
    nrf_delay_ms(10);
    printf("   r: Run repeated encryption\r\n");
    printf("   q: Quit aes_masked mode\r\n");
}


/** @brief Function for reading the data rate.
*/
void get_datarate(void)
{
    uint8_t c;

#ifndef NRF52840_XXAA
    printf("Enter data rate ('0'=250 Kbit/s, '1'=1 Mbit/s, '2'=2 Mbit/s and '3'=BLE 1 Mbit/s):\r\n");
#else
    printf("Enter data rate ('1'=1 Mbit/s, '2'=2 Mbit/s and '3'=BLE 1 Mbit/s):\r\n");
#endif //NRF52840_XXAA
    while (true)
    {
        scanf("%c",&c);
        if ((c >= '0') && (c <= '2'))
        {
            printf("%c\r\n",c);
            break;
        }
        else
        {
            printf("%c\r\n",BELL);
        }
    }

    if (c == '1')
    {
        mode_ = RADIO_MODE_MODE_Nrf_1Mbit;
    }
#ifndef NRF52840_XXAA
    else if (c == '0')
    {
        mode_ = RADIO_MODE_MODE_Nrf_250Kbit;
    }
#endif //NRF52840_XXAA
    else if (c == '2')
    {
        mode_ = RADIO_MODE_MODE_Nrf_2Mbit;
    }
    else if (c == '3')
    {
        mode_ = RADIO_MODE_MODE_Ble_1Mbit;
    }
    printf("\r\n");
}


/** @brief Function for reading the output power.
*/
void get_power(void)
{
    uint8_t c;

    printf("Enter output power ('0'=+4 dBm, '1'=0 dBm,...,'7'=-30 dBm):\r\n");
    while (true)
    {
        scanf("%c",&c);
        if ((c >= '0') && (c <= '7'))
        {
            UNUSED_VARIABLE(app_uart_put(c));
            break;
        }
        else
        {
            UNUSED_VARIABLE(app_uart_put(BELL));
        }
    }

    switch (c)
    {
        case '0':
            txpower_ =  RADIO_TXPOWER_TXPOWER_Pos4dBm;
            break;

        case '1':
            txpower_ =  RADIO_TXPOWER_TXPOWER_0dBm;
            break;

        case '2':
            txpower_ = RADIO_TXPOWER_TXPOWER_Neg4dBm;
            break;

        case '3':
            txpower_ = RADIO_TXPOWER_TXPOWER_Neg8dBm;
            break;

        case '4':
            txpower_ = RADIO_TXPOWER_TXPOWER_Neg12dBm;
            break;

        case '5':
            txpower_ = RADIO_TXPOWER_TXPOWER_Neg16dBm;
            break;

        case '6':
            txpower_ = RADIO_TXPOWER_TXPOWER_Neg20dBm;
            break;

        case '7':
            // fall through

        default:
            txpower_ = RADIO_TXPOWER_TXPOWER_Neg30dBm;
            break;
    }
    printf("\r\n");
}


/** @brief Function for printing parameters to the serial port.
*/
void print_parameters(void)
{
    printf("Parameters:\r\n");
    switch (mode_)
    {
#ifndef NRF52840_XXAA
        case RADIO_MODE_MODE_Nrf_250Kbit:
            printf("Data rate...........: 250 Kbit/s\r\n");
            break;
#endif //NRF52840_XXAA

        case RADIO_MODE_MODE_Nrf_1Mbit:
            printf("Data rate...........: 1 Mbit/s\r\n");
            break;

        case RADIO_MODE_MODE_Nrf_2Mbit:
            printf("Data rate...........: 2 Mbit/s\r\n");
            break;

        case RADIO_MODE_MODE_Ble_1Mbit:
            printf("Data rate...........: BLE 1 Mbit/s\r\n");
            break;
    }

    switch (txpower_)
    {
        case RADIO_TXPOWER_TXPOWER_Pos4dBm:
            printf("TX Power............: +4 dBm\r\n");
            break;

        case RADIO_TXPOWER_TXPOWER_0dBm:
            printf("TX Power............: 0 dBm\r\n");
            break;

        case RADIO_TXPOWER_TXPOWER_Neg4dBm:
            printf("TX Power............: -4 dBm\r\n");
            break;

        case RADIO_TXPOWER_TXPOWER_Neg8dBm:
            printf("TX Power............: -8 dBm\r\n");
            break;

        case RADIO_TXPOWER_TXPOWER_Neg12dBm:
            printf("TX Power............: -12 dBm\r\n");
            break;

        case RADIO_TXPOWER_TXPOWER_Neg16dBm:
            printf("TX Power............: -16 dBm\r\n");
            break;

        case RADIO_TXPOWER_TXPOWER_Neg20dBm:
            printf("TX Power............: -20 dBm\r\n");
            break;

        case RADIO_TXPOWER_TXPOWER_Neg30dBm:
            printf("TX Power............: -30 dBm\r\n");
            break;

        default:
            // No implementation needed.
            break;

    }
    printf("(Start) Channel.....: %d\r\n",channel_start_);
    printf("End Channel.........: %d\r\n",channel_end_);
    printf("Time on each channel: %d ms\r\n",delayms_);
    printf("CCM block...........: %s\r\n", NRF_CCM->ENABLE ? "on" : "off");
    printf("Key.................: "); hexdump(ccm_config.key); printf("\r\n");
    printf("Counter.............: "); hexdump(ccm_config.counter); printf("\r\n");
    printf("IV..................: "); hexdump(ccm_config.iv); printf("\r\n");
    printf("Encrypted data......: "); hexdump(ccm_data_out.payload); printf("\r\n");
    printf("Low frequency clock.: %s\r\n",
           (NRF_CLOCK->LFCLKSTAT & CLOCK_LFCLKSTAT_STATE_Msk) ? "on" : "off");
}

bool timer1_init()
{
    NRF_TIMER1->TASKS_STOP  = 1;
    NRF_TIMER1->TASKS_CLEAR = 1;
    NRF_TIMER1->INTENCLR    = 0xffffffff;
    NRF_TIMER1->INTENSET    = TIMER_INTENSET_COMPARE0_Msk;

    NRF_TIMER1->SHORTS    = (1 << TIMER_SHORTS_COMPARE0_CLEAR_Pos);
    NRF_TIMER1->PRESCALER = 22; // f_timer = 16MHz/(2^prescalar)

    NRF_TIMER1->CC[0] = 0;

    NVIC_ClearPendingIRQ(TIMER1_IRQn);
    NVIC_EnableIRQ(TIMER1_IRQn);
    return true;
}

void start_noisy_op(void)
{
    NRF_TIMER1->TASKS_CLEAR = 1;
    NRF_TIMER1->TASKS_START = 1;
}

void stop_noisy_op(void)
{
    NRF_TIMER1->TASKS_STOP = 1;
}

void TIMER1_IRQHandler()
{
    //rcounter_++;
    //printf("timer event: %d\r\n",rcounter_);
    bsp_board_led_invert(0); //flip LED0
    NRF_POWER->GPREGRET ^= 0xFFFFFFFF; //flip/unflip a register
    NRF_TIMER1->EVENTS_COMPARE[0] = 0;
}

/*
 * @brief Function to read 16 integers from the serial line and to write them in
 * to a bytearray
 */
void read_128(uint8_t* in){
    int tmp;
    for(int i=0;i<16;i++){
        scanf("%d",&tmp);
        in[i] = (uint8_t)tmp;
    }
    /*scanf("%hhd %hhd %hhd %hhd %hhd %hhd %hhd %hhd %hhd %hhd %hhd %hhd %hhd %hhd %hhd %hhd",*/
           /*&in[ 0],&in[ 1],&in[ 2],&in[ 3],*/
           /*&in[ 4],&in[ 5],&in[ 6],&in[ 7],*/
           /*&in[ 8],&in[ 9],&in[10],&in[11],*/
           /*&in[12],&in[13],&in[14],&in[15]);*/
}

/*
 * @brief Function to write a byte array as 16 integers to the serial line
 */
void write_128(uint8_t* out){
    printf("%d %d %d %d %d %d %d %d %d %d %d %d %d %d %d %d\r\n",
           out[ 0],out[ 1],out[ 2],out[ 3],
           out[ 4],out[ 5],out[ 6],out[ 7],
           out[ 8],out[ 9],out[10],out[11],
           out[12],out[13],out[14],out[15]);
}

/*
 * brief Function that creates a preable for easy alignment
 */
void preamble(){
    typedef uint8_t state_t[4][4];
    state_t state = {0};
    uint8_t i,j;
    for(i=0;i<4;++i)
    {
      for(j = 0; j < 4; ++j)
      {
        state[i][j] ^= 0xff;
      }
    }
    for(i=0;i<4;++i)
    {
      for(j = 0; j < 4; ++j)
      {
        state[i][j] ^= 0xff;
      }
    }
    for(i=0;i<4;++i)
    {
      for(j = 0; j < 4; ++j)
      {
        state[i][j] ^= 0xff;
      }
    }
    for(i=0;i<4;++i)
    {
      for(j = 0; j < 4; ++j)
      {
        state[i][j] ^= 0xff;
      }
    }
    for(i=0;i<4;++i)
    {
      for(j = 0; j < 4; ++j)
      {
        state[i][j] ^= 0xff;
      }
    }
}

/*
 * @brief Function to handle tiny_aes_128 attacks
 */
void tiny_aes_128_mode(){
    printf("Entering tiny_aes_128 mode\r\n");
    uint8_t control;
    bool exit = false;
    uint8_t key[16] = {0};
    uint8_t in[16] = {0};
    uint8_t out[16] = {0};
    uint32_t num_repetitions = 1;


    while(!exit){
        scanf("%c",&control);
        switch(control){
            case 'p':
                read_128(in);
                write_128(in); // dbg
                break;
            case 'k':
                read_128(key);
                write_128(key); // dbg
                break;
            case 'e':
                AES128_ECB_encrypt(in,key,out);
                break;
            case 'n':           /* set number of repetitions */
                scanf("%lu", &num_repetitions);
                printf("Setting number of repetitions to %ld\r\n", num_repetitions);
                break;
            case 'r':           /* repeated encryption */
                for (uint32_t i = 0; i < num_repetitions; ++i) {
                    for(uint32_t j = 0; j < 0xff; j++);
                    AES128_ECB_encrypt(in, key, out);
                }
                printf("Done\r\n");
                break;
            case 'o':
                write_128(out);
                break;
            case 'q':
                exit = true;
                break;
            default:
                break;
        }
    }
    printf("Exiting tiny_aes_128 mode\r\n");
}

/*
 * @brief Function to handle hw crypto attacks
 */
void hwcrypto_mode(){
    printf("Entering hwcrypto mode\r\n");
    uint8_t control;
    bool exit = false;
    ccm_enable(CCM_MODE_DATARATE_1Mbit);
    ccm_data_in.length = 16;
    uint8_t init[16];
    uint32_t num_repetitions = 1;
    while(!exit){
        scanf("%c",&control);
        switch(control){
            case 'p':
                read_128(ccm_data_in.payload);
                write_128(ccm_data_in.payload); // dbg
                break;
            case 'k':
                read_128(ccm_config.key);
                write_128(ccm_config.key); // dbg
                break;
            case 'i':
                read_128(init);
                write_128(init); // dbg
                for(int i = 0; i < 5; i++)
                    ccm_config.counter[i] = init[i + 11];
                for(int i = 0; i < 8; i++)
                    ccm_config.iv[i] = init[i + 3];
                break;
            case 'e':
                preamble();
                ccm_run_crypto_sync();
                break;
            case 'n':           /* set number of repetitions */
                scanf("%lu", &num_repetitions);
                printf("Setting number of repetitions to %ld\r\n", num_repetitions);
                break;
            case 'r':           /* repeated encryption */
                for (uint32_t i = 0; i < num_repetitions; ++i) {
                    preamble();
                    ccm_run_crypto_sync();
                }
                printf("Done\r\n");
                break;
            case 'q':
                exit = true;
                break;
            default:
                break;
        }
    }
    ccm_disable();
    printf("Exiting hwcrypto mode\r\n");
}

void do_aes_masked(aes_mask_mode_t mode, uint8_t *in, uint8_t *out, uint8_t *key, uint32_t num_repetition)
{
    int i;

    switch(mode)
    {
        case AES_UNMASKED:
            run_aes(in, out, key, num_repetition);
            break;

        case AES_RIVAIN_PROUFF:
            for( i=0 ; i < num_repetition ; i++)
                aes_rp(in, out, key);
            break;

        case AES_RIVAIN_PROUFF_SHARED:
            run_aes_share(in,out,key,3,&subbyte_rp_share,num_repetition);
            break;
        case AES_RAND_TABLE:
            run_aes_share(in,out,key,3,&subbyte_htable,num_repetition); 
            break;

        case AES_RAND_TABLE_INC:
            run_aes_share(in,out,key,3,&subbyte_htable_inc,num_repetition); 
            break;

        case AES_RAND_TABLE_WORD:
            run_aes_share(in,out,key,3,&subbyte_htable_word,num_repetition); 
            break;

        case AES_RAND_TABLE_WORD_INC:
            run_aes_share(in,out,key,3,&subbyte_htable_word_inc,num_repetition); 
            break;

        case AES_RAND_TABLE_SHARED:
            run_aes_common_share(in,out,key,3,&subbyte_cs_htable,num_repetition); 
            break;

        case AES_RAND_TABLE_SHARED_WORD:
            run_aes_common_share(in,out,key,3,&subbyte_cs_htable_word,num_repetition); 
            break;

        case AES_RAND_TABLE_SHARED_WORD_INC:
            run_aes_common_share(in,out,key,3,&subbyte_cs_htable_word_inc,num_repetition); 
            break;

        default:
            printf("Not implemented yet \r\n");
    }
}

/*  Function for the aes_masked mode */
void aes_masked_mode(){
    uint8_t control;
    bool exit = false;
    uint8_t key[16] = {0};
    uint8_t in[16] = {0};
    uint8_t out[16] = {0};
    uint32_t num_repetitions = 1;
    aes_mask_mode_t mask_mode = AES_UNMASKED;

    printf("Entering aes_masked mode\r\n");
    while(!exit){
        scanf("%c",&control);
        switch(control){
            case '0':
            case '1':
            case '2':
            case '3':
            case '4':
            case '5':
            case '6':
            case '7':
            case '8':
            case '9':
                mask_mode = (aes_mask_mode_t) control - '0';
                printf("Switched masking mode to mode no: %d\r\n", mask_mode);
                break;
            case 'p':
                read_128(in);
                write_128(in); // dbg
                break;
            case 'k':
                read_128(key);
                write_128(key); // dbg
                break;
            case 'e':
                do_aes_masked(mask_mode, in, out, key, 1); 
                break;
            case 'n':           /* set number of repetitions */
                scanf("%lu", &num_repetitions);
                printf("Setting number of repetitions to %ld\r\n", num_repetitions);
                break;
            case 'r':           /* repeated encryption */
                do_aes_masked(mask_mode, in, out, key, num_repetitions); 
                printf("Done\r\n");
                break;
            case 'o':
                write_128(out);
                break;
            case 'q':
                exit = true;
                break;
            default:
                break;
        }
    }
    printf("Exiting aes_masked mode\r\n");
}



/*
 * @brief Function that models the swithcing activity of the AES state
 */
void switch_state(uint8_t* switching_mask){
    typedef uint8_t state_t[4][4];
    state_t state = {0};
    uint8_t i,j;
    for(int q=0;q<7;q++){
    for(i=0;i<4;++i)
    {
      for(j = 0; j < 4; ++j)
      {
        state[i][j] ^= switching_mask[i * 4 + j];
      }
    }
    for(int k=0;k<100;k++){
    }
    }
}

/*
 * @brief Function to handle power analysis
 */
void power_analysis_mode(){
    printf("Entering power analysis mode\r\n");
    uint8_t control;
    bool exit = false;
    uint8_t switching_mask[16] = {0};
    while(!exit){
        scanf("%c",&control);
        switch(control){
            case 'p':
                read_128(switching_mask);
                write_128(switching_mask); // dbg
                break;
            case 's':
                switch_state(switching_mask);
                break;
            case 'q':
                exit = true;
                break;
            default:
                break;
        }
    }
    printf("Exiting power analysis mode\r\n");
}

typedef struct {
    bool sweep;
    bool ccm;
} main_state_t;

/** @brief Helper to switch off all activity.
 */
void all_off(main_state_t* state)
{
    if (state->sweep)
    {
        radio_sweep_end();
        state->sweep = false;
    }
    if (state->ccm)
    {
        ccm_disable();
        state->ccm = false;
    }
}

/** @brief Function for main application entry.
 */
int main(void)
{
    uint32_t err_code;
    radio_tests_t test     = RADIO_TEST_NOP;
    radio_tests_t cur_test = RADIO_TEST_NOP;
    main_state_t state     = {false, false};

    init();
    const app_uart_comm_params_t comm_params =
    {
        RX_PIN_NUMBER,
        TX_PIN_NUMBER,
        RTS_PIN_NUMBER,
        CTS_PIN_NUMBER,
        APP_UART_FLOW_CONTROL_DISABLED,
        false,
        UART_BAUDRATE_BAUDRATE_Baud115200
    };

    APP_UART_FIFO_INIT(&comm_params,
                         UART_RX_BUF_SIZE,
                         UART_TX_BUF_SIZE,
                         uart_error_handle,
                         APP_IRQ_PRIORITY_LOWEST,
                         err_code);

    APP_ERROR_CHECK(err_code);
    bsp_board_leds_init();
    printf("RF Test\r\n");
    NVIC_EnableIRQ(TIMER0_IRQn);
    NVIC_EnableIRQ(TIMER1_IRQn);
    NVIC_EnableIRQ(CCM_AAR_IRQn);
    __enable_irq();
    while (true)
    {
        uint8_t control;
        scanf("%c",&control);
        switch (control)
        {
            case 'a':
                while (true)
                {
                    printf("Enter start channel (two decimal digits, 00 to 80):\r\n");
                    scanf("%d",&channel_start_);
                    if ((channel_start_ <= 80)&&(channel_start_ >= 0))
                    {
                        printf("%d\r\n", channel_start_);
                        break;
                    }

                    printf("Channel must be between 0 and 80\r\n");
                }
                test = cur_test;
                break;

            case 'b':
                while (true)
                {
                    printf("Enter end channel (two decimal digits, 00 to 80):\r\n");
                    scanf("%d",&channel_end_);
                    if ((channel_end_ <= 80)&&(channel_start_ >= 0))
                    {
                        printf("%d\r\n", channel_end_);
                        break;
                    }
                    printf("Channel must be between 0 and 80\r\n");
                }
                test = cur_test;
                break;

            case 'c':
                test = RADIO_TEST_TXCC;
                break;

            case 'd':
                while (true)
                {
                    printf("Enter delay in ms (two decimal digits, 01 to 99):\r\n");
                    scanf("%d",&delayms_);
                    if ((delayms_ > 0) && (delayms_ < 100))
                    {
                        printf("%d\r\n", delayms_);
                        break;
                    }
                    printf("Delay must be between 1 and 99\r\n");
                }
                test = cur_test;
                break;

            case 'e':
                radio_sweep_end();
                ccm_disable();
                cur_test = RADIO_TEST_NOP;
                break;

            case 'f':
                NRF_CCM->ENABLE = NRF_CCM->ENABLE ?
                    CCM_ENABLE_ENABLE_Disabled : CCM_ENABLE_ENABLE_Enabled;
                break;

            case 'g':
                ccm_config.counter[0]++;
                break;

            case 'i':
                test = RADIO_TEST_TXCC_CCM;
                printf("TX modulated carrier with encryption\r\n");
                break;

            case 'j':
                test = RADIO_TEST_TXCC_CCM_DELAY;
                printf("TX modulated carrier with encryption and delays\r\n");
                break;

            case 'l':
                if (cur_test != RADIO_TEST_NOP || test != RADIO_TEST_NOP)
                    printf("Disable running test first!\r\n");
                else
                    ccm_test_crypto();
                break;

            case 'm':
                get_datarate();
                test = cur_test;
                break;
            case 'w':
                aes_masked_mode();
                break;

            case 'n':
                tiny_aes_128_mode();
                break;

            case 'o':
                test = RADIO_TEST_TXMC;
                printf("TX modulated carrier\r\n");
                break;

            case 'p':
                get_power();
                test = cur_test;
                break;

            case 'q':
                test = RADIO_TEST_TXMC_CCM;
                printf("TX modulated carrier with encryption\r\n");
                break;

            case 'r':
                test = RADIO_TEST_RXSWEEP;
                printf("RX Sweep\r\n");
                break;

            case 's':
                print_parameters();
                break;

            case 't':
                test = RADIO_TEST_TXSWEEP;
                printf("TX Sweep\r\n");
                break;

            case 'u':
                hwcrypto_mode();
                break;

            case 'v':
                power_analysis_mode();
                break;

            case 'x':
                test = RADIO_TEST_RXC;
                printf("RX constant carrier\r\n");
                break;

            case 'y':
                test = RADIO_TEST_NOISYOP;
                printf("Exercise the processor\r\n");
                break;

            case 'z':
                stop_noisy_op();
                test = RADIO_TEST_NOP;
                printf("Relax the processor\r\n");
                break;

            case 'h':
                help();
                break;

            default:
                // No implementation needed
                break;
        }

        switch (test)
        {
            case RADIO_TEST_TXCC:
                all_off(&state);
                radio_tx_carrier(txpower_, mode_, channel_start_);
                cur_test = test;
                test     = RADIO_TEST_NOP;
                break;

            case RADIO_TEST_TXCC_CCM:
                all_off(&state);
                state.ccm = true;
                ccm_radio_tx(txpower_, mode_, channel_start_, CCM_RADIO_TX_CW);
                cur_test = test;
                test     = RADIO_TEST_NOP;
                break;

            case RADIO_TEST_TXCC_CCM_DELAY:
                all_off(&state);
                state.ccm = true;
                ccm_radio_tx(txpower_, mode_, channel_start_, CCM_RADIO_TX_CW_WITH_DELAY);
                cur_test = test;
                test     = RADIO_TEST_NOP;
                break;

            case RADIO_TEST_TXMC:
                all_off(&state);
                radio_modulated_tx_carrier(txpower_, mode_, channel_start_);
                cur_test = test;
                test     = RADIO_TEST_NOP;
                break;

            case RADIO_TEST_TXMC_CCM:
                all_off(&state);
                state.ccm = true;
                ccm_radio_tx(txpower_, mode_, channel_start_, CCM_RADIO_TX_TRANSMIT_RESULT);
                cur_test = test;
                test     = RADIO_TEST_NOP;
                break;

            case RADIO_TEST_TXSWEEP:
                all_off(&state);
                radio_tx_sweep_start(txpower_, mode_, channel_start_, channel_end_, delayms_);
                state.sweep = true;
                cur_test = test;
                test     = RADIO_TEST_NOP;
                break;

            case RADIO_TEST_RXC:
                all_off(&state);
                radio_rx_carrier(mode_, channel_start_);
                cur_test = test;
                test     = RADIO_TEST_NOP;
                break;

            case RADIO_TEST_RXSWEEP:
                radio_rx_sweep_start(mode_, channel_start_, channel_end_, delayms_);
                state.sweep = true;
                cur_test = test;
                test     = RADIO_TEST_NOP;
                break;

            case RADIO_TEST_NOISYOP:
                timer1_init();
                start_noisy_op();
                state.sweep    = false;
                cur_test = test;
                test     = RADIO_TEST_NOP;
                break;

            case RADIO_TEST_NOP:
                // Fall through.
            default:
                // No implementation needed.
                break;
        }
    }
}

/** @} */
