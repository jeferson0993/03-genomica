"""create tables

Revision ID: 0001
Revises:
Create Date: 2026-06-12

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
import sqlalchemy as sa

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "pipeline_runs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("samplesheet_path", sa.String(), nullable=False),
        sa.Column("reference", sa.String(), nullable=False),
        sa.Column("params", sa.JSON, nullable=True),
        sa.Column("nextflow_run_id", sa.String(), nullable=True),
        sa.Column("output_dir", sa.String(), nullable=True),
        sa.Column("report_path", sa.String(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("datalake_dataset_id", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "reference_genomes",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(), unique=True, nullable=False),
        sa.Column("species", sa.String(), nullable=False, server_default="Homo sapiens"),
        sa.Column("fasta_path", sa.String(), nullable=False),
        sa.Column("bwa_index_prefix", sa.String(), nullable=True),
        sa.Column("dbsnp_path", sa.String(), nullable=True),
        sa.Column("known_indels_path", sa.String(), nullable=True),
        sa.Column("gtf_path", sa.String(), nullable=True),
        sa.Column("minio_prefix", sa.String(), nullable=True),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("reference_genomes")
    op.drop_table("pipeline_runs")
