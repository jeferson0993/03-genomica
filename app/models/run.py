from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base
from app.models.enums import PipelineStatus


class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str]
    status: Mapped[PipelineStatus] = mapped_column(
        default=PipelineStatus.pending
    )
    samplesheet_path: Mapped[str]
    reference: Mapped[str]
    params: Mapped[dict[str, object] | None] = mapped_column(JSON, nullable=True, default=dict)
    nextflow_run_id: Mapped[str | None] = mapped_column(nullable=True)
    output_dir: Mapped[str | None] = mapped_column(nullable=True)
    report_path: Mapped[str | None] = mapped_column(nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    datalake_dataset_id: Mapped[str | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )
