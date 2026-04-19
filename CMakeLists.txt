cmake_minimum_required(VERSION 3.13)

# Initialize the Pico SDK
include($ENV{PICO_SDK_PATH}/pico_sdk_init.cmake)
project(kws_firmware C CXX ASM)
pico_sdk_init()

# 1. Define your main executable FIRST 
# (Edge Impulse's script will hunt for this exact name)
add_executable(app main.cpp)

# 2. Pull in the Edge Impulse Neural Network library
# (This script will automatically inject its source files into 'app')
add_subdirectory(deploy/board_library)

# 3. Link ONLY the Pico hardware! 
# (Edge Impulse is already attached, no need to link it)
target_link_libraries(app pico_stdlib)

# 4. Route standard output (printf) to the USB port instead of UART pins
pico_enable_stdio_usb(app 1)
pico_enable_stdio_uart(app 0)

# 5. Tell the SDK to generate the .bin and .uf2 artifact files
pico_add_extra_outputs(app)