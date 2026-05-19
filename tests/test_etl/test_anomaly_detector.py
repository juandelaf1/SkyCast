import pytest
import pandas as pd
import numpy as np
from app.etl.anomaly_detector import AnomalyDetector


class TestAnomalyDetector:
    def setup_method(self):
        self.detector = AnomalyDetector(std_threshold=2.0)

    def test_no_anomalies_constant_data(self):
        df = pd.DataFrame({"temperatura": [20.0] * 10})
        mask = self.detector.detect_anomalies(df)
        assert mask.sum() == 0

    def test_detect_anomaly_std(self):
        temps = [20.0] * 20 + [50.0] + [20.0] * 20
        df = pd.DataFrame({"temperatura": temps})
        mask = self.detector.detect_anomalies(df)
        assert mask.iloc[20]

    def test_no_false_positive_normal_distribution(self):
        np.random.seed(42)
        temps = np.random.normal(20, 2, 100).tolist()
        df = pd.DataFrame({"temperatura": temps})
        mask = self.detector.detect_anomalies(df)
        anomaly_count = mask.sum()
        assert anomaly_count <= 6

    def test_detect_no_column(self):
        df = pd.DataFrame({"temp": [20, 30]})
        mask = self.detector.detect_anomalies(df, column="temperatura")
        assert mask.sum() == 0

    def test_detect_all_nan(self):
        df = pd.DataFrame({"temperatura": [None, None, None]})
        mask = self.detector.detect_anomalies(df)
        assert mask.sum() == 0

    def test_fewer_than_3_rows(self):
        df = pd.DataFrame({"temperatura": [20, 25]})
        mask = self.detector.detect_anomalies(df)
        assert mask.sum() == 0

    def test_zero_std(self):
        df = pd.DataFrame({"temperatura": [30] * 5})
        mask = self.detector.detect_anomalies(df)
        assert mask.sum() == 0

    def test_outliers_iqr(self):
        data = [10, 12, 11, 13, 12, 100, 11, 13, 12, 14]
        df = pd.DataFrame({"temperatura": data})
        mask = self.detector.detect_outliers_iqr(df, "temperatura")
        assert mask.iloc[5]
        assert mask.sum() == 1

    def test_outliers_iqr_no_outliers(self):
        data = [10, 11, 12, 13, 14, 11, 12]
        df = pd.DataFrame({"temperatura": data})
        mask = self.detector.detect_outliers_iqr(df, "temperatura")
        assert mask.sum() == 0

    def test_outliers_iqr_fewer_than_4(self):
        df = pd.DataFrame({"temperatura": [10, 11, 12]})
        mask = self.detector.detect_outliers_iqr(df, "temperatura")
        assert mask.sum() == 0

    def test_anomaly_summary(self):
        temps = [20] * 20 + [60] + [20] * 20
        df = pd.DataFrame({"temperatura": temps, "humedad": [50] * 41})
        summary = self.detector.get_anomaly_summary(df)
        assert "temperatura" in summary
        assert summary["temperatura"]["count"] >= 1
        assert "mean" in summary["temperatura"]
        assert "std" in summary["temperatura"]

    def test_anomaly_summary_no_anomalies(self):
        df = pd.DataFrame({"temperatura": [20] * 10, "humedad": [50] * 10})
        summary = self.detector.get_anomaly_summary(df)
        assert summary == {}
