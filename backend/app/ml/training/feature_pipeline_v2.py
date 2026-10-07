"""
Feature Pipeline & Multi-Modal Vectorizer V2 for VitaLens AI Model.
Transforms raw patient symptom text and 24 canonical biomarker records into
normalized 306-dimensional multi-modal tensors for PyTorch training and inference.

Feature Dimensions Breakdown:
- 256 dimensions: Sublinear TF-IDF unigram & bigram embeddings of clinical text
- 48 dimensions: Standardized continuous value and encoded flag for each of the 24 biomarkers
- 2 dimensions: Normalized clinical severity (0-1) and duration (0-1)
Total = 306 features.
"""

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler
import joblib

CANONICAL_BIOMARKERS_V2 = [
    "glucose_fasting", "hba1c", "total_cholesterol", "ldl_cholesterol",
    "hdl_cholesterol", "triglycerides", "hemoglobin", "wbc_count",
    "platelet_count", "alt_sgpt", "ast_sgot", "total_bilirubin",
    "serum_creatinine", "bun", "egfr", "tsh", "free_t4",
    "uric_acid", "crp", "esr",
    # 4 New Canonical Biomarkers
    "ferritin", "iron", "rbc_count", "hematocrit"
]

FLAG_ENCODING = {
    "NORMAL": 0.0,
    "LOW": -1.0,
    "CRITICAL_LOW": -2.0,
    "HIGH": 1.0,
    "CRITICAL_HIGH": 2.0,
    "CRITICAL": 2.0
}

class ClinicalFeaturePipelineV2:
    def __init__(self, max_tfidf_features: int = 256):
        self.max_tfidf_features = max_tfidf_features
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            max_features=max_tfidf_features,
            sublinear_tf=True,
            stop_words="english"
        )
        self.scaler = StandardScaler()
        self.is_fitted = False
        self.input_dim = max_tfidf_features + (len(CANONICAL_BIOMARKERS_V2) * 2) + 2

    def _extract_biomarker_features(self, df_or_dict_list):
        """Extracts numerical biomarker values and categorical flag vectors."""
        num_rows = len(df_or_dict_list)
        bio_matrix = np.zeros((num_rows, len(CANONICAL_BIOMARKERS_V2) * 2), dtype=np.float32)
        meta_matrix = np.zeros((num_rows, 2), dtype=np.float32)

        for i, row in enumerate(df_or_dict_list):
            row_get = lambda k, default=0.0: row[k] if (hasattr(row, '__getitem__') and k in row) else default

            for j, b_name in enumerate(CANONICAL_BIOMARKERS_V2):
                val = float(row_get(f"val_{b_name}", 0.0))
                flag_str = str(row_get(f"flag_{b_name}", "NORMAL")).upper()
                flag_val = FLAG_ENCODING.get(flag_str, 0.0)

                bio_matrix[i, j * 2] = val
                bio_matrix[i, j * 2 + 1] = flag_val

            meta_matrix[i, 0] = float(row_get("severity_score", 5.0)) / 10.0
            meta_matrix[i, 1] = min(float(row_get("duration_days", 7.0)) / 90.0, 1.0)

        return np.hstack([bio_matrix, meta_matrix])

    def fit(self, df_or_rows):
        """Fits text vectorizer and numerical scaler strictly on training data."""
        if hasattr(df_or_rows, "to_dict"):
            rows = df_or_rows.to_dict(orient="records")
        else:
            rows = df_or_rows

        texts = [str(r.get("full_text", "")) for r in rows]
        self.vectorizer.fit(texts)

        dense_features = self._extract_biomarker_features(rows)
        self.scaler.fit(dense_features)

        self.is_fitted = True
        return self

    def transform(self, df_or_rows) -> np.ndarray:
        """Transforms clinical input records into the 306-dimensional dense feature matrix."""
        if not self.is_fitted:
            raise RuntimeError("ClinicalFeaturePipelineV2 must be fitted before transforming data.")

        if hasattr(df_or_rows, "to_dict"):
            rows = df_or_rows.to_dict(orient="records")
        elif isinstance(df_or_rows, dict):
            rows = [df_or_rows]
        else:
            rows = df_or_rows

        texts = [str(r.get("full_text", "")) for r in rows]
        text_tfidf = self.vectorizer.transform(texts).toarray().astype(np.float32)

        dense_features = self._extract_biomarker_features(rows)
        scaled_dense = self.scaler.transform(dense_features).astype(np.float32)

        combined = np.hstack([text_tfidf, scaled_dense])
        return combined

    def fit_transform(self, df_or_rows) -> np.ndarray:
        return self.fit(df_or_rows).transform(df_or_rows)

    def save(self, filepath: str):
        joblib.dump(self, filepath)

    @classmethod
    def load(cls, filepath: str) -> "ClinicalFeaturePipelineV2":
        return joblib.load(filepath)
