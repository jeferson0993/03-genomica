from __future__ import annotations

import enum


class PipelineStatus(enum.StrEnum):
    pending = "pending"
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"
