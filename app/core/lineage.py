import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class LineageLogger:
    def __init__(self, source: str = "unknown"):
        self.source = source
        self.steps: list[dict] = []
        self._start()

    def _start(self):
        self.steps.append({
            "step": "init",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": self.source,
            "rows_in": 0,
            "rows_out": 0,
            "rows_discarded": 0,
            "details": f"Pipeline started from source: {self.source}",
        })

    def log_extract(self, rows_extracted: int, details: str = ""):
        self.steps.append({
            "step": "extract",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "rows_in": 0,
            "rows_out": rows_extracted,
            "rows_discarded": 0,
            "details": details or f"Extracted {rows_extracted} rows",
        })
        logger.info(f"[Lineage] Extract: {rows_extracted} rows - {details}")

    def log_transform(
        self, rows_in: int, rows_out: int, rows_discarded: int = 0, details: str = ""
    ):
        self.steps.append({
            "step": "transform",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "rows_in": rows_in,
            "rows_out": rows_out,
            "rows_discarded": rows_discarded,
            "details": details or f"Transformed {rows_in} -> {rows_out} ({rows_discarded} discarded)",
        })
        logger.info(f"[Lineage] Transform: {rows_in} -> {rows_out} ({rows_discarded} discarded) - {details}")

    def log_load(
        self, rows_in: int, rows_loaded: int, rows_duplicates: int = 0, details: str = ""
    ):
        self.steps.append({
            "step": "load",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "rows_in": rows_in,
            "rows_out": rows_loaded,
            "rows_discarded": rows_duplicates,
            "details": details or f"Loaded {rows_loaded}/{rows_in} rows ({rows_duplicates} duplicates skipped)",
        })
        logger.info(f"[Lineage] Load: {rows_loaded}/{rows_in} loaded ({rows_duplicates} duplicates) - {details}")

    def summary(self) -> dict:
        if not self.steps:
            return {"source": self.source, "steps": [], "total_loaded": 0}

        total_loaded = 0
        for s in self.steps:
            if s["step"] == "load":
                total_loaded = s["rows_out"]

        return {
            "source": self.source,
            "started_at": self.steps[0]["timestamp"],
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "steps": self.steps,
            "total_rows_loaded": total_loaded,
        }

    def get_extracted_count(self) -> int:
        for s in reversed(self.steps):
            if s["step"] == "extract":
                return s["rows_out"]
        return 0

    def get_discarded_count(self) -> int:
        total = 0
        for s in self.steps:
            total += s.get("rows_discarded", 0)
        return total

    def get_loaded_count(self) -> int:
        for s in reversed(self.steps):
            if s["step"] == "load":
                return s["rows_out"]
        return 0
