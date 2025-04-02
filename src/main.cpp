#include "pico/stdlib.h"
#include <cstdio>

int main() {
    // Initialize all stdio types, USB, UART
    stdio_init_all();

    // Initialize LED pin
    const uint LED_PIN = PICO_DEFAULT_LED_PIN;
    gpio_init(LED_PIN);
    gpio_set_dir(LED_PIN, GPIO_OUT);

    printf("Pico Project Started!\n");

    while (true) {
        // Blink LED
        gpio_put(LED_PIN, 1);
        sleep_ms(500);
        gpio_put(LED_PIN, 0);
        sleep_ms(500);
        
        // Print status
        printf("LED Toggle\n");
    }
} 