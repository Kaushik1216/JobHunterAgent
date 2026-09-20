from __future__ import annotations

import threading
from datetime import datetime, timezone
from typing import Any

from job_agent.config import Settings
from job_agent.core.runner import AgentRunner
from job_agent.models.enums import RunMode
from job_agent.models.schemas import SearchTarget


class RunInProgressError(RuntimeError):
    pass


class RunManager:
    """Single-flight background runner for dashboard-triggered pipeline jobs."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._lock = threading.Lock()
        self._state: dict[str, Any] = self._idle_state()

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return dict(self._state)

    def start(self, mode: RunMode, targets: list[SearchTarget] | None = None) -> dict[str, Any]:
        with self._lock:
            if self._state.get("status") == "running":
                raise RunInProgressError("A pipeline run is already in progress")
            self._state = {
                "status": "running",
                "mode": mode.value,
                "message": _mode_message(mode),
                "error": None,
                "summary": None,
                "started_at": datetime.now(timezone.utc).isoformat(),
                "completed_at": None,
            }
            thread = threading.Thread(
                target=self._execute,
                args=(mode, targets),
                daemon=True,
                name=f"job-agent-run-{mode.value}",
            )
            thread.start()
            return dict(self._state)

    def _execute(self, mode: RunMode, targets: list[SearchTarget] | None) -> None:
        try:
            from job_agent.config import get_settings
            runner = AgentRunner(get_settings())
            summary = runner.run(mode=mode, targets=targets)
            data = summary.model_dump(mode="json")
            data["duration_seconds"] = summary.duration_seconds
            has_errors = bool(summary.search_errors)
            with self._lock:
                self._state = {
                    "status": "failed" if has_errors and summary.jobs_discovered == 0 and summary.jobs_found == 0 else "completed",
                    "mode": mode.value,
                    "message": f"{len(summary.search_errors)} search error(s) — check portal connectivity" if has_errors else "Run finished",
                    "error": "\n".join(summary.search_errors) if has_errors else None,
                    "summary": data,
                    "started_at": self._state.get("started_at"),
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                }
        except Exception as exc:
            with self._lock:
                self._state = {
                    "status": "failed",
                    "mode": mode.value,
                    "message": "Run failed",
                    "error": str(exc),
                    "summary": None,
                    "started_at": self._state.get("started_at"),
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                }

    @staticmethod
    def _idle_state() -> dict[str, Any]:
        return {
            "status": "idle",
            "mode": None,
            "message": "No run in progress",
            "error": None,
            "summary": None,
            "started_at": None,
            "completed_at": None,
        }


def _mode_message(mode: RunMode) -> str:
    if mode == RunMode.SEARCH:
        return "Searching portals…"
    if mode == RunMode.MATCH:
        return "Matching discovered jobs…"
    return "Searching and matching…"
