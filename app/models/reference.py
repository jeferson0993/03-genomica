from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


class ReferenceGenome(Base):
    __tablename__ = "reference_genomes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(unique=True)
    species: Mapped[str] = mapped_column(default="Homo sapiens")
    fasta_path: Mapped[str]
    bwa_index_prefix: Mapped[str | None] = mapped_column(nullable=True)
    dbsnp_path: Mapped[str | None] = mapped_column(nullable=True)
    known_indels_path: Mapped[str | None] = mapped_column(nullable=True)
    gtf_path: Mapped[str | None] = mapped_column(nullable=True)
    minio_prefix: Mapped[str | None] = mapped_column(nullable=True)
    is_default: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
