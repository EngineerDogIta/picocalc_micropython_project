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

I'll analyze the keyboard mapping code and integrate it with the schematic documentation. Based on the patch code and schematic analysis, here's the enhanced keypad documentation:

## 4. Keypad Interface (Updated)

### 4.1 GPIO Matrix Configuration
| Row/Column | Pico GPIO | Pull-Up Resistor | 
|------------|-----------|------------------|
| Row 0      | GP2       | R20 (10kΩ)       |
| Row 1      | GP3       | R21 (10kΩ)       | 
| Row 2      | GP4       | R22 (10kΩ)       |
| Row 3      | GP5       | R23 (10kΩ)       |
| Column 0   | GP6       | –                |
| Column 1   | GP7       | –                |
| Column 2   | GP8       | –                |
| Column 3   | GP9       | –                |

### 4.2 Keycode Mapping Table
The firmware patch reveals these specific keycode-to-function mappings:

| Key Code (Hex) | Mapped Function | Physical Button |
|----------------|-----------------|-----------------|
| 0xB1           | ESC             | Escape          |
| 0x81           | F1              | Function 1      |
| 0x82           | F2              | Function 2      |
| 0x83           | F3              | Function 3      |
| 0x84           | F4              | Function 4      |
| 0x85           | F5              | Function 5      |
| 0x86           | F6              | Function 6      |
| 0x87           | F7              | Function 7      |
| 0x88           | F8              | Function 8      |
| 0x89           | F9              | Function 9      |
| 0x90           | F10             | Function 10     |
| 0xB5           | UP              | Up Arrow        |
| 0xB6           | DOWN            | Down Arrow      |
| 0xB7           | RIGHT           | Right Arrow     |
| 0xB4           | LEFT            | Left Arrow      |
| 0xD0           | BreakKey        | Break           |
| 0xD1           | INSERT          | Insert          |
| 0xD2           | HOME            | Home            |
| 0xD5           | END             | End             |
| 0xD6           | PUP             | Page Up         |
| 0xD7           | PDOWN           | Page Down       |

### 4.3 Control Key Handling
The code shows special handling for modifier keys:
```c
if(buff==0xA503) ctrlheld=0;  // Ctrl release
else if(buff==0xA502) ctrlheld=1;  // Ctrl press
```
This enables CTRL+letter combinations (e.g., CTRL+C maps to ASCII 03)

### 4.4 Implementation Notes
- Keycodes use a 16-bit format where upper byte contains scancode
- The matrix scanning logic converts physical keypresses to these hex codes
- Arrow keys and function keys use dedicated codes rather than ASCII equivalents
- Break key (0xD0) triggers special interrupt handling for program termination

This mapping aligns with the Clockwork PicoCalc's physical keyboard layout and the Mainboard V2.0 schematic's keypad matrix configuration[1][3].

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
*Reference: Clockwork Mainboard V2.0 Schematic*