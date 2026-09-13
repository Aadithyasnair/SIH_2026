import os
import json
import sys
from pathlib import Path

# Add repo root to path
REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from sih26146.shared.schemas.records import Alert, Cluster, NetworkEvent, BlockchainTxn

def validate_file(file_path, model_cls):
    if not os.path.exists(file_path):
        print(f"File {file_path} does not exist yet (skipping sample validation for missing file).")
        return True
    
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    if isinstance(data, dict):
        data = [data]
        
    validated_count = 0
    for idx, item in enumerate(data):
        try:
            model_cls(**item)
            validated_count += 1
        except Exception as e:
            print(f"Validation error in {file_path} at index {idx}: {e}")
            return False
            
    print(f"Successfully validated {validated_count} records in {file_path}")
    return True

def main():
    sample_dir = REPO_ROOT / "sih26146" / "shared" / "sample_data"
    alerts_json = REPO_ROOT / "alerts.json"
    explainability_alerts = REPO_ROOT / "sih26146" / "explainability" / "alerts.json"
    
    all_valid = True
    
    if alerts_json.exists():
        all_valid = validate_file(alerts_json, Alert) and all_valid
    if explainability_alerts.exists():
        all_valid = validate_file(explainability_alerts, Alert) and all_valid
        
    sample_alerts = sample_dir / "alerts.json"
    if sample_alerts.exists():
        all_valid = validate_file(sample_alerts, Alert) and all_valid

    if all_valid:
        print("All existing sample and output alert records are valid!")
        sys.exit(0)
    else:
        print("Schema validation failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
