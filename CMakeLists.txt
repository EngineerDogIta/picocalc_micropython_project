# == DO NOT EDIT THE FOLLOWING LINES for the Raspberry Pi Pico VS Code Extension to work ==
if(WIN32)
    set(USERHOME $ENV{USERPROFILE})
else()
    set(USERHOME $ENV{HOME})
endif()
set(sdkVersion 2.1.1)
set(toolchainVersion 14_2_Rel1)
set(picotoolVersion 2.1.1)
set(picoVscode ${USERHOME}/.pico-sdk/cmake/pico-vscode.cmake)
if (EXISTS ${picoVscode})
    include(${picoVscode})
endif()
# ====================================================================================

cmake_minimum_required(VERSION 3.13)

# Initialize the Raspberry Pi Pico SDK
include(pico_sdk_import.cmake)

# Set default board type
if(NOT PICO_BOARD)
    set(PICO_BOARD "pico" CACHE STRING "Board type (pico or pico2)")
endif()

# Validate board type
if(NOT PICO_BOARD STREQUAL "pico" AND NOT PICO_BOARD STREQUAL "pico2")
    message(FATAL_ERROR "PICO_BOARD must be either 'pico' or 'pico2'")
endif()

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

# Add compile definitions for board type
target_compile_definitions(${PROJECT_NAME} PRIVATE
    PICO_BOARD="${PICO_BOARD}"
) 