# PicoCalc Interactive Shell

This project implements a simple interactive shell environment for the Clockwork PicoCalc device, utilizing its ILI9488 display and keypad.

## Overview

The goal is to create a basic terminal-like interface directly on the PicoCalc hardware. Users can type characters using the physical keypad, and the corresponding text appears on the display. This serves as a foundation for potentially more complex applications running directly on the device.

## Hardware Architecture

This firmware is designed specifically for the **Clockwork PicoCalc Mainboard V2.0**.

Key components utilized:
- **CPU**: Raspberry Pi Pico (RP2040)
- **Display**: ILI9488 TFT LCD (320x320, SPI Interface)
- **Input**: 6x6 Keypad Matrix controlled by an STM32F103R8T6 microcontroller

The PicoCalc uses a **dual-MCU architecture**:
1. The STM32F103 handles the physical keyboard matrix scanning
2. The Raspberry Pi Pico handles the display, application logic, and communication with the STM32

For detailed hardware specifications, pinouts, and schematics, please refer to the `PICOCALC_SPECS.md` document in this repository.

## Keyboard Implementation

Based on analysis of the official firmware in the [Clockwork GitHub repository](https://github.com/clockworkpi/PicoCalc/tree/master/Code/picocalc_keyboard), the keyboard has a specialized architecture:

### Hardware Design
- The keyboard matrix is directly connected to the STM32F103 microcontroller, not to the Pico
- The STM32 scans a 6x6 key matrix using direct GPIO pins:
  - Column pins: PIN_PA05 through PIN_PA10 (outputs)
  - Row pins: PIN_PA11 through PIN_PA16 (inputs)

### Communication
The STM32 keyboard controller communicates with the Raspberry Pi Pico, likely through a custom protocol. Implementation options include:

1. **GPIO-based Communication**: Using specific GPIO pins for signaling between the controllers
2. **UART/Serial Communication**: Standard serial interface
3. **Custom I2C Protocol**: Non-standard I2C implementation that requires custom handling

Our current focus is on implementing a proper interface to communicate with the STM32 keyboard controller.

## Current Features

- Initialization of the ILI9488 display
- Basic screen clearing and pixel writing
- Bitmap font rendering
- Simple shell interface framework

## Files

- `main.py`: Main application entry point
- `ili9488.py`: Display driver for the ILI9488 TFT LCD
- `font.py`: Bitmap font definitions
- `graphics.py`: Graphics drawing functions
- `keyboard.py`: Keyboard interface module (being updated for STM32 communication)
- `i2c_scanner.py`: Utility for general I2C device detection

## Setup

1. **Install MicroPython:** Flash the latest stable MicroPython firmware for the Raspberry Pi Pico onto your PicoCalc. You can find the firmware and instructions on the [Raspberry Pi documentation site](https://www.raspberrypi.com/documentation/microcontrollers/micropython.html). Remember to put the Pico into BOOTSEL mode (hold SW1 while plugging in USB).
2. **Copy Files:** Connect to the Pico's REPL (e.g., using Thonny IDE). Copy all the required `.py` files to the root directory of the Pico's filesystem.
3. **Reset:** Reset the Pico (either physically or via CTRL+D in the REPL). The `main.py` script should run automatically.

## Usage

Once the firmware is running:
- The display will initialize and show a prompt (e.g., `> `).
- Press keys on the physical keypad. The corresponding characters should appear on the screen.
- Use the designated Backspace and Enter keys for basic line editing and "command" entry.

## Development Plan

1. [x] Basic Display Initialization (`main.py` initial version)
2. [x] Refactor display logic into `ili9488.py`
3. [x] Implement bitmap font (`font.py`) and character drawing (`graphics.py`)
4. [ ] Implement proper communication with the STM32 keyboard controller
5. [ ] Integrate components into `main.py` to create the interactive shell loop
6. [ ] Add basic scrolling or line wrapping

## Contributing

Feel free to submit issues or pull requests if you have suggestions or improvements.

## Development Journey

During our development, we initially assumed the keyboard was directly connected to the Raspberry Pi Pico's GPIO pins. After extensive testing and analysis of the official firmware, we discovered it actually uses a dual-MCU architecture with an STM32F103 handling the keyboard matrix.

Our early approaches focused on direct GPIO matrix scanning and I2C communication attempts from the Pico, which were unsuccessful because they didn't match the actual hardware architecture. Understanding the STM32's role was key to developing a proper implementation.

The current approach focuses on implementing the correct communication protocol between the Pico and the STM32 keyboard controller.
