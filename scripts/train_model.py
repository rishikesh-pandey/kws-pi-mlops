import os
import time
import requests
import yaml
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("EI_API_KEY")
PROJECT_ID = os.getenv("PROJECT_ID")

with open("config.yaml", "r") as file:
    config = yaml.safe_load(file)

if not API_KEY or not PROJECT_ID:
    print("❌ ERROR: Missing API keys in .env")
    exit(1)

HEADERS = {
    "x-api-key": API_KEY,
    "Accept": "application/json",
    "Content-Type": "application/json"
}

BASE_URL = f"https://studio.edgeimpulse.com/v1/api/{PROJECT_ID}"

def get_blocks():
    """Fetches the internal IDs of the DSP and Neural Network blocks."""
    res = requests.get(f"{BASE_URL}/impulse", headers=HEADERS)
    if res.status_code != 200:
        print("❌ Failed to fetch project impulse architecture.")
        exit(1)
    
    data = res.json()["impulse"]
    dsp_id = data["dspBlocks"][0]["id"] if data.get("dspBlocks") else None
    learn_id = data["learnBlocks"][0]["id"] if data.get("learnBlocks") else None
    return dsp_id, learn_id

def start_training():
    dsp_id, learn_id = get_blocks()
    
    if not learn_id:
        print("❌ Could not find a Neural Network block in this project.")
        exit(1)

    train_config = config.get("training", {})
    
    if train_config.get("override_ui"):
        print("⚙️  Merging YAML overrides with UI default parameters...")
        
        # 1. Fetch current UI defaults for the Keras model
        keras_res = requests.get(f"{BASE_URL}/models/keras/{learn_id}", headers=HEADERS)
        if keras_res.status_code == 200:
            current_ui_params = keras_res.json()
        
        # 2. Build the exact payload for the override endpoint
        payload = {}
        if "learning_rate" in train_config: payload["learningRate"] = train_config["learning_rate"]
        if "epochs" in train_config: payload["epochs"] = train_config["epochs"]
        if "batch_size" in train_config: payload["batchSize"] = train_config["batch_size"]
        
        # Add data augmentation overrides if they exist
        aug = train_config.get("data_augmentation", {})
        if aug.get("enabled"):
            payload["dataAugmentation"] = True
            
        print(f"🚀 Triggering Custom GPU Training with overrides: {payload}")
        res = requests.post(f"{BASE_URL}/jobs/train/keras/{learn_id}", headers=HEADERS, json=payload)
    
    else:
        print("🚀 Triggering Standard Pipeline (Strictly using Web UI Defaults)...")
        res = requests.post(f"{BASE_URL}/jobs/retrain", headers=HEADERS)
    
    if res.status_code != 200:
        print(f"❌ Failed to start pipeline: {res.text}")
        exit(1)
        
    data = res.json()
    if not data.get("success"):
        print(f"❌ API Error: {data.get('error')}")
        exit(1)
        
    job_id = data["id"]
    print(f"✅ Cloud Pipeline started! (Job ID: {job_id})")
    return job_id

def wait_for_job(job_id, max_retries=15, sleep_time=20):
    """Dynamically polls the API to check if the job is finished."""
    print(f"⏳ Waiting for cloud job to finish. Polling every {sleep_time} seconds...")
    
    status_url = f"{BASE_URL}/jobs/{job_id}/status"
    
    for attempt in range(max_retries):
        print(f"🔄 Check {attempt + 1}/{max_retries}: Querying GPU training status...")
        res = requests.get(status_url, headers=HEADERS)
        
        if res.status_code == 200:
            job_data = res.json().get("job", {})
            
            # The API returns 'finished' boolean when the job is completely done
            if job_data.get("finished"):
                if job_data.get("finishedSuccessful"):
                    print("✅ Cloud Training Job completed successfully!")
                    return
                else:
                    print("❌ Cloud Training Job failed during execution. Check EI Dashboard for logs.")
                    exit(1)
            else:
                print(f"⏳ Model is still training... waiting {sleep_time} seconds.")
                time.sleep(sleep_time)
        else:
            print(f"❌ Failed to check job status: {res.text}")
            exit(1)
            
    print(f"❌ Training timed out. The cloud job took longer than {max_retries * sleep_time / 60} minutes.")
    exit(1)

def print_metrics(learn_id):
    print("\n📊 Fetching Model Performance Metrics...")
    
    # BUGFIX: The correct endpoint is the Keras metadata route
    url = f"{BASE_URL}/training/keras/{learn_id}/metadata"
    res = requests.get(url, headers=HEADERS)
    
    if res.status_code != 200:
        print(f"❌ Failed to fetch metrics: {res.status_code}")
        return

    data = res.json()
    metrics_list = data.get("modelValidationMetrics", [])
    
    if not metrics_list:
        print("⚠️ No validation metrics found. Raw API Response:")
        print(data)
        return
        
    # Grab the metrics for the int8 quantized model (or fallback to whatever is first)
    target_metrics = next((m for m in metrics_list if m.get("type") == "int8"), metrics_list[0])
    
    # Safely parse Accuracy (EI sometimes returns a float, sometimes a nested dict)
    acc_data = target_metrics.get("accuracy", 0)
    acc = acc_data.get("raw", 0) * 100 if isinstance(acc_data, dict) else float(acc_data) * 100
    loss = target_metrics.get("loss", 0)
    
    print(f"🎯 Accuracy (Validation): {acc:.2f}%")
    print(f"📉 Loss:     {loss:.4f}")

    # Print the Confusion Matrix
    cm = target_metrics.get("confusionMatrix", [])
    if cm:
        print("\n🧮 Confusion Matrix:")
        for row in cm:
            # Format each row to look like a clean, spaced grid
            print(" | ".join([f"{str(val):>5}" for val in row]))
    print("\n")

if __name__ == "__main__":
    dsp_id, learn_id = get_blocks()
    
    job_id = start_training()
    wait_for_job(job_id, max_retries=15, sleep_time=20)
    
    # We ONLY fetch metrics for the Neural Network, not the DSP block
    print_metrics(learn_id)
    
    print("🏁 Training command executed successfully.")