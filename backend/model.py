import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
import joblib
import os
import time

MODEL_PATH = "model.joblib"

class AnomalyModel:
    def __init__(self):
        self.model = None
        self.last_trained = 0
        self.load_model()
        
    def load_model(self):
        if os.path.exists(MODEL_PATH):
            try:
                self.model = joblib.load(MODEL_PATH)
                self.last_trained = os.path.getmtime(MODEL_PATH)
            except Exception as e:
                print(f"Error loading model: {e}")
                self.train_baseline()
        else:
            self.train_baseline()
            
    def train_baseline(self):
        print("Training baseline model with mock data...")
        # Generate some dummy "normal" traffic features
        np.random.seed(42)
        n_samples = 1000
        
        X = pd.DataFrame({
            'packet_count': np.random.poisson(10, n_samples),
            'byte_count': np.random.normal(5000, 1000, n_samples),
            'avg_packet_size': np.random.normal(500, 100, n_samples),
            'packet_rate': np.random.normal(5, 2, n_samples),
            'unique_dst_ports': np.random.poisson(1, n_samples),
            'syn_count': np.random.poisson(0.5, n_samples),
            'syn_without_ack_ratio': np.random.uniform(0, 0.1, n_samples),
            'protocol_entropy': np.random.uniform(0.5, 1.5, n_samples),
            'duration': np.random.uniform(1, 5, n_samples),
            'bytes_per_second': np.random.normal(1000, 200, n_samples)
        })
        
        self.model = IsolationForest(n_estimators=200, contamination=0.02, random_state=42)
        self.model.fit(X)
        joblib.dump(self.model, MODEL_PATH)
        self.last_trained = time.time()
        print("Baseline model trained and saved.")
        
    def retrain(self, features_df):
        if len(features_df) < 50:
            print("Not enough samples to retrain.")
            return False
            
        self.model = IsolationForest(n_estimators=200, contamination=0.02)
        self.model.fit(features_df)
        joblib.dump(self.model, MODEL_PATH)
        self.last_trained = time.time()
        return True

    def score(self, features_dict):
        if not self.model:
            return 0.0, "normal"
            
        # Ensure correct column order
        cols = [
            'packet_count', 'byte_count', 'avg_packet_size', 'packet_rate',
            'unique_dst_ports', 'syn_count', 'syn_without_ack_ratio',
            'protocol_entropy', 'duration', 'bytes_per_second'
        ]
        
        row = {c: features_dict.get(c, 0) for c in cols}
        df = pd.DataFrame([row])
        
        score = self.model.decision_function(df)[0]
        
        if score > 0.1:
            severity = "low"
        elif score > 0.0:
            severity = "medium"
        elif score > -0.1:
            severity = "high"
        else:
            severity = "critical"
            
        return float(score), severity

anomaly_model = AnomalyModel()
