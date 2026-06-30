from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.reference import ReferenceGenome
from app.schemas.reference import (
    ReferenceGenomeCreate,
    ReferenceGenomeResponse,
)

router = APIRouter(prefix="/references", tags=["references"])


@router.post("", response_model=ReferenceGenomeResponse, status_code=201)
async def create_reference(
    body: ReferenceGenomeCreate,
    session: AsyncSession = Depends(get_session),
) -> ReferenceGenome:
    existing = await session.execute(
        select(ReferenceGenome).where(ReferenceGenome.name == body.name)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=409, detail="Reference with this name already exists"
        )

    ref = ReferenceGenome(**body.model_dump())
    session.add(ref)
    await session.commit()
    await session.refresh(ref)
    return ref


@router.get("")
async def list_references(
    session: AsyncSession = Depends(get_session),
) -> list[ReferenceGenomeResponse]:
    result = await session.execute(
        select(ReferenceGenome).order_by(ReferenceGenome.created_at.desc())
    )
    refs = result.scalars().all()
    return [ReferenceGenomeResponse.model_validate(r) for r in refs]


@router.get("/{ref_id}", response_model=ReferenceGenomeResponse)
async def get_reference(
    ref_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> ReferenceGenome:
    ref = await session.get(ReferenceGenome, ref_id)
    if not ref:
        raise HTTPException(status_code=404, detail="Reference not found")
    return ref
