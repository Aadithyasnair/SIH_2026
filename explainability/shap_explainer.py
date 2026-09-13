"""
SHAP Explainer Module for SIH26146 Explainability Layer (Module D).

Purpose:
Obtains top-3 model-derived feature contributors per transaction with direction (increased/decreased risk).
Supports loading real trained models from Module C (ml_detection/models/) and executing SHAP,
with a lightweight feature-importance fallback when SHAP is too slow or offline dependencies are restricted.
"""

import os
import sys
from typing import List, Dict, Any, Optional

# Attempt optional shap and joblib imports
try:
    import joblib
except ImportError:
    joblib = None

try:
    import shap
except ImportError:
    shap = None


DEFAULT_MODEL_PATH = "ml_detection/models/isolation_forest.joblib"


class SHAPExplainer:
    def __init__(self, model_path: Optional[str] = None):
        """
        Initializes the explainer. Attempts to load trained model from Module C.
        """
        self.model_path = model_path or DEFAULT_MODEL_PATH
        self.model = None
        self.explainer = None
        self._load_model()

    def _load_model(self):
        """Attempts to load trained model from joblib file if present."""
        if joblib and os.path.exists(self.model_path):
            try:
                self.model = joblib.load(self.model_path)
                if shap and hasattr(self.model, "predict"):
                    # Initialize SHAP TreeExplainer or KernelExplainer
                    try:
                        self.explainer = shap.TreeExplainer(self.model)
                    except Exception:
                        self.explainer = None
            except Exception as e:
                self.model = None
                self.explainer = None

    def explain_transaction(
        self,
        feature_dict: Dict[str, float],
        top_n: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        Obtains the top N feature contributors for a single transaction.

        :param feature_dict: Dictionary of feature_name -> feature_value
        :param top_n: Number of top contributing features to return (default 3)
        :return: List of dicts, e.g. [{"feature": "amount_zscore", "value": 3.2, "direction": "increased"}]
        """
        if not feature_dict:
            return []

        # If SHAP and model exist, compute SHAP values
        if self.model and self.explainer:
            try:
                import numpy as np
                feature_names = list(feature_dict.keys())
                feature_vector = np.array([[feature_dict[k] for k in feature_names]])
                shap_values = self.explainer.shap_values(feature_vector)
                
                if isinstance(shap_values, list):
                    shap_values = shap_values[0]
                if len(shap_values.shape) > 1:
                    shap_values = shap_values[0]
                    
                contributions = []
                for name, s_val, f_val in zip(feature_names, shap_values, feature_vector[0]):
                    direction = "increased" if s_val > 0 else "decreased"
                    contributions.append({
                        "feature": name,
                        "value": float(f_val),
                        "importance": abs(float(s_val)),
                        "direction": direction,
                    })
                    
                contributions.sort(key=lambda x: x["importance"], reverse=True)
                return contributions[:top_n]
            except Exception:
                # Fallback if SHAP calculation fails at runtime
                pass

        # Lightweight Feature-Importance Fallback
        # Evaluate feature contribution magnitude based on normalized absolute deviation
        contributions = []
        for name, val in feature_dict.items():
            f_val = float(val)
            # Determine direction: values > 0.5 or positive deviation increase risk signal
            direction = "increased" if f_val > 0.0 else "decreased"
            importance = abs(f_val)
            
            contributions.append({
                "feature": name,
                "value": f_val,
                "importance": importance,
                "direction": direction,
            })

        contributions.sort(key=lambda x: x["importance"], reverse=True)
        return contributions[:top_n]


def get_top_contributors(
    feature_dict: Dict[str, float],
    model_path: Optional[str] = None,
    top_n: int = 3,
) -> List[Dict[str, Any]]:
    """Convenience helper function to get top contributors per transaction."""
    explainer = SHAPExplainer(model_path=model_path)
    return explainer.explain_transaction(feature_dict=feature_dict, top_n=top_n)
