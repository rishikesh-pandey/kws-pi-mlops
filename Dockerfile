# Start with a standard Python Linux environment
FROM python:3.10-slim

# Install the ARM Cross-Compiler, CMake, and Git
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    gcc-arm-none-eabi \
    libnewlib-arm-none-eabi \
    libstdc++-arm-none-eabi-newlib \
    python3 \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Clone the official Raspberry Pi Pico SDK
RUN git clone -b master https://github.com/raspberrypi/pico-sdk.git /opt/pico-sdk
RUN cd /opt/pico-sdk && git submodule update --init

# Set the environment variable so CMake knows where the SDK is
ENV PICO_SDK_PATH=/opt/pico-sdk

# Set up the working directory for your Python scripts
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Keep the container running
CMD ["tail", "-f", "/dev/null"]