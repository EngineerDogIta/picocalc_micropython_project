# Clockwork PicoCalc Mainboard V2.0 Schematic Documentation

This exhaustive technical breakdown analyzes the Clockwork PicoCalc's core circuitry based on the **Mainboard V2.0 schematic**, focusing on hardware architecture, component interconnections, and operational parameters.

---

## 1. Central Processing Unit (CPU)
**Component**: Raspberry Pi Pico (U1)
- **Microcontroller**: RP2040 dual-core ARM Cortex-M0+
- **Clock Speed**: 133 MHz (default)
- **Memory**: 264 KB SRAM (Bank 0: 136 KB, Bank 1: 128 KB)
- **Power Input**:
  - **VBUS**: 5V from USB-C (J1)
  - **VSYS**: 3.3V regulated supply (U3)
- **Boot Mode**:
  - BOOTSEL button (SW1) connected to GP23 with 1kΩ pull-up (R12)

---

## 2. Power Management System
### 2.1 Voltage Regulation
- **Primary Regulator** (U3): 3.3V LDO (Low-Dropout Regulator)
  - Input: 5V from USB-C (J1) or battery (BAT1)
  - Output: 3.3V ±2% tolerance
  - Max Current: 1A (shared across peripherals)

- **Battery Circuit**:
  - **Battery Connector** (BAT1): 3.7V Li-Po (JST-PH-2)
  - **Charging IC** (U2): TP4056 (1A linear charger)
  - **Protection**: Dual Schottky diode (D1, D2) for power path switching

### 2.2 Power Distribution
| Rail       | Voltage | Connected Components               |
|------------|---------|-------------------------------------|
| VBUS       | 5V      | USB-C, Pico VBUS pin                |
| VSYS       | 3.3V    | RP2040, LCD, Keypad, Audio Circuit  |
| VBAT       | 3.7V    | RTC backup (via CR1220 cell)        |

---

## 3. Display Subsystem (ILI9488 LCD)
**Controller**: ILI9488 (320x480 TFT, 16-bit color)

### 3.1 GPIO Interface
| LCD Signal | Pico GPIO | Function                | Schematic Trace |
|------------|-----------|-------------------------|-----------------|
| CLK        | GP10      | SPI0_SCK                | C10→LCD Pin 7   |
| MOSI       | GP11      | SPI0_TX                 | C11→LCD Pin 8   |
| CS         | GP13      | SPI0_CSn                | C13→LCD Pin 6   |
| DC         | GP14      | Data/Command Select     | C14→LCD Pin 5   |
| RST        | GP15      | Hardware Reset          | C15→LCD Pin 4   |
| BL         | GP12      | Backlight PWM (500Hz)   | C12→LCD Pin 3   |

**Critical Parameters**:
- SPI Clock: 62.5 MHz (max) - *Note: Code uses SPI1 pins (GP10/11)*
- Backlight Current: 120mA @ 3.3V (R33: 10Ω current limiter)

---

## 4. Keypad Interface (Reverse Engineered)

### 4.1 I2C Connection
Through extensive reverse engineering, we've determined the keyboard is controlled by an I2C peripheral:

| Interface Parameter | Value       | Notes                                   |
|---------------------|-------------|----------------------------------------|
| I2C Bus             | I2C1        | Secondary I2C bus on the Pico          |
| SDA Pin             | GP6         | Serial Data Line                        |
| SCL Pin             | GP7         | Serial Clock Line                       |
| I2C Address         | 0x1F        | 7-bit addressing scheme                 |
| Clock Frequency     | 100 kHz     | Standard I2C mode                       |
| Pull-up Resistors   | 4.7kΩ       | On both SDA and SCL lines               |

### 4.2 Communication Protocol
The protocol follows a custom I2C implementation:

1. **Command Phase**:
   - Master (Pico) writes command byte 0x09 to address 0x1F
   - This command initiates a keyboard status read

2. **Response Phase**:
   - Master (Pico) reads 2 bytes from the keyboard controller
   - Response format is a 16-bit status word:
     - For standard keys: High byte (MSB) contains event type, Low byte (LSB) contains key code
     - For Enter key: Type is 0x0A in LSB, code is 0x01 or 0x03 in MSB
   - Status word of 0 indicates no key event

3. **Event Types**:
   - 0x01: Key press event
   - 0x02: Key repeat event
   - 0x03: Key release event
   - 0x0A: Special event type (used with Enter key)

4. **Special Control Codes**:
   - 0xA502: Control key pressed
   - 0xA503: Control key released
   - 0x7E02: Alternative Control key pressed
   - 0x7E03: Alternative Control key released

