# PicoCalc Hello World

This is a basic hello world project for the PicoCalc, demonstrating basic functionality of the Raspberry Pi Pico.

## Prerequisites

- Raspberry Pi Pico SDK
- CMake (3.13 or higher)
- Build tools (gcc-arm-none-eabi, make)

## Building

1. Set up the Pico SDK environment variable:

```bash
export PICO_SDK_PATH=/path/to/pico-sdk
```

1. Create a build directory and build the project:

```bash
mkdir build
cd build
cmake ..
make
```

## Flashing

After building, you'll find the following files in the `build` directory:

- `picocalc_hello.uf2` - The file to flash to your Pico
- `picocalc_hello.elf` - The ELF binary
- `picocalc_hello.bin` - The binary file
- `picocalc_hello.hex` - The hex file
- `picocalc_hello.map` - The map file

To flash the Pico:

1. Hold down the BOOTSEL button on your Pico
1. Connect the Pico to your computer via USB
1. Release the BOOTSEL button
1. Copy the `picocalc_hello.uf2` file to the RPI-RP2 drive that appears

## Running

After flashing:

1. The Pico will automatically restart
1. You should see the onboard LED blinking
1. Connect to the USB serial port to see the "Hello, PicoCalc!" message

## Serial Output

To view the serial output:

```bash
screen /dev/ttyACM0 115200
```

(Replace `/dev/ttyACM0` with the correct serial port for your system)

## License

MIT License
