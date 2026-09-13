"""
ML Models for Module C (AI/ML Detection).
Includes:
1. Isolation Forest (unsupervised tree-based anomaly detector)
2. Feedforward Autoencoder in PyTorch (unsupervised neural reconstruction error)
3. Explicit score normalization and weighted ensemble combination
"""
from typing import Dict, Any, Tuple, Optional
import os
import joblib
import numpy as np
from sklearn.ensemble import IsolationForest
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset


class Autoencoder(nn.Module):
    """
    Feedforward Autoencoder for learning normal Bitcoin transaction representations.
    Anomalies exhibit higher reconstruction error.
    """
    def __init__(self, input_dim: int, latent_dim: int = 8):
        super().__init__()
        self.input_dim = input_dim
        self.latent_dim = latent_dim

        # Encoder: compresses input features into lower-dimensional bottleneck
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 16),
            nn.ReLU(),
            nn.Linear(16, latent_dim),
        )

        # Decoder: reconstructs the original feature representation from bottleneck
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, 16),
            nn.ReLU(),
            nn.Linear(16, 32),
            nn.ReLU(),
            nn.Linear(32, input_dim),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        latent = self.encoder(x)
        reconstructed = self.decoder(latent)
        return reconstructed


def train_isolation_forest(
    X_scaled: np.ndarray,
    contamination: float = 0.12,
    random_state: int = 42,
) -> Tuple[IsolationForest, float, float]:
    """
    Train Isolation Forest on scaled features.
    Returns: (fitted_model, s_min, s_max) for inference normalization.
    """
    model = IsolationForest(
        n_estimators=150,
        contamination=contamination,
        random_state=random_state,
        n_jobs=-1,
    )
    model.fit(X_scaled)

    # In scikit-learn, score_samples returns opposite of anomaly score (lower is more anomalous)
    # Negating it makes higher values correspond to greater anomaly
    raw_scores = -model.score_samples(X_scaled)
    # Robust percentile calibration prevents single-point outlier skew
    s_min = float(np.percentile(raw_scores, 1.0))
    s_max = float(np.percentile(raw_scores, 99.0))
    if abs(s_max - s_min) < 1e-7:
        s_max = s_min + 1.0

    return model, s_min, s_max


def score_isolation_forest(
    model: IsolationForest,
    X_scaled: np.ndarray,
    s_min: float,
    s_max: float,
) -> np.ndarray:
    """
    Compute normalized Isolation Forest anomaly scores in [0, 1].
    Higher = more anomalous.
    """
    raw = -model.score_samples(X_scaled)
    denom = max(s_max - s_min, 1e-7)
    norm = (raw - s_min) / denom
    return np.clip(norm, 0.0, 1.0)


def train_autoencoder(
    X_scaled: np.ndarray,
    latent_dim: int = 8,
    epochs: int = 150,
    lr: float = 0.003,
    batch_size: int = 64,
    random_state: int = 42,
) -> Tuple[Autoencoder, float, float]:
    """
    Train PyTorch Feedforward Autoencoder to reconstruct scaled feature vectors.
    Returns: (trained_model, err_min, err_max) for inference normalization.
    """
    torch.manual_seed(random_state)
    np.random.seed(random_state)

    input_dim = X_scaled.shape[1]
    model = Autoencoder(input_dim=input_dim, latent_dim=latent_dim)
    model.train()

    dataset = TensorDataset(torch.tensor(X_scaled, dtype=torch.float32))
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-5)
    criterion = nn.MSELoss()

    for epoch in range(epochs):
        for batch in loader:
            inputs = batch[0]
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, inputs)
            loss.backward()
            optimizer.step()

    # Compute training reconstruction errors for calibration
    model.eval()
    with torch.no_grad():
        x_tensor = torch.tensor(X_scaled, dtype=torch.float32)
        recons = model(x_tensor)
        errors = torch.mean((x_tensor - recons) ** 2, dim=1).numpy()

    # Robust percentile calibration (2nd and 96th percentiles) for heavy-tailed reconstruction error
    err_min = float(np.percentile(errors, 2.0))
    err_max = float(np.percentile(errors, 96.0))
    if abs(err_max - err_min) < 1e-7:
        err_max = err_min + 1.0

    return model, err_min, err_max


def score_autoencoder(
    model: Autoencoder,
    X_scaled: np.ndarray,
    err_min: float,
    err_max: float,
) -> np.ndarray:
    """
    Compute normalized Autoencoder reconstruction anomaly scores in [0, 1].
    Higher = more anomalous.
    """
    model.eval()
    with torch.no_grad():
        x_tensor = torch.tensor(X_scaled, dtype=torch.float32)
        recons = model(x_tensor)
        errors = torch.mean((x_tensor - recons) ** 2, dim=1).numpy()

    denom = max(err_max - err_min, 1e-7)
    norm = (errors - err_min) / denom
    return np.clip(norm, 0.0, 1.0)


def combine_anomaly_scores(
    if_scores: np.ndarray,
    ae_scores: np.ndarray,
    alpha: float = 0.70,
) -> np.ndarray:
    """
    Combine Isolation Forest and Autoencoder scores into single anomaly_score in [0, 1].
    alpha: weight assigned to Isolation Forest (default 0.70 for primary tree-based detector).
    """
    combined = alpha * if_scores + (1.0 - alpha) * ae_scores
    return np.clip(combined, 0.0, 1.0)
