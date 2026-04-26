import os
import glob
import requests

API_KEY = os.environ.get("EI_API_KEY")
HEADERS = {"x-api-key": API_KEY, "Accept": "application/json"}

def clear_project_data(project_id):
    print("🧹 Clearing all existing data from Edge Impulse...")
    for category in ['training', 'testing']:
        res = requests.get(f"https://studio.edgeimpulse.com/v1/api/{project_id}/raw-data?category={category}", headers=HEADERS)
        data = res.json()
        
        if data.get('success') and 'samples' in data:
            for sample in data['samples']:
                sample_id = sample['id']
                requests.delete(f"https://studio.edgeimpulse.com/v1/api/{project_id}/raw-data/{sample_id}", headers=HEADERS)
    print("Project data cleared.")

def upload_all_data():
    if not API_KEY:
        print("ERROR: EI_API_KEY is missing! Check your GitHub Secrets.")
        exit(1)

    # 1. Get Project ID
    proj_res = requests.get("https://studio.edgeimpulse.com/v1/api/projects", headers=HEADERS)
    proj_data = proj_res.json()
    if not proj_data.get('success'):
        print(f"Authentication Failed: {proj_data.get('error')}")
        exit(1)
        
    project_id = proj_data['projects'][0]['id']

    # 2. Wipe everything clean
    clear_project_data(project_id)

    # 3. Upload the exact dataset from scratch
    print("Uploading fresh dataset...")
    local_paths = glob.glob("data/raw_data/**/*.wav", recursive=True)
    
    for local_path in local_paths:
        filename = os.path.basename(local_path)
        label = os.path.basename(os.path.dirname(local_path))
        
        with open(local_path, 'rb') as file_data:
            upload_headers = {
                "x-api-key": API_KEY, 
                "x-label": label
            }
            
            res = requests.post(
                "https://ingestion.edgeimpulse.com/api/split/files", 
                headers=upload_headers, 
                files={"data": (filename, file_data, "audio/wav")}
            )
            
            if res.status_code == 200:
                # print(f"Uploaded: {filename} | Label: '{label}' | Category: split")
                pass
            else:
                print(f"Failed to upload {filename}: {res.text}")

    print("Ingestion Complete!")

if __name__ == "__main__":
    upload_all_data()