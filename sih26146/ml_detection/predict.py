"""
Shim re-exporting ml_detection.predict for sih26146 package compatibility.
"""
from ml_detection.predict import score_transactions, load_model_artifacts, clear_artifact_cache

__all__ = ["score_transactions", "load_model_artifacts", "clear_artifact_cache"]
