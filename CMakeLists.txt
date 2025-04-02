cmake_minimum_required(VERSION 3.13)

# Initialize the Raspberry Pi Pico SDK
include(pico_sdk_import.cmake)

project(picocalc_hello C CXX ASM)
set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)

# Initialize the Raspberry Pi Pico SDK
pico_sdk_init()

# Add source files
add_executable(${PROJECT_NAME}
    src/main.c
)

# Enable USB output, disable uart output
pico_enable_stdio_usb(${PROJECT_NAME} 1)
pico_enable_stdio_uart(${PROJECT_NAME} 0)

# Link against libraries
target_link_libraries(${PROJECT_NAME}
    pico_stdlib
)

# Create map/bin/hex/uf2 file in addition to ELF.
pico_add_extra_outputs(${PROJECT_NAME}) 