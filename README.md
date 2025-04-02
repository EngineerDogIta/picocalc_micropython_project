# PicoCalc Project

This project is designed to run on both Raspberry Pi Pico (RP2040) and Pico 2 (RP2350) boards.

## Prerequisites

- Raspberry Pi Pico SDK
- CMake (version 3.13 or higher)
- ARM GCC toolchain
- USB cable for flashing

## Building the Project

### Using the Build Script (Recommended)

The project includes a build script that makes building easier:

```bash
# Build for Pico 1 (RP2040)
./build.sh

# Build for Pico 2 (RP2350)
./build.sh pico2
```

### Manual Build

If you prefer to build manually:

```bash
# Create build directory
mkdir -p build
cd build

# Configure for Pico 1
cmake -DPICO_BOARD=pico ..

# Or configure for Pico 2
# cmake -DPICO_BOARD=pico2 ..

# Build
make -j$(nproc)
```

## Flashing the Firmware

1. Enter BOOTSEL mode:
   - Hold the BOOTSEL button
   - Connect the Pico via USB
   - Release the BOOTSEL button

2. Flash the firmware:
   ```bash
   cp build/picocalc_hello.uf2 /media/$USER/RPI-RP2/
   ```

3. Running on PicoCalc:
   - Unplug the Micro-USB cable
   - Connect via USB Type-C
   - Press Power On button on top of PicoCalc

## Project Structure

```
.
├── CMakeLists.txt      # Main CMake configuration
├── build.sh           # Build script
├── src/               # Source files
│   └── main.c        # Main application code
└── build/            # Build output directory
```

## Development Notes

- The project supports both Pico 1 (RP2040) and Pico 2 (RP2350)
- USB output is enabled by default
- UART output is disabled by default
- The project uses the Pico SDK standard library

## Troubleshooting

If you encounter build issues:
1. Make sure the Pico SDK is properly installed
2. Check that your toolchain is correctly set up
3. Verify you're using the correct board type for your hardware
4. Check the build output for specific error messages

## License

MIT License
