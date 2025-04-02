#!/bin/bash

# Default board type
BOARD_TYPE=${1:-pico}

# Validate board type
if [ "$BOARD_TYPE" != "pico" ] && [ "$BOARD_TYPE" != "pico2" ]; then
    echo "Error: Board type must be either 'pico' or 'pico2'"
    echo "Usage: ./build.sh [board_type]"
    echo "  board_type: pico (default) or pico2"
    exit 1
fi

# Set platform based on board type
if [ "$BOARD_TYPE" = "pico" ]; then
    PLATFORM="rp2040"
else
    PLATFORM="rp2350"
fi

# Create build directory if it doesn't exist
mkdir -p build

# Clean build directory to avoid platform conflicts
echo "Cleaning build directory..."
rm -rf build/*

# Configure and build
cd build
cmake -DPICO_BOARD=$BOARD_TYPE -DPICO_PLATFORM=$PLATFORM ..
make -j$(sysctl -n hw.ncpu)

# Check if build was successful
if [ $? -eq 0 ]; then
    echo "Build successful!"
    echo "Output files are in the build directory:"
    ls -l *.uf2 *.bin *.hex *.elf 2>/dev/null || echo "No output files found"
else
    echo "Build failed!"
    exit 1
fi 