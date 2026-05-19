import pytest
import pandas as pd
from app.etl.transform import transform_data, normalize_zone_name
from datetime import date


class TestTransform:
    def test_transform_empty_list(self):
        df = transform_data([])
        assert df.empty

    def test_transform_basic_data(self):
        raw = [
            {"fecha": "2026-05-01", "temperatura": "22.5", "humedad": "60", "municipio": "madrid"},
            {"fecha": "2026-05-02", "temperatura": "25.0", "humedad": "55", "municipio": "getafe"},
        ]
        df = transform_data(raw)
        assert len(df) == 2
        assert "fecha" in df.columns
        assert df["temperatura"].iloc[0] == 22.5
        assert df["humedad"].iloc[1] == 55.0

    def test_transform_removes_all_nan_rows(self):
        raw = [
            {"fecha": "2026-05-01", "temperatura": 22.0},
            {},
            {"fecha": "2026-05-02", "temperatura": 25.0},
        ]
        df = transform_data(raw)
        assert len(df) == 2

    def test_transform_deduplicates(self):
        raw = [
            {"fecha": "2026-05-01", "municipio": "Madrid", "temperatura": 22.0},
            {"fecha": "2026-05-01", "municipio": "Madrid", "temperatura": 23.0},
        ]
        df = transform_data(raw)
        assert len(df) == 1
        assert df["temperatura"].iloc[0] == 23.0

    def test_transform_coerces_numeric(self):
        raw = [{"temperatura": "invalid", "humedad": "80", "municipio": "madrid"}]
        df = transform_data(raw)
        assert pd.isna(df["temperatura"].iloc[0])
        assert df["humedad"].iloc[0] == 80.0

    def test_transform_fills_unknown(self):
        raw = [{"municipio": None, "temperatura": 20.0}]
        df = transform_data(raw)
        assert df["municipio"].iloc[0] == "Desconocido"

    def test_transform_municipio_title_case(self):
        raw = [{"municipio": "  madrid  ", "temperatura": 20.0}]
        df = transform_data(raw)
        assert df["municipio"].iloc[0] == "Centro"

    def test_normalize_zone(self):
        assert normalize_zone_name("Mostoles") == "Sur"
        assert normalize_zone_name("Alcalá de Henares") == "Este"
        assert normalize_zone_name("Madrid") == "Centro"
        assert normalize_zone_name("Toledo") == "Toledo"

    def test_transform_filters_future_dates(self):
        from datetime import timedelta
        future = (date.today() + timedelta(days=10)).isoformat()
        raw = [
            {"fecha": future, "temperatura": 25.0, "municipio": "Madrid"},
            {"fecha": "2026-05-01", "temperatura": 22.0, "municipio": "Getafe"},
        ]
        df = transform_data(raw)
        assert all(df["fecha"].dt.date <= date.today())

    def test_transform_converts_date_column(self):
        raw = [{"fecha": "2026-05-01", "temperatura": 22.0, "municipio": "madrid"}]
        df = transform_data(raw)
        assert pd.api.types.is_datetime64_any_dtype(df["fecha"])

    def test_transform_alertas_column(self):
        raw = [
            {"temperatura": 20.0, "alertas": "texto_invalido", "municipio": "madrid"},
            {"temperatura": 25.0, "alertas": ["rojo"], "municipio": "getafe"},
        ]
        df = transform_data(raw)
        assert df["alertas"].iloc[0] == []
        assert df["alertas"].iloc[1] == ["rojo"]

    def test_transform_column_not_present(self):
        raw = [{"temp": 20.0}]
        df = transform_data(raw)
        assert not df.empty
        assert "fecha" not in df.columns
