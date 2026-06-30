from __future__ import annotations

import logging
import re
import subprocess

logger = logging.getLogger(__name__)


class MonitorService:
    def __init__(self, worker_container: str = "03-genomica-worker-1") -> None:
        self.worker_container = worker_container

    async def poll_logs(self, run_id: str, tail: int = 100) -> str:
        _ = run_id  # used for per-run log isolation
        cmd = [
            "docker",
            "exec",
            self.worker_container,
            "cat",
            "/workspace/.nextflow.log",
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                return "\n".join(lines[-tail:])
            return f"Logs not available: {result.stderr}"
        except subprocess.TimeoutExpired:
            return "Timeout reading logs"

    async def check_status_from_logs(self, run_id: str) -> str | None:
        logs = await self.poll_logs(run_id, tail=50)
        if "Pipeline execution completed" in logs:
            return "completed"
        if "ERROR" in logs or "Error" in logs:
            return "failed"
        if "Submitted process" in logs:
            return "running"
        return None

    async def get_error_message(self, run_id: str) -> str | None:
        logs = await self.poll_logs(run_id, tail=200)
        match = re.search(r"ERROR\s*~(.+?)(?:\n|$)", logs, re.DOTALL)
        if match:
            return match.group(1).strip()
        return None

    async def read_report(self, run_id: str, report_name: str = "report.html") -> str | None:
        report_path = f"/workspace/results_{run_id}/r-report/{report_name}"
        cmd = [
            "docker",
            "exec",
            self.worker_container,
            "cat",
            report_path,
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                return result.stdout
            logger.warning("Report not found for run %s: %s", run_id, result.stderr)
            return None
        except subprocess.TimeoutExpired:
            logger.warning("Timeout reading report for run %s", run_id)
            return None
