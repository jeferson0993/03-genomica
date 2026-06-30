from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_session
from app.models.enums import PipelineStatus
from app.models.run import PipelineRun
from app.schemas.run import PipelineRunCreate, PipelineRunList, PipelineRunResponse
from app.services.monitor_service import MonitorService
from app.services.pipeline_service import PipelineService

router = APIRouter(prefix="/runs", tags=["runs"])


@router.post("", response_model=PipelineRunResponse, status_code=201)
async def create_run(
    body: PipelineRunCreate,
    session: AsyncSession = Depends(get_session),
) -> PipelineRun:
    active_count: int = await session.scalar(
        select(func.count(PipelineRun.id)).where(
            PipelineRun.status.in_([
                PipelineStatus.pending,
                PipelineStatus.queued,
                PipelineStatus.running,
            ])
        )
    ) or 0

    if active_count >= settings.max_concurrent_runs:
        raise HTTPException(
            status_code=429,
            detail=(
                f"Limite de {settings.max_concurrent_runs} execuções simultâneas "
                f"atingido ({active_count} ativas). Aguarde uma execução concluir."
            ),
        )

    run = PipelineRun(
        name=body.name,
        status=PipelineStatus.pending,
        samplesheet_path=body.samplesheet_path,
        reference=body.reference,
        params=body.params or {},
    )
    session.add(run)
    await session.commit()
    await session.refresh(run)

    pipeline = PipelineService()
    pid = await pipeline.dispatch(
        run_id=run.id,
        samplesheet_path=run.samplesheet_path,
        reference=run.reference,
        params=run.params,
    )
    run.nextflow_run_id = pid
    run.status = PipelineStatus.queued
    await session.commit()
    await session.refresh(run)

    return run


@router.get("", response_model=PipelineRunList)
async def list_runs(
    status: PipelineStatus | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> PipelineRunList:
    query = select(PipelineRun)
    count_query = select(func.count(PipelineRun.id))

    if status:
        query = query.where(PipelineRun.status == status)
        count_query = count_query.where(PipelineRun.status == status)

    query = query.order_by(PipelineRun.created_at.desc())
    query = query.offset(offset).limit(limit)

    result = await session.execute(query)
    items = result.scalars().all()

    total_result = await session.execute(count_query)
    total = total_result.scalar() or 0

    return PipelineRunList(
        items=[PipelineRunResponse.model_validate(r) for r in items],
        total=total,
    )


@router.get("/{run_id}", response_model=PipelineRunResponse)
async def get_run(
    run_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> PipelineRun:
    run = await session.get(PipelineRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@router.get("/{run_id}/logs")
async def get_run_logs(
    run_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    run = await session.get(PipelineRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    monitor = MonitorService()
    logs = await monitor.poll_logs(str(run_id))
    return {"run_id": str(run_id), "logs": logs}


@router.get("/{run_id}/report")
async def get_run_report(
    run_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> dict[str, str | None]:
    run = await session.get(PipelineRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    if not run.report_path:
        raise HTTPException(status_code=404, detail="Report not available yet")
    return {"run_id": str(run_id), "report_path": run.report_path}


@router.get("/{run_id}/r-report", response_class=HTMLResponse)
async def get_run_r_report(
    run_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> str:
    run = await session.get(PipelineRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    monitor = MonitorService()
    html = await monitor.read_report(str(run_id))
    if html is None:
        raise HTTPException(
            status_code=404,
            detail="R report not available yet or run not found",
        )
    return html


@router.post("/{run_id}/cancel", response_model=PipelineRunResponse)
async def cancel_run(
    run_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> PipelineRun:
    run = await session.get(PipelineRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    if run.status not in (PipelineStatus.pending, PipelineStatus.queued, PipelineStatus.running):
        raise HTTPException(status_code=400, detail="Run cannot be cancelled in current status")

    if run.nextflow_run_id:
        pipeline = PipelineService()
        await pipeline.cancel(run.nextflow_run_id)

    run.status = PipelineStatus.cancelled
    run.completed_at = datetime.now(UTC)
    await session.commit()
    await session.refresh(run)
    return run
