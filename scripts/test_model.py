import os
import time
import requests
import yaml
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.environ.get("EI_API_KEY")

with open("config.yaml", "r") as file:
    config = yaml.safe_load(file)

if not API_KEY:
    print("ERROR: EI_API_KEY environment variable is missing!")
    exit(1)

HEADERS = {
    "x-api-key": API_KEY,
    "Accept": "application/json",
    "Content-Type": "application/json"
}

# DYNAMICALLY FETCH THE PROJECT ID FROM THE API KEY
print("Fetching Project ID from API Key...")
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


def start_testing():
    print("Triggering Model Testing Job (Classify All Unseen Data)...")
    res = requests.post(f"{BASE_URL}/jobs/evaluate", headers=HEADERS)
    
    if res.status_code != 200:
        print(f"Failed to start testing pipeline: {res.text}")
        exit(1)
        
    data = res.json()
    if not data.get("success"):
        print(f"API Error: {data.get('error')}")
        exit(1)
        
    job_id = data["id"]
    print(f"Cloud Testing Job started! (Job ID: {job_id})")
    return job_id

def wait_for_job(job_id, max_retries=25, sleep_time=20):
    print(f"Waiting for testing job to finish. Polling every {sleep_time} seconds...")
    status_url = f"{BASE_URL}/jobs/{job_id}/status"
    
    for attempt in range(max_retries):
        print(f"Check {attempt + 1}/{max_retries}: Querying testing status...")
        res = requests.get(status_url, headers=HEADERS)
        
        if res.status_code == 200:
            job_data = res.json().get("job", {})
            if job_data.get("finished"):
                if job_data.get("finishedSuccessful"):
                    print("✅ Cloud Testing Job completed successfully!")
                    return
                else:
                    print("Cloud Testing Job failed. Check EI Dashboard for logs.")
                    exit(1)
            else:
                time.sleep(sleep_time)
        else:
            print(f"Failed to check job status: {res.text}")
            exit(1)
            
    print("Testing timed out.")
    exit(1)

def get_learn_id():
    res = requests.get(f"{BASE_URL}/impulse", headers=HEADERS)
    data = res.json().get("impulse", {})
    return data.get("learnBlocks", [{}])[0].get("id")

def print_final_report():
    print("\n" + "="*50)
    print(" FINAL CI/CD MODEL EVALUATION REPORT ")
    print("="*50)
    
    test_res = requests.get(f"{BASE_URL}/classify/all/result", headers=HEADERS)
    test_acc = None 

    if test_res.status_code == 200:
        test_data = test_res.json()
        results_list = test_data.get("result", [])
        
        if isinstance(results_list, list) and len(results_list) > 0:
            correct = 0
            total = len(results_list)
            
            # Gather Labels 
            labels_set = set()
            for item in results_list:
                true_label = item.get("sample", {}).get("label")
                if true_label:
                    labels_set.add(true_label)
                
                # Dig through the nested lists to find the predictions dictionary
                classifications = item.get("classifications", [])
                if classifications and len(classifications) > 0:
                    res_list = classifications[0].get("result", [])
                    if res_list and len(res_list) > 0:
                        labels_set.update(res_list[0].keys())

            labels_set.discard(None)
            labels = sorted(list(labels_set))
            
            # Initialize empty confusion matrix grid
            cm = {t_label: {p_label: 0 for p_label in labels} for t_label in labels}
            
            # Calculate Accuracy 
            for item in results_list:
                expected = item.get("sample", {}).get("label")
                
                # Navigate the nested JSON maze
                classifications = item.get("classifications", [])
                if classifications and len(classifications) > 0:
                    res_list = classifications[0].get("result", [])
                    if res_list and len(res_list) > 0:
                        predictions = res_list[0] # This is {"yes": 0.93, "no": 0.06}
                        
                        if isinstance(predictions, dict) and predictions:
                            predicted = max(predictions, key=predictions.get)
                            
                            if expected == predicted:
                                correct += 1
                                
                            if expected in cm and predicted in cm[expected]:
                                cm[expected][predicted] += 1
                                
            # Final Math
            test_acc = (correct / total) * 100
            print(f"TEST ACCURACY (Unseen Data): {test_acc:.2f}%\n")
            
            print("Test Data Confusion Matrix:")
            header = f"{'':>10} | " + " | ".join([f"{l:>8}" for l in labels])
            print(header)
            print("-" * len(header))
            for t_label in labels:
                row_str = " | ".join([f"{cm[t_label][p_label]:>8}" for p_label in labels])
                print(f"{t_label:>10} | {row_str}")
        else:
            print("Testing list is empty. No test data available.")
    else:
        print(f"Could not fetch test data metrics: {test_res.status_code}")

    print("-" * 50)

    # FETCH HARDWARE METRICS 
    learn_id = get_learn_id()
    if learn_id:
        hw_res = requests.get(f"{BASE_URL}/training/keras/{learn_id}/metadata", headers=HEADERS)
        if hw_res.status_code == 200:
            hw_data = hw_res.json()
            metrics_list = hw_data.get("modelValidationMetrics", [])
            
            target_metrics = next((m for m in metrics_list if m.get("type") == "int8"), 
                                 next((m for m in metrics_list if m.get("type") == "float32"), metrics_list[0] if metrics_list else {}))
            
            val_acc_data = target_metrics.get("accuracy", 0)
            val_acc = val_acc_data.get("raw", 0) * 100 if isinstance(val_acc_data, dict) else float(val_acc_data) * 100
            
            profile = target_metrics.get("profile", {})
            eon_profile = profile.get("eon", profile.get("tflite", {}))
            
            print(f"Validation Accuracy (During Training): {val_acc:.2f}%")
            
            latency = eon_profile.get('timePerInferenceMs', 0)
            ram = eon_profile.get('ram', 0)
            rom = eon_profile.get('rom', 0)
            
            if latency == 0 and ram == 0:
                print("Hardware profile unavailable (dataset may be too small).")
            else:
                print(f"Latency / Inference Time: {latency} ms")
                print(f"Peak RAM Used:           {ram} bytes")
                print(f"Flash / ROM Used:        {rom} bytes")
                if latency > 20:
                    print(f"Latency exceeds threshold of 20 ms!")
                    exit(1)
                if ram > 20:
                    print(f"RAM usage exceeds threshold of 20 bytes!")
                    exit(1)
                if rom > 120:
                    print(f"ROM usage exceeds threshold of 120 bytes!")
                    exit(1)
                else:
                    print("Hardware metrics are within acceptable thresholds.")

    # Fail Closed Logic
    if test_acc is None:
        print("\n CI/CD GATE FAILED: Test Accuracy could not be calculated.")
        print("Halting pipeline. Deployment will NOT proceed.")
        exit(1)
    elif test_acc < 80.0:
        print(f"\n CI/CD GATE FAILED: Test Accuracy ({test_acc:.2f}%) is below 80%.")
        print("Halting pipeline. Deployment will NOT proceed.")
        exit(1)
    else:
        print("\n CI/CD GATE PASSED: Model is healthy and ready for deployment.")
    print("="*50 + "\n")

if __name__ == "__main__":
    job_id = start_testing()
    wait_for_job(job_id, max_retries=10, sleep_time=15)
    print_final_report()