import os
import time
import requests
import zipfile
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.environ.get("EI_API_KEY")

if not API_KEY:
    print("ERROR: EI_API_KEY environment variable is missing!")
    exit(1)

HEADERS = {
    "x-api-key": API_KEY,
    "Accept": "application/json",
    "Content-Type": "application/json"
}

# --- THE FIX: DYNAMICALLY FETCH THE PROJECT ID ---
print("🔍 Fetching Project ID from API Key...")
proj_res = requests.get("https://studio.edgeimpulse.com/v1/api/projects", headers=HEADERS)
if proj_res.status_code != 200:
    print(f"Failed to fetch projects. RAW ERROR: {proj_res.text}")
    exit(1)

proj_data = proj_res.json()
if not proj_data.get('success') or not proj_data.get('projects'):
    print(f"Authentication Failed or no projects found: {proj_data}")
    exit(1)
    
PROJECT_ID = proj_data['projects'][0]['id']
BASE_URL = f"https://studio.edgeimpulse.com/v1/api/{PROJECT_ID}"
print(f"Successfully attached to Project ID: {PROJECT_ID}")


def build_and_download():
    # deploy_type = "raspberry-pi-rp2040"
    deploy_type = "zip"
    
    print(f"Triggering Cloud Compilation for {deploy_type}...")
    
    # BUGFIX: Explicitly tell the compiler to build the int8 quantized model!
    payload = { 
        "engine": "tflite",
        "modelType": "int8" 
    }
    
    deploy_url = f"{BASE_URL}/jobs/build-ondevice-model?type={deploy_type}"
    res = requests.post(deploy_url, headers=HEADERS, json=payload)
    
    if res.status_code != 200:
        print(f"Build failed: {res.text}")
        exit(1)
        
    job_id = res.json().get("id")
    print(f"Cloud Compiler Job started! (Job ID: {job_id})")
    
    # 2. Smart Polling Loop
    print("⏳ Waiting for the cloud compiler to finish. This usually takes 1-2 minutes...")
    
    download_headers = {"x-api-key": API_KEY, "Accept": "application/zip"}
    download_url = f"{BASE_URL}/deployment/download?type={deploy_type}&modelType=int8"
    
    max_retries = 15
    for attempt in range(max_retries):
        print(f"Check {attempt + 1}/{max_retries}: Asking the server if the file is ready...")
        download_res = requests.get(download_url, headers=download_headers)
        
        if download_res.status_code == 200:
            os.makedirs("deploy", exist_ok=True)
            zip_path = "deploy/firmware.zip"
            
            with open(zip_path, 'wb') as f:
                f.write(download_res.content)
            print(f"Firmware downloaded to {zip_path}")
            
            try:
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall("deploy/board_library")
                print("Firmware extracted! Look inside the deploy/board_library folder.")
            except zipfile.BadZipFile:
                print("Downloaded file is not a valid ZIP.")
            
            return 
            
        elif download_res.status_code == 500:
            print("Still building... waiting 20 seconds.")
            time.sleep(20)
        else:
            print(f"Unexpected Error: {download_res.status_code} - {download_res.text}")
            exit(1)
            
    print("Build timed out. The cloud compiler took longer than 5 minutes.")

if __name__ == "__main__":
    build_and_download()