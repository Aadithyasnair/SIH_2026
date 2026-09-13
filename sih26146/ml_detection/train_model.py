"""
Shim re-exporting ml_detection.train_model for sih26146 package compatibility.
"""
from ml_detection.train_model import train_pipeline, main

if __name__ == "__main__":
    main()
