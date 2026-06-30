from __future__ import annotations

import pytest
from httpx import AsyncClient


class TestReferencesAPI:
    @pytest.mark.asyncio
    async def test_create_reference(self, client: AsyncClient) -> None:
        payload = {
            "name": "grch38",
            "fasta_path": "/ref/grch38/GRCh38.fa",
            "is_default": True,
        }
        response = await client.post("/references", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "grch38"
        assert data["is_default"] is True

    @pytest.mark.asyncio
    async def test_create_duplicate_reference(self, client: AsyncClient) -> None:
        payload = {
            "name": "grch38",
            "fasta_path": "/ref/grch38/GRCh38.fa",
        }
        await client.post("/references", json=payload)
        response = await client.post("/references", json=payload)
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_list_references(self, client: AsyncClient) -> None:
        response = await client.get("/references")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_reference(self, client: AsyncClient) -> None:
        payload = {
            "name": "grch37",
            "fasta_path": "/ref/grch37/GRCh37.fa",
        }
        create_resp = await client.post("/references", json=payload)
        ref_id = create_resp.json()["id"]

        response = await client.get(f"/references/{ref_id}")
        assert response.status_code == 200
        assert response.json()["name"] == "grch37"

    @pytest.mark.asyncio
    async def test_get_reference_not_found(self, client: AsyncClient) -> None:
        response = await client.get("/references/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404
