import os
import subprocess
import multiprocessing

# 1. Define paths
BUILD_DIR = "deploy/build"
LIBRARY_DIR = "deploy/board_library"

print("🚀 Starting Firmware Compilation for RP2040...")

# 2. Verify the SDK was extracted by deploy_board.py
if not os.path.exists(LIBRARY_DIR):
    print(f"❌ ERROR: SDK not found at {LIBRARY_DIR}! Run deploy_board.py first.")
    exit(1)

print("✅ Edge Impulse SDK verified.")

# 3. Create the CMake build directory
os.makedirs(BUILD_DIR, exist_ok=True)

# 4. Run CMake to configure the Pico build
print("⚙️ Configuring CMake (Linking Pico SDK & Edge Impulse)...")
cmake_cmd = [
    "cmake", 
    "..", 
    "-DPICO_BOARD=pico", 
    "-DCMAKE_BUILD_TYPE=Release"
]

# Removed capture_output=True so logs stream live to the GitHub Actions console
result = subprocess.run(cmake_cmd, cwd=BUILD_DIR)

if result.returncode != 0:
    print("❌ CMake Configuration Failed!")
    exit(1)

# 5. Run Make to compile the .bin file
cores = multiprocessing.cpu_count()
print(f"🔨 Compiling C++ into ARM binary using {cores} CPU cores...")
print("⏳ This step takes a few minutes. Watch the live logs below:")

make_cmd = ["make", f"-j{cores}"]
result = subprocess.run(make_cmd, cwd=BUILD_DIR)

if result.returncode != 0:
    print("❌ Compilation Failed!")
    exit(1)

print("✅ SUCCESS! Firmware compiled.")
print("📦 You can find your binary files in: deploy/build/")