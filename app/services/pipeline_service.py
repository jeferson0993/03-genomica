from __future__ import annotations

import json
import logging
import subprocess
import uuid

from fastapi import HTTPException
from sqlalchemy import func, select

from app.config import settings
from app.database import async_session
from app.models.enums import PipelineStatus
from app.models.run import PipelineRun

logger = logging.getLogger(__name__)


class PipelineService:
    def __init__(self) -> None:
        self.worker_container = settings.genomics_worker_container
        self.pipeline_dir = settings.genomics_pipeline_dir
        self.workspace = settings.genomics_workspace
        self.max_concurrent = settings.max_concurrent_runs
        self.default_profile = settings.genomics_default_profile

    async def _count_active_runs(self) -> int:
        async with async_session() as session:
            query = select(func.count(PipelineRun.id)).where(
                PipelineRun.status.in_([
                    PipelineStatus.pending,
                    PipelineStatus.queued,
                    PipelineStatus.running,
                ])
            )
            result = await session.execute(query)
            return result.scalar() or 0

    async def dispatch(
        self,
        run_id: uuid.UUID,
        samplesheet_path: str,
        reference: str,
        params: dict[str, object] | None = None,
    ) -> str:
        active = await self._count_active_runs()
        if active >= self.max_concurrent:
            raise HTTPException(
                status_code=429,
                detail=(
                    f"Limite de {self.max_concurrent} execuções simultâneas "
                    f"atingido ({active} ativas). Aguarde uma execução concluir."
                ),
            )

        params_file = f"{self.workspace}/params_{run_id}.json"
        params_data = {
            "samplesheet": samplesheet_path,
            "reference": reference,
            "outdir": f"{self.workspace}/results_{run_id}",
            "run_id": str(run_id),
            **(params or {}),
        }

        with open(params_file, "w") as f:
            json.dump(params_data, f)

        cmd = [
            "docker",
            "exec",
            self.worker_container,
            "nextflow",
            "run",
            f"{self.pipeline_dir}/main.nf",
            "-params-file",
            params_file,
            "-profile",
            self.default_profile,
            "-w",
            f"{self.workspace}/work_{run_id}",
        ]

        logger.info("Dispatching Nextflow: %s", " ".join(cmd))
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        return str(proc.pid)

    async def cancel(self, nextflow_run_id: str) -> None:
        cmd = [
            "docker",
            "exec",
            self.worker_container,
            "nextflow",
            "cancel",
            nextflow_run_id,
        ]
        subprocess.run(cmd, capture_output=True, text=True)
        logger.info("Cancelled Nextflow run: %s", nextflow_run_id)
