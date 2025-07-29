"""SQLite-backed experiment store."""

import json
import logging
import sqlite3

from servesmith.models.experiment import Experiment, ExperimentRequest, ExperimentStatus

logger = logging.getLogger(__name__)


class ExperimentStore:
    """Persist experiments to SQLite."""

    def __init__(self, db_path: str = "servesmith.db") -> None:
        self.db = sqlite3.connect(db_path, check_same_thread=False)
        self._create_tables()

    def _create_tables(self) -> None:
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS experiments (
                experiment_id TEXT PRIMARY KEY,
                request_json TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL
            )
        """)
        self.db.commit()

    def save(self, exp: Experiment) -> None:
        self.db.execute(
            "INSERT OR REPLACE INTO experiments (experiment_id, request_json, status, created_at) VALUES (?, ?, ?, ?)",
            (exp.experiment_id, exp.request.model_dump_json(), exp.status.value, exp.created_at.isoformat()),
        )
        self.db.commit()

    def get(self, experiment_id: str) -> Experiment | None:
        row = self.db.execute(
            "SELECT experiment_id, request_json, status, created_at FROM experiments WHERE experiment_id = ?",
            (experiment_id,),
        ).fetchone()
        if not row:
            return None
        return Experiment(
            experiment_id=row[0],
            request=ExperimentRequest.model_validate_json(row[1]),
            status=ExperimentStatus(row[2]),
        )

    def update_status(self, experiment_id: str, status: ExperimentStatus) -> None:
        self.db.execute(
            "UPDATE experiments SET status = ? WHERE experiment_id = ?",
            (status.value, experiment_id),
        )
        self.db.commit()
