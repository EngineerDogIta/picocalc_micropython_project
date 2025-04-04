# PicoCalc Interactive Shell

![MicroPython](https://img.shields.io/badge/MicroPython-2B2728?style=for-the-badge&logo=micropython&logoColor=white)
![Raspberry Pi](https://img.shields.io/badge/Raspberry%20Pi-A22846?style=for-the-badge&logo=Raspberry%20Pi&logoColor=white)
![Cursor](https://img.shields.io/badge/Developed%20with-Cursor-blue?style=for-the-badge&logo=cursor&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![I2C](https://img.shields.io/badge/I2C-Protocol-lightgrey?style=for-the-badge)

This project implements a simple interactive shell environment for the Clockwork PicoCalc device, utilizing its ILI9488 display and keypad.

## Overview

The goal is to create a basic terminal-like interface directly on the PicoCalc hardware. Users can type characters using the physical keypad, and the corresponding text appears on the display. This serves as a foundation for potentially more complex applications running directly on the device.

## Hardware Architecture

This firmware is designed specifically for the **Clockwork PicoCalc Mainboard V2.0**.

Key components utilized:
- **CPU**: Raspberry Pi Pico (RP2040)
- **Display**: ILI9488 TFT LCD (320x320, SPI Interface)
- **Input**: I2C-based keyboard controller on the PicoCalc

The PicoCalc uses a **dual-MCU architecture**:
1. A dedicated keyboard controller handles the physical keyboard matrix scanning
2. The Raspberry Pi Pico handles the display, application logic, and communicates with the keyboard controller over I2C

For detailed hardware specifications, pinouts, and schematics, please refer to the `PICOCALC_SPECS.md` document in this repository.

## Keyboard Implementation

After extensive reverse engineering and analysis, we successfully implemented communication with the PicoCalc's keyboard controller:

### Hardware Design
- The keyboard controller is accessible via I2C
- Communication parameters:
  - **I2C Bus**: 1
  - **SDA Pin**: 6
  - **SCL Pin**: 7
  - **I2C Address**: 0x1F

### Communication Protocol
We've documented the keyboard controller's proprietary protocol:
1. **Command Byte**: Send 0x09 to initiate a status read
2. **Status Word**: Read 2 bytes from the controller
   - For normal keys: High byte (MSB) is the event type, Low byte (LSB) is the key code
   - For Enter key: Type is 0x0A, code is 0x01 or 0x03
   - For Ctrl key: Special status words 0xA502 (press) and 0xA503 (release)

### Key Mapping
Special key codes are translated to appropriate characters/control codes:
- Function keys (F1-F10): 0x81-0x8A, 0x90
- Arrow keys: UP (0xB5), DOWN (0xB6), RIGHT (0xB7), LEFT (0xB4)
- Enter key: 0x01/0x03 with type 0x0A → translated to CR (13)
- Standard printable ASCII characters are passed through

## Current Features

- ✅ Initialization of the ILI9488 display
- ✅ Basic screen clearing and pixel writing
- ✅ Bitmap font rendering with all printable ASCII characters
- ✅ Keyboard interface with the I2C controller
- ✅ Working shell interface with character input and command processing
- ✅ Support for special keys (Enter, Backspace, etc.)

## Files

- `main.py`: Main application entry point
- `ili9488.py`: Display driver for the ILI9488 TFT LCD
- `font.py`: Bitmap font definitions for all ASCII characters
- `graphics.py`: Graphics drawing functions
- `keyboard.py`: I2C-based keyboard interface module
- `i2c_scanner.py`: Utility for general I2C device detection

## Setup

1. **Install MicroPython:** Flash the latest stable MicroPython firmware for the Raspberry Pi Pico onto your PicoCalc. You can find the firmware and instructions on the [Raspberry Pi documentation site](https://www.raspberrypi.com/documentation/microcontrollers/micropython.html). Remember to put the Pico into BOOTSEL mode (hold SW1 while plugging in USB).
2. **Copy Files:** Connect to the Pico's REPL (e.g., using Thonny IDE). Copy all the required `.py` files to the root directory of the Pico's filesystem.
3. **Reset:** Reset the Pico (either physically or via CTRL+D in the REPL). The `main.py` script should run automatically.

## Usage

Once the firmware is running:
- The display will initialize and show a prompt (e.g., `> `).
- Press keys on the physical keypad. The corresponding characters should appear on the screen.
- Use Backspace for text deletion and Enter to execute "commands".
- The shell supports all alphanumeric keys and special characters.

## Development Plan

1. [x] Basic Display Initialization
2. [x] Refactor display logic into `ili9488.py`
3. [x] Implement bitmap font (`font.py`) and character drawing (`graphics.py`)
4. [x] Implement proper communication with the keyboard controller via I2C
5. [x] Integrate components into `main.py` to create the interactive shell loop
6. [ ] Add basic scrolling or line wrapping
7. [ ] Implement command processing functions

## Contributing

Feel free to submit issues or pull requests if you have suggestions or improvements.

## Development Journey

Our development process involved significant reverse engineering of the PicoCalc hardware:

1. **Initial Approach**: We first attempted direct GPIO matrix scanning, assuming the keyboard was directly connected to the Pico.

2. **Discovery**: Using I2C scanning tools, we identified a keyboard controller at address 0x1F on the I2C1 bus (SDA=GP6, SCL=GP7).

3. **Protocol Analysis**: Through testing and debugging, we discovered:
   - Special command byte (0x09) initiates status reads
   - 2-byte status words encode key type and value
   - Special handling for Enter key (which sends two different codes)
   - Different byte order interpretation for normal keys vs. Enter key

4. **Implementation**: We built a robust keyboard driver that handles all key types, special key codes, and properly debounces input.

This work has resulted in a fully functional keyboard interface that accurately translates physical key presses to on-screen characters with proper handling of special keys.

---

*This project was developed with [Cursor](https://cursor.sh/), an AI-powered code editor.*
