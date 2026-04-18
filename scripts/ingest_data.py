import os
import requests
import yaml
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("EI_API_KEY")

with open("config.yaml", "r") as file:
    config = yaml.safe_load(file)

if not API_KEY:
    print("❌ ERROR: EI_API_KEY not found. Check your .env file.")
    exit(1)

DATA_DIR = config.get("pipeline", {}).get("data_directory", "data/raw_data")
UPLOAD_CAT = config.get("pipeline", {}).get("upload_category", "split")

URL = f"https://ingestion.edgeimpulse.com/api/{UPLOAD_CAT}/files"

def upload_file(filepath, label):
    with open(filepath, 'rb') as file:
        headers = {
            "x-api-key": API_KEY,
            "x-label": label,
            "x-category": UPLOAD_CAT
        }
        files = {
            'data': (os.path.basename(filepath), file, 'audio/wav')
        }
        
        response = requests.post(URL, headers=headers, files=files)
        
        if response.status_code == 200:
            print(f"✅ Uploaded: {os.path.basename(filepath)} | Label: '{label}' | Category: {UPLOAD_CAT}")
        else:
            print(f"❌ Failed to upload {filepath}: {response.text}")

if __name__ == "__main__":
    print(f"🚀 Starting Data Ingestion Pipeline (Category: {UPLOAD_CAT})...")
    
    if not os.path.exists(DATA_DIR) or not os.listdir(DATA_DIR):
        print(f"⚠️ No directory found at {DATA_DIR}. Please check your config.")
        exit(0)

    # NEW LOGIC: Iterate through the subdirectories
    for folder_name in os.listdir(DATA_DIR):
        folder_path = os.path.join(DATA_DIR, folder_name)
        
        # Verify it is actually a folder (like 'yes' or 'no')
        if os.path.isdir(folder_path):
            label = folder_name # The folder name is the exact label!
            
            # Loop through all the .wav files inside that specific folder
            for filename in os.listdir(folder_path):
                if filename.endswith(".wav"):
                    filepath = os.path.join(folder_path, filename)
                    upload_file(filepath, label)
                    
    print("🏁 Ingestion Complete.")