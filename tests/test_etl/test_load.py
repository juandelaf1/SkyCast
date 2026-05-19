import pytest
import pandas as pd
from datetime import datetime
from app.etl.load import load_data, pd_to_datetime, run_pipeline


class TestLoad:
    def test_pd_to_datetime_with_timestamp(self):
        ts = pd.Timestamp("2026-05-01 12:00:00")
        result = pd_to_datetime(ts)
        assert isinstance(result, datetime)
        assert result.year == 2026
        assert result.month == 5

    def test_pd_to_datetime_with_datetime(self):
        dt = datetime(2026, 5, 1, 12, 0, 0)
        result = pd_to_datetime(dt)
        assert result is dt

    def test_pd_to_datetime_with_string(self):
        result = pd_to_datetime("2026-05-01T12:00:00")
        assert isinstance(result, datetime)
        assert result.year == 2026

    def test_pd_to_datetime_with_invalid_string(self):
        result = pd_to_datetime("not-a-date")
        assert isinstance(result, datetime)

    def test_load_data_empty_df(self, db_session):
        df = pd.DataFrame()
        result = load_data(df, db_session)
        assert result == 0

    def test_load_data_with_valid_data(self, db_session):
        from app.db.models import Estacion
        estacion = db_session.query(Estacion).first()
        df = pd.DataFrame([{
            "estacion_id": estacion.indicativo,
            "fecha": datetime(2026, 5, 1, 12, 0, 0),
            "temperatura": 22.5,
            "humedad": 55.0,
            "viento": 12.0,
            "lluvia": 0.0,
        }])
        result = load_data(df, db_session)
        assert result == 1

    def test_load_data_skips_existing(self, db_session):
        from app.db.models import Estacion
        estacion = db_session.query(Estacion).first()
        row = {
            "estacion_id": estacion.indicativo,
            "fecha": datetime(2026, 5, 1, 12, 0, 0),
            "temperatura": 22.5, "humedad": 55.0, "viento": 12.0, "lluvia": 0.0,
        }
        df1 = pd.DataFrame([row])
        assert load_data(df1, db_session) == 1
        df2 = pd.DataFrame([row])
        assert load_data(df2, db_session) == 0

    def test_load_data_unknown_station(self, db_session):
        df = pd.DataFrame([{
            "estacion_id": "NOEXISTE",
            "fecha": datetime(2026, 5, 1, 12, 0, 0),
            "temperatura": 22.5, "humedad": 55.0, "viento": 12.0, "lluvia": 0.0,
        }])
        result = load_data(df, db_session, source_code="manual")
        assert result == 0

    def test_run_pipeline_nonexistent_file(self, db_session):
        result = run_pipeline("/no/existe.json", db_session)
        assert result["errors"] == 1
        assert result["extracted"] == 0

    def test_run_pipeline_empty_file(self, db_session, tmp_path):
        import json
        f = tmp_path / "empty.json"
        f.write_text("[]")
        result = run_pipeline(str(f), db_session)
        assert result["extracted"] == 0
        assert result["transformed"] == 0
        assert result["loaded"] == 0

    def test_run_pipeline_success(self, db_session, tmp_path):
        import json
        from app.db.models import Estacion
        estacion = db_session.query(Estacion).first()
        data = [{
            "estacion_id": estacion.indicativo,
            "fecha": "2026-05-01", "temperatura": 22.5, "humedad": 55.0,
            "viento": 12.0, "lluvia": 0.0, "municipio": "Madrid",
        }]
        f = tmp_path / "data.json"
        f.write_text(json.dumps(data))
        result = run_pipeline(str(f), db_session)
        assert result["extracted"] == 1
        assert result["transformed"] == 1
        assert result["loaded"] == 1

    def test_run_pipeline_twice_dedup(self, db_session, tmp_path):
        import json
        from app.db.models import Estacion
        estacion = db_session.query(Estacion).first()
        data = [{
            "estacion_id": estacion.indicativo,
            "fecha": "2026-05-01", "temperatura": 22.5, "humedad": 55.0,
            "viento": 12.0, "lluvia": 0.0, "municipio": "Madrid",
        }]
        f = tmp_path / "data2.json"
        f.write_text(json.dumps(data))
        r1 = run_pipeline(str(f), db_session)
        assert r1["loaded"] == 1
        r2 = run_pipeline(str(f), db_session)
        assert r2["loaded"] == 0
