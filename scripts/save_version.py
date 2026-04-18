import os
import requests
import subprocess

API_KEY = os.environ.get("EI_API_KEY")
HEADERS = {
    "x-api-key": API_KEY, 
    "Accept": "application/json", 
    "Content-Type": "application/json"
}

def create_snapshot():
    # 1. Grab the short Git Commit hash from the system
    try:
        git_hash = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"]).decode("utf-8").strip()
    except:
        git_hash = "manual-run"

    # 2. Get Project ID
    proj_res = requests.get("https://studio.edgeimpulse.com/v1/api/projects", headers=HEADERS)
    project_id = proj_res.json()['projects'][0]['id']

    # 3. Tell Edge Impulse to freeze the project state
    print(f"📸 Creating Edge Impulse Version snapshot for Git commit: {git_hash}")
    payload = {
        "description": f"Automated MLOps Pipeline Snapshot - Git Commit: {git_hash}"
    }

    res = requests.post(f"https://studio.edgeimpulse.com/v1/api/{project_id}/versions", headers=HEADERS, json=payload)
    
    if res.status_code == 200:
        print("✅ Version successfully locked in Edge Impulse!")
    else:
        print(f"❌ Failed to save version: {res.text}")

if __name__ == "__main__":
    create_snapshot()