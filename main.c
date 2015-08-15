/*
 * main.c
 *
 *  Created on: 24.07.2015
 *      Author: hd
 */

#include <libopencm3/stm32/rcc.h>
#include <libopencm3/stm32/gpio.h>
#include <libopencm3/stm32/spi.h>
#include <libopencm3/stm32/flash.h>
#include <string.h>

#include "config.h"
#include "can.h"
#include "systime.h"
#include "ws2812_spi.h"

uint32_t spi = SPI1;

#define NUM_LEDS 10
uint8_t rgb_buf[3 * NUM_LEDS];


void update_led(uint8_t lednum, uint8_t r, uint8_t g, uint8_t b);
void update_led(uint8_t lednum, uint8_t r, uint8_t g, uint8_t b) {
	rgb_buf[lednum*3 + 0] = g;
	rgb_buf[lednum*3 + 1] = r;
	rgb_buf[lednum*3 + 2] = b;

	for (int i=0; i<20; i++) { spi_send(spi, 0); }
	for (unsigned i=0; i<sizeof(rgb_buf); i++) {
		ws2812_write_byte(spi, rgb_buf[i]);
	}
	ws2812_write_byte(spi, 0);
}

void can_rx_message(const can_message_t *msg);
void can_rx_message(const can_message_t *msg) {
	if (msg->id_and_flags == 0x933701ed) {
		uint8_t lednum = msg->data[0];
		uint8_t r = msg->data[1];
		uint8_t g = msg->data[2];
		uint8_t b = msg->data[3];
		//ws2812_write_rgb(spi, r, g, b);
		update_led(lednum, r, g, b);
	}

	if (msg->id_and_flags == 0x933701ef) {
		uint8_t lednum = msg->data[0];
		float h = (msg->data[1] *2) % 360;
		float s = msg->data[2]/255.0;
		float v = msg->data[3]/255.0;

		uint32_t rgb = hsv_to_rgb(h, s, v);
		//ws2812_write_hsv(spi, h, s, v);
		update_led(lednum, (rgb>>16) & 0xFF, (rgb>>8) & 0xFF, (rgb>>0) & 0xFF);
	}
}


int main(void) {

	clock_scale_t clkcfg_96mhz = {
		.pllm = 4,
		.plln = 192,
		.pllp = 4,
		.pllq = 8,
		.flash_config = FLASH_ACR_ICE | FLASH_ACR_DCE | FLASH_ACR_LATENCY_3WS, // TODO check if this is sane (seems to work for 48MHz as well as 120MHz)
		.hpre = 1,
		.ppre1 = 4,
		.ppre2 = 2,
		.power_save = 1,
		.apb1_frequency = 24000000,
		.apb2_frequency = 48000000
	};

	rcc_clock_setup_hse_3v3(&clkcfg_96mhz);
	systime_setup(96000);

	rcc_periph_clock_enable(RCC_GPIOB);
	rcc_periph_clock_enable(RCC_SPI1);

	gpio_mode_setup(GPIOB, GPIO_MODE_AF, GPIO_PUPD_PULLUP, GPIO5);
	gpio_set_af(GPIOB, GPIO_AF5, GPIO5);

	// use PIN B5 as ws2812 open drain output (1K pullup -> +5V)
	gpio_set_output_options(GPIOB, GPIO_OTYPE_OD, GPIO_OSPEED_25MHZ, GPIO5);
	ws2812_init(spi);

	delay_ms(10);
	for(int i=0; i<NUM_LEDS; i++) {
		update_led(i, 0, 0xFF, 0);
	}

	candle_can_init();
	candle_can_register_rx_callback(can_rx_message);
	candle_can_set_bitrate(0, 6, 13, 2, 1);
	candle_can_set_bus_active(0, 1);
	candle_can_set_silent(0, 0);

	uint32_t t_next_heartbeat = 0;

	can_message_t msg_heartbeat;

	msg_heartbeat.channel = 0;
	msg_heartbeat.id_and_flags = 0x933701ea;
	msg_heartbeat.dlc = 4;
	while (1) {
		candle_can_poll();
		if (get_time_ms() >= t_next_heartbeat) {
			msg_heartbeat.data32[0] = get_time_ms();
			candle_can_send_message(&msg_heartbeat);
			t_next_heartbeat = get_time_ms() + 1000;
		}
	}
}
