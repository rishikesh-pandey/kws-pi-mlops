cmake_minimum_required(VERSION 3.13)

# Initialize the Pico SDK
include($ENV{PICO_SDK_PATH}/pico_sdk_init.cmake)
project(kws_firmware C CXX ASM)
pico_sdk_init()

# 1. Pull in the Edge Impulse Neural Network library from the deploy folder
add_subdirectory(deploy/board_library)

# 2. Define your main executable as 'app'
add_executable(app main.cpp)

# 3. Link the Pico hardware AND the Edge Impulse SDK to your main app!
# THE FIX: Removed the hyphen! The target is named 'edgeimpulse'
target_link_libraries(app pico_stdlib edgeimpulse)

# 4. Route standard output (printf) to the USB port instead of UART pins
pico_enable_stdio_usb(app 1)
pico_enable_stdio_uart(app 0)

# 5. Tell the SDK to generate the .bin and .uf2 artifact files!
pico_add_extra_outputs(app)