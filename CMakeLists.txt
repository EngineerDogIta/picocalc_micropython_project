cmake_minimum_required(VERSION 3.13)

# Include the Pico SDK initialization script
include($ENV{PICO_SDK_PATH}/pico_sdk_init.cmake)

project(pico_project)

# Initialize the Pico SDK
pico_sdk_init()

# Add include directories
include_directories(${PROJECT_SOURCE_DIR}/include)

# Add source files
add_executable(${PROJECT_NAME}
    src/main.cpp
)

# Enable USB stdio and disable UART stdio
pico_enable_stdio_usb(${PROJECT_NAME} 1)
pico_enable_stdio_uart(${PROJECT_NAME} 0)

# Link the Pico SDK to your project
target_link_libraries(${PROJECT_NAME} 
    pico_stdlib
)

# Create map/bin/hex/uf2 files
pico_add_extra_outputs(${PROJECT_NAME})

# Add subdirectories for additional components
add_subdirectory(lib)
add_subdirectory(tests)
add_subdirectory(examples) 