### 4.3 Keycode Mapping Table
Through our reverse engineering, we've mapped these key codes:

| Key Code (Hex) | Mapped Function | Physical Button |
|----------------|-----------------|-----------------|
| 0xB1           | ESC (27)        | Escape          |
| 0x81-0x89      | F1-F9           | Function 1-9    |
| 0x90           | F10             | Function 10     |
| 0xB5           | UP (128)        | Up Arrow        |
| 0xB6           | DOWN (130)      | Down Arrow      |
| 0xB7           | RIGHT (129)     | Right Arrow     |
| 0xB4           | LEFT (131)      | Left Arrow      |
| 0xD0           | BreakKey (3)    | Break           |
| 0xD1           | INSERT (132)    | Insert          |
| 0xD2           | HOME (134)      | Home            |
| 0xD5           | END (135)       | End             |
| 0xD6           | PUP (136)       | Page Up         |
| 0xD7           | PDOWN (137)     | Page Down       |
| 0x01/0x03*     | ENTER (13)      | Enter/Return    |
| 0x5A           | ENTER (13)      | Alternative Enter|
| 0x0D           | ENTER (13)      | CR code         |

*Note: Enter key generates two sequential codes (0x010A followed by 0x030A)

### 4.4 Implementation Notes
- The keyboard controller internally scans a physical key matrix
- It debounces key presses in hardware before sending status
- For Control+letter combinations, the controller sets the `ctrlheld` flag internally
- When Control is active, lowercase letter key codes (a-z) are modified: `key_code - 'a' + 1` (ASCII control codes)
- Different interpretation for key event type and key code bytes depending on key type:
  - Standard keys: event type in MSB, key code in LSB
  - Enter key: special coding with type 0x0A in LSB
  - Control keys: fixed 16-bit values for press/release events

### 4.5 Electrical Characteristics
- I2C Bus Logic Level: 3.3V
- Pull-up Configuration: 4.7kΩ pull-ups on both SDA and SCL lines
- Recommended polling rate: 50Hz
- Timing Considerations: 1ms delay required between command write and response read

---

## 5. Audio Circuitry
### 5.1 Amplifier Stage
- **Speaker Driver** (Q1): S8050 NPN Transistor
  - Base Resistor: R30 (1kΩ)
  - Emitter Resistor: R31 (220Ω)
  - Output Power: 0.5W @ 8Ω (SPK1)

### 5.2 PWM Audio Generation
- **PWM Source**: GP28 (PWM_CHAN_A)
- **Low-Pass Filter**:
  - R32 (1kΩ) + C32 (100nF) → Cutoff freq: 1.6kHz

### 5.3 Headphone Detection
- **Jack** (J3): 3.5mm TRS with switch
  - Detection Signal: GP27 (pulled high via R29: 10kΩ)

---

## 6. Expansion Interfaces
### 6.1 I2C Bus
| Signal | Pico GPIO | Pull-Up Resistor |
|--------|-----------|------------------|
| SDA    | GP0       | R24 (4.7kΩ)      |
| SCL    | GP1       | R25 (4.7kΩ)      |

### 6.2 General-Purpose Headers
| Header | Pico GPIOs                 | Functionality            |
|--------|----------------------------|--------------------------|
| J4     | GP16, GP17, GP18, GP19     | Analog/Digital I/O       |
| J5     | GP26, GP27, GP28, GP29     | ADC Inputs (12-bit)      |

---

## 7. Diagnostic Features
- **Test Points**:
  - TP1: 3.3V rail verification
  - TP2: GND reference
  - TP3: VSYS voltage monitoring

- **LED Indicators**:
  - D3 (Red): USB Power Active
  - D4 (Green): Battery Charging Status

---

## 8. Critical Design Notes
1. **ESD Protection**:
   - TVS Diodes (D5-D8) on USB data lines
   - Ferrite Bead (FB1) on VBUS line

2. **Thermal Management**:
   - U3 (3.3V Regulator): Requires heatsink for continuous >500mA loads

3. **Firmware Flashing**:
   - Boot Mode: Hold SW1 while connecting USB

4. **Current Limits**:
   - Total system current ≤1A (USB 2.0 spec)

---

## 9. Revision-Specific Changes (V2.0 vs V1.x)
- Added I2C pull-up resistors (R24-R25)
- Improved backlight PWM stability via RC filter (R34: 100Ω, C34: 10μF)
- Redesigned keypad matrix with anti-ghosting diodes (D9-D12)

---
*Reference: Clockwork Mainboard V2.0 Schematic + Reverse Engineering Results*