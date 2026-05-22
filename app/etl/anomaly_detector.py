import pandas as pd
import logging

logger = logging.getLogger(__name__)


class AnomalyDetector:
    def __init__(self, std_threshold: float = 2.0):
        self.std_threshold = std_threshold

    def detect_anomalies(self, df: pd.DataFrame, column: str = "temperatura") -> pd.Series:
        if column not in df.columns or df[column].isna().all():
            return pd.Series([False] * len(df))

        series = df[column].dropna()
        if len(series) < 3:
            return pd.Series([False] * len(df))

        mean = series.mean()
        std = series.std()
        if std == 0:
            return pd.Series([False] * len(df))

        mask = abs(df[column] - mean) > (self.std_threshold * std)
        return mask.fillna(False)

    def get_anomaly_summary(
        self, df: pd.DataFrame, columns: list[str] | None = None
    ) -> dict:
        if columns is None:
            columns = ["temperatura", "humedad", "viento", "lluvia"]

        summary = {}
        for col in columns:
            if col not in df.columns:
                continue
            anomaly_mask = self.detect_anomalies(df, col)
            anomaly_df = df[anomaly_mask]
            if not anomaly_df.empty:
                summary[col] = {
                    "count": int(anomaly_mask.sum()),
                    "percentage": round(float(anomaly_mask.sum() / len(df) * 100), 2),
                    "values": anomaly_df[col].tolist(),
                    "mean": float(df[col].mean()),
                    "std": float(df[col].std()),
                }
        return summary

    def detect_outliers_iqr(self, df: pd.DataFrame, column: str, factor: float = 1.5) -> pd.Series:
        if column not in df.columns:
            return pd.Series([False] * len(df))

        series = df[column].dropna()
        if len(series) < 4:
            return pd.Series([False] * len(df))

        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        lower = q1 - factor * iqr
        upper = q3 + factor * iqr

        mask = (df[column] < lower) | (df[column] > upper)
        return mask.fillna(False)