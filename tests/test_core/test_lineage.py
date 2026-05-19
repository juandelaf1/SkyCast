from app.core.lineage import LineageLogger


class TestLineageLogger:
    def test_init_creates_first_step(self):
        ll = LineageLogger(source="test")
        assert len(ll.steps) == 1
        assert ll.steps[0]["step"] == "init"
        assert ll.steps[0]["source"] == "test"

    def test_log_extract(self):
        ll = LineageLogger(source="aemet")
        ll.log_extract(100, details="Extracted from JSON")
        assert ll.get_extracted_count() == 100
        assert ll.steps[1]["step"] == "extract"
        assert ll.steps[1]["rows_out"] == 100

    def test_log_transform(self):
        ll = LineageLogger(source="aemet")
        ll.log_transform(rows_in=100, rows_out=80, rows_discarded=20)
        assert ll.steps[1]["rows_in"] == 100
        assert ll.steps[1]["rows_out"] == 80
        assert ll.steps[1]["rows_discarded"] == 20

    def test_log_load(self):
        ll = LineageLogger(source="aemet")
        ll.log_load(rows_in=80, rows_loaded=75, rows_duplicates=5)
        assert ll.steps[1]["rows_in"] == 80
        assert ll.steps[1]["rows_out"] == 75
        assert ll.steps[1]["rows_discarded"] == 5

    def test_full_pipeline(self):
        ll = LineageLogger(source="manual")
        ll.log_extract(150)
        ll.log_transform(rows_in=150, rows_out=120, rows_discarded=30)
        ll.log_load(rows_in=120, rows_loaded=115, rows_duplicates=5)

        summary = ll.summary()
        assert summary["total_rows_loaded"] == 115
        assert summary["source"] == "manual"
        assert len(summary["steps"]) == 4

    def test_get_discarded_count(self):
        ll = LineageLogger(source="test")
        ll.log_transform(rows_in=100, rows_out=80, rows_discarded=20)
        ll.log_load(rows_in=80, rows_loaded=75, rows_duplicates=5)
        assert ll.get_discarded_count() == 25

    def test_empty_summary_no_crash(self):
        ll = LineageLogger(source="empty")
        summary = ll.summary()
        assert summary["source"] == "empty"
        assert len(summary["steps"]) == 1

    def test_get_loaded_count_no_load(self):
        ll = LineageLogger(source="test")
        ll.log_extract(50)
        assert ll.get_loaded_count() == 0

    def test_get_extracted_count_before_extract(self):
        ll = LineageLogger(source="test")
        assert ll.get_extracted_count() == 0
