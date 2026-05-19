import pytest
import json
import tempfile
from pathlib import Path
from app.etl.extract import extract_data, extract_from_db


class TestExtract:
    def test_extract_valid_json(self):
        records = [{"temperatura": 20.0}, {"temperatura": 25.0}]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump(records, f)
            fpath = f.name
        result = extract_data(fpath)
        assert result == records
        Path(fpath).unlink()

    def test_extract_empty_json(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump([], f)
            fpath = f.name
        result = extract_data(fpath)
        assert result == []
        Path(fpath).unlink()

    def test_extract_file_not_found(self):
        result = extract_data("/no/existe/data.json")
        assert result is None

    def test_extract_invalid_json(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
            f.write("not json")
            fpath = f.name
        result = extract_data(fpath)
        assert result is None
        Path(fpath).unlink()

    def test_extract_single_record(self):
        record = {"temperatura": 22.5, "humedad": 55.0}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump(record, f)
            fpath = f.name
        result = extract_data(fpath)
        assert result is not None
        Path(fpath).unlink()

    def test_extract_from_db(self, db_session):
        from app.db.models import FuenteDato
        result = extract_from_db(db_session, FuenteDato)
        assert len(result) >= 2
        assert any(f.codigo == "aemet" for f in result)
        assert any(f.codigo == "manual" for f in result)

    def test_extract_from_db_with_filters(self, db_session):
        from app.db.models import FuenteDato
        result = extract_from_db(db_session, FuenteDato, {"codigo": "aemet"})
        assert len(result) == 1
        assert result[0].codigo == "aemet"

    def test_extract_from_db_no_results(self, db_session):
        from app.db.models import FuenteDato
        result = extract_from_db(db_session, FuenteDato, {"codigo": "noexiste"})
        assert result == []
