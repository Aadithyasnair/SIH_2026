"""
Shim re-exporting ml_detection.evaluate_model for sih26146 package compatibility.
"""
from ml_detection.evaluate_model import evaluate_model, main

if __name__ == "__main__":
    main()
