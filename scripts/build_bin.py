import os
import subprocess
import shutil

# 1. Define paths
ZIP_PATH = "deploy/firmware.zip"
BUILD_DIR = "deploy/build"
LIBRARY_DIR = "deploy/board_library"

print("🚀 Starting Firmware Compilation for RP2040...")

# 2. Extract the Edge Impulse ZIP
if not os.path.exists(ZIP_PATH):
    print("❌ ERROR: firmware.zip not found! Run deploy_board.py first.")
    exit(1)

shutil.unpack_archive(ZIP_PATH, LIBRARY_DIR)
print("✅ Edge Impulse SDK extracted.")

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
result = subprocess.run(cmake_cmd, cwd=BUILD_DIR, capture_output=True, text=True)

if result.returncode != 0:
    print("❌ CMake Configuration Failed!")
    print(result.stderr)
    exit(1)

# 5. Run Make to compile the .bin file
print("🔨 Compiling C++ into ARM binary. This will take a few minutes...")
make_cmd = ["make", "-j4"]
result = subprocess.run(make_cmd, cwd=BUILD_DIR, capture_output=True, text=True)

if result.returncode != 0:
    print("❌ Compilation Failed!")
    print(result.stderr)
    exit(1)

print("✅ SUCCESS! Firmware compiled.")
print("📦 You can find your files in: deploy/build/")