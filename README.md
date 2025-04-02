# Pico Project

A Raspberry Pi Pico project template with a structured development environment.

## Project Structure

```
pico_project/
├── src/           # Source files
├── include/       # Header files
├── lib/          # Reusable components
├── tests/        # Unit tests
├── examples/     # Example code
└── docs/         # Documentation
```

## Prerequisites

- macOS
- Homebrew
- CMake (version 3.13 or higher)
- ARM GCC Toolchain
- Pico SDK

## Setup Instructions

1. Install required tools:
```bash
brew install cmake gcc-arm-none-eabi
```

2. Set up Pico SDK:
```bash
mkdir -p ~/pico
cd ~/pico
git clone -b master https://github.com/raspberrypi/pico-sdk.git
cd pico-sdk
git submodule update --init
```

3. Set environment variable (add to ~/.zshrc):
```bash
echo 'export PICO_SDK_PATH=~/pico/pico-sdk' >> ~/.zshrc
source ~/.zshrc
```

## Building the Project

```bash
mkdir -p build
cd build
cmake ..
make
```

## Flashing to Pico

1. Hold the BOOTSEL button on the Pico
2. While holding BOOTSEL, plug the Pico into your Mac
3. Release BOOTSEL - it should mount as a mass storage device
4. Copy the generated .uf2 file:
```bash
cp pico_project.uf2 /Volumes/RPI-RP2/
```

## Monitoring Output

```bash
# List available serial devices
ls /dev/tty.*

# Connect using screen (replace XXXX with your device number)
screen /dev/tty.usbmodemXXXX 115200
```

## Development Tips

1. Use VS Code with the following extensions:
   - C/C++
   - CMake Tools
   - Cortex-Debug (for debugging)

2. For debugging:
   - Set up OpenOCD
   - Configure VS Code launch.json for Cortex-Debug
   - Use the SWD interface on the Pico

## License

MIT License 