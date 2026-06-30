from __future__ import annotations

from app.models.enums import PipelineStatus


class TestPipelineStatus:
    def test_values(self) -> None:
        assert PipelineStatus.pending == "pending"
        assert PipelineStatus.queued == "queued"
        assert PipelineStatus.running == "running"
        assert PipelineStatus.completed == "completed"
        assert PipelineStatus.failed == "failed"
        assert PipelineStatus.cancelled == "cancelled"
