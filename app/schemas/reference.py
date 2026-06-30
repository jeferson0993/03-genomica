from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ReferenceGenomeCreate(BaseModel):
    name: str
    species: str = "Homo sapiens"
    fasta_path: str
    bwa_index_prefix: str | None = None
    dbsnp_path: str | None = None
    known_indels_path: str | None = None
    gtf_path: str | None = None
    minio_prefix: str | None = None
    is_default: bool = False


class ReferenceGenomeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    species: str
    fasta_path: str
    bwa_index_prefix: str | None
    dbsnp_path: str | None
    known_indels_path: str | None
    gtf_path: str | None
    minio_prefix: str | None
    is_default: bool
    created_at: datetime
