# model_service.py
from __future__ import annotations
import os
import numpy as np
import pandas as pd
import joblib

# ⚠️ IMPORTANT : sécurité pickle/joblib
# Ne charger que des fichiers de confiance.

class CrisisRiskModel:
    def __init__(self, artifacts: dict, alpha: float = 0.6):
        """
        artifacts : dict attendu avec clés :
          - preprocessor : ColumnTransformer
          - seq_length : int
          - feature_input_cols : list[str]
          - numeric_features : list[str]
          - categorical_features : list[str] (ex: ["Genotype"])
          - lstm_model : tf.keras.Model (optionnel si sauvé à part)
          - xgb_model : xgboost.XGBClassifier (ou sklearn-like)
        alpha : pondération LSTM (alpha) vs tabulaire (1-alpha)
        """
        self.pre = artifacts.get("preprocessor")
        self.seq_length = int(artifacts.get("seq_length", 14))
        self.feature_input_cols = list(artifacts.get("feature_input_cols", []))
        self.numeric_features = list(artifacts.get("numeric_features", []))
        self.categorical_features = list(artifacts.get("categorical_features", []))
        self.lstm = artifacts.get("lstm_model", None)
        self.xgb = artifacts.get("xgb_model", None)
        self.alpha = float(alpha)

    def _make_sequences(self, X_all: np.ndarray) -> np.ndarray:
        """Fabrique des fenêtres (n-seq, seq_len, n_feat) sur X_all déjà transformé."""
        L = self.seq_length
        X_seq = []
        for i in range(L-1, len(X_all)):
            window = X_all[i-(L-1):i+1]
            X_seq.append(window)
        return np.array(X_seq) if X_seq else np.empty((0, L, X_all.shape[1]))

    def predict_proba_series(self, df_patient: pd.DataFrame) -> pd.Series:
        """
        df_patient : trié par date croissante, doit contenir les colonnes feature_input_cols.
        Retourne une Series alignée sur df_patient["date"] avec proba (0..1).
        """
        assert "date" in df_patient.columns, "df_patient doit contenir une colonne 'date'."
        # 1) complétion des colonnes attendues
        for c in self.feature_input_cols:
            if c not in df_patient.columns:
                # défauts raisonnables (à ajuster selon ton dataset)
                df_patient[c] = 0 if c not in self.categorical_features else "SS"

        # 2) preprocess tabulaire
        X_all = self.pre.transform(df_patient[self.feature_input_cols])
        # X_all est (n_day, n_feat_encodés)
        # 3) séquences pour LSTM
        X_seq = self._make_sequences(X_all)

        # 4) prédictions tabulaires (dernier jour de chaque fenêtre)
        p_tab = None
        if self.xgb is not None:
            # on prend la ligne correspondante à chaque fenêtre (dernier index)
            idx_last_each_window = list(range(self.seq_length-1, len(df_patient)))
            X_tab = X_all[idx_last_each_window]
            if hasattr(self.xgb, "predict_proba"):
                p_tab = self.xgb.predict_proba(X_tab)[:, 1]
            else:
                # fallback pour modèles régressifs
                p_tab = self.xgb.predict(X_tab).ravel()

        # 5) prédictions LSTM (si dispo)
        p_seq = None
        if (self.lstm is not None) and (len(X_seq) > 0):
            import tensorflow as tf  # import tardif pour éviter coût si non nécessaire
            p = self.lstm.predict(X_seq, verbose=0)
            p_seq = p.reshape(-1)

        # 6) combinaison
        if p_seq is not None and p_tab is not None:
            p_h = self.alpha * p_seq + (1.0 - self.alpha) * p_tab
        elif p_seq is not None:
            p_h = p_seq
        elif p_tab is not None:
            p_h = p_tab
        else:
            # rien ne marche : retourner 0.0
            p_h = np.zeros(max(0, len(df_patient) - (self.seq_length - 1)))

        # 7) ré-alignement sur toutes les dates (les (L-1) 1ers jours n’ont pas de séquence)
        out = pd.Series(index=df_patient.index, dtype=float)
        # pour les premiers jours : on propage la première proba dispo (ou 0.0)
        first_val = float(p_h[0]) if len(p_h) else 0.0
        out.iloc[:self.seq_length-1] = first_val
        out.iloc[self.seq_length-1:] = p_h
        # clamp (au cas où)
        return out.clip(0.0, 1.0)

# -------- API module-level avec cache Streamlit
_model_cache = None

def load_model(pkl_path: str, keras_path: str | None = None, alpha: float = 0.6) -> CrisisRiskModel:
    """
    pkl_path : chemin vers hybrid_crisis_predictor.pkl (artifacts)
    keras_path : si le LSTM n’a pas pu être picklé, fournis le chemin '.keras' (optionnel)
    """
    global _model_cache
    if _model_cache is not None:
        return _model_cache

    artifacts = joblib.load(pkl_path)

    # Si le LSTM n’est pas dans le pkl, on tente un chargement séparé
    if artifacts.get("lstm_model", None) is None and keras_path and os.path.exists(keras_path):
        import tensorflow as tf
        artifacts["lstm_model"] = tf.keras.models.load_model(keras_path)

    _model_cache = CrisisRiskModel(artifacts, alpha=alpha)
    return _model_cache

def predict_patient_timeseries(df_patient: pd.DataFrame, pkl_path: str, keras_path: str | None = None, alpha: float = 0.6) -> pd.Series:
    """
    df_patient : DataFrame patient (doit avoir 'date' triée ASC + colonnes features).
    Retourne une Series 'risk' (0..100).
    """
    model = load_model(pkl_path, keras_path=keras_path, alpha=alpha)
    probs = model.predict_proba_series(df_patient.sort_values("date").reset_index(drop=True))
    return (probs * 100.0).round(0)
