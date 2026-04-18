import os
import requests
import subprocess

API_KEY = os.environ.get("EI_API_KEY")

if not API_KEY:
    print("❌ ERROR: EI_API_KEY environment variable is missing!")
    exit(1)

HEADERS = {
    "x-api-key": API_KEY, 
    "Accept": "application/json", 
    "Content-Type": "application/json"
}

def create_snapshot():
    # 1. Fix the Docker/Git "Dubious Ownership" Security Block
    subprocess.run(["git", "config", "--global", "--add", "safe.directory", "/app"])

    # 2. Grab the short Git Commit hash
    try:
        git_hash = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"]).decode("utf-8").strip()
    except Exception as e:
        print(f"⚠️ Could not read git hash, defaulting to 'manual-run'.")
        git_hash = "manual-run"

    # 3. Get Project ID Safely
    print("🔍 Fetching Project ID from API Key...")
    proj_res = requests.get("https://studio.edgeimpulse.com/v1/api/projects", headers=HEADERS)
    if proj_res.status_code != 200:
        print(f"❌ Failed to fetch projects. RAW ERROR: {proj_res.text}")
        exit(1)

    proj_data = proj_res.json()
    if not proj_data.get('success') or not proj_data.get('projects'):
        print(f"❌ Authentication Failed or no projects found: {proj_data}")
        exit(1)
        
    project_id = proj_data['projects'][0]['id']
    print(f"✅ Successfully attached to Project ID: {project_id}")

    # 4. Tell Edge Impulse to freeze the project state
    print(f"📸 Creating Edge Impulse Version snapshot for Git commit: {git_hash}")
    payload = {
        "description": f"Automated MLOps Pipeline Snapshot - Git Commit: {git_hash}"
    }

    # THE FIX: Changed /versions to /jobs/version
    res = requests.post(f"https://studio.edgeimpulse.com/v1/api/{project_id}/jobs/version", headers=HEADERS, json=payload)
    
    if res.status_code == 200:
        data = res.json()
        if data.get("success"):
            print("✅ Version snapshot successfully triggered in Edge Impulse!")
        else:
            print(f"❌ Failed to save version (API Error): {data.get('error')}")
            exit(1)
    else:
        print(f"❌ Failed to save version (HTTP Error): {res.text}")
        exit(1)

if __name__ == "__main__":
    create_snapshot()