import os
import glob
import requests

API_KEY = os.environ.get("EI_API_KEY")
HEADERS = {"x-api-key": API_KEY, "Accept": "application/json"}

def sync_data():
    if not API_KEY:
        print("❌ ERROR: EI_API_KEY is missing! Check your GitHub Secrets.")
        exit(1)

    # 1. Get Project ID safely
    proj_res = requests.get("https://studio.edgeimpulse.com/v1/api/projects", headers=HEADERS)
    proj_data = proj_res.json()
    if not proj_data.get('success'):
        print(f"❌ Authentication Failed: {proj_data.get('error')}")
        exit(1)
        
    project_id = proj_data['projects'][0]['id']

    # 2. Get files currently sitting in Edge Impulse safely
    print("🔍 Fetching current Edge Impulse state...")
    ei_samples = {}
    
    # We must explicitly query the API by category, otherwise it returns an error!
    for category in ['training', 'testing']:
        res = requests.get(f"https://studio.edgeimpulse.com/v1/api/{project_id}/raw-data?category={category}", headers=HEADERS)
        data = res.json()
        
        # Safely extract samples only if the request was successful
        if data.get('success') and 'samples' in data:
            for sample in data['samples']:
                ei_samples[sample['filename']] = sample['id']
        else:
            print(f"⚠️ API Warning for {category}: {data.get('error')}")

    # 3. Get files sitting in your local DVC folder
    local_files = []
    local_paths = glob.glob("data/raw_data/**/*.wav", recursive=True)
    for path in local_paths:
        local_files.append(os.path.basename(path))

    # 4. Phase 1: The Purge (Delete files in the cloud that you removed locally)
    for filename, sample_id in ei_samples.items():
        if filename not in local_files:
            print(f"🗑️ Deleting orphaned file from cloud: {filename}")
            requests.delete(f"https://studio.edgeimpulse.com/v1/api/{project_id}/raw-data/{sample_id}", headers=HEADERS)

    # 5. Phase 2: The Upload (Only upload new files)
    for local_path in local_paths:
        filename = os.path.basename(local_path)
        if filename not in ei_samples:
            print(f"☁️ Uploading new file: {filename}")
            
            with open(local_path, 'rb') as file_data:
                label = os.path.basename(os.path.dirname(local_path))
                # x-disallow-duplicates prevents the API from ever duplicating a file hash
                upload_headers = {
                    "x-api-key": API_KEY, 
                    "x-file-name": filename, 
                    "x-label": label,
                    "x-disallow-duplicates": "1",
                    "Content-Type": "audio/wav"
                }
                res = requests.post("https://ingestion.edgeimpulse.com/api/training/data", headers=upload_headers, data=file_data)
                if res.status_code != 200:
                    print(f"⚠️ Failed to upload {filename}: {res.text}")
                    
    print("✅ Ingestion & Sync Complete!") 

if __name__ == "__main__":
    sync_data()