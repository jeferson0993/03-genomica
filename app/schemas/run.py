from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import PipelineStatus


class PipelineRunCreate(BaseModel):
    name: str
    samplesheet_path: str
    reference: str
    params: dict[str, object] | None = None


class PipelineRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    status: PipelineStatus
    samplesheet_path: str
    reference: str
    params: dict[str, object] | None
    nextflow_run_id: str | None
    output_dir: str | None
    report_path: str | None
    started_at: datetime | None
    completed_at: datetime | None
    duration_seconds: int | None
    error_message: str | None
    datalake_dataset_id: str | None
    created_at: datetime
    updated_at: datetime


class PipelineRunList(BaseModel):
    items: list[PipelineRunResponse]
    total: int
