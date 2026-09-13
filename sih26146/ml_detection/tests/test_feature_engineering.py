"""
sih26146/ml_detection/tests — re-exports all Module C tests so the canonical
verification gate `pytest sih26146/ml_detection/tests/ -v` works identically
to `pytest ml_detection/tests/ -v`.
All test logic lives in ml_detection/tests/*.
"""
from ml_detection.tests.test_feature_engineering import *
