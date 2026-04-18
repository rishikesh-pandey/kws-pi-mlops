import os
import glob
import requests

API_KEY = os.environ.get("EI_API_KEY")
HEADERS = {"x-api-key": API_KEY, "Accept": "application/json"}

def sync_data():
    # 1. Get Project ID from your API Key
    proj_res = requests.get("https://studio.edgeimpulse.com/v1/api/projects", headers=HEADERS)
    project_id = proj_res.json()['projects'][0]['id']

    # 2. Get files currently sitting in the Edge Impulse cloud
    print("🔍 Fetching current Edge Impulse state...")
    samples_res = requests.get(f"https://studio.edgeimpulse.com/v1/api/{project_id}/raw-data", headers=HEADERS)
    
    # Create a dictionary of {filename: sample_id}
    ei_samples = {sample['filename']: sample['id'] for sample in samples_res.json()['samples']}

    # 3. Get files currently sitting in your local DVC folder
    local_files = []
    local_paths = glob.glob("data/raw_data/**/*.wav", recursive=True)
    for path in local_paths:
        local_files.append(os.path.basename(path))

    # 4. Phase 1: The Purge (Delete files in EI that you removed from DVC)
    for filename, sample_id in ei_samples.items():
        if filename not in local_files:
            print(f"🗑️ Deleting orphaned file from Edge Impulse: {filename}")
            requests.delete(f"https://studio.edgeimpulse.com/v1/api/{project_id}/raw-data/{sample_id}", headers=HEADERS)

    # 5. Phase 2: The Upload (Only upload new files)
    for local_path in local_paths:
        filename = os.path.basename(local_path)
        if filename not in ei_samples:
            print(f"☁️ Uploading new file: {filename}")
            
            # Read the audio file and upload it
            with open(local_path, 'rb') as file_data:
                # Edge Impulse determines the label from the folder name
                label = os.path.basename(os.path.dirname(local_path))
                upload_headers = {"x-api-key": API_KEY, "x-file-name": filename, "x-label": label}
                requests.post("https://ingestion.edgeimpulse.com/api/training/data", headers=upload_headers, data=file_data)

if __name__ == "__main__":
    sync_data()