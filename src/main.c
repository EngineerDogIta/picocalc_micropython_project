#include <stdio.h>
#include "pico/stdlib.h"
#include "pico/binary_info.h"

int main() {
    // Initialize all stdio types, set file handles
    stdio_init_all();

    // Print some information to the console
    printf("Hello, PicoCalc!\n");

    // Initialize the LED pin
    const uint LED_PIN = PICO_DEFAULT_LED_PIN;
    gpio_init(LED_PIN);
    gpio_set_dir(LED_PIN, GPIO_OUT);

    // Main loop
    while (true) {
        gpio_put(LED_PIN, 1);
        sleep_ms(500);
        gpio_put(LED_PIN, 0);
        sleep_ms(500);
    }
} 