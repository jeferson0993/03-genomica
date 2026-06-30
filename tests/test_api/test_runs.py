from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient


class TestRunsAPI:
    @pytest.mark.asyncio
    async def test_create_run(self, client: AsyncClient) -> None:
        patch_dispatch = patch(
            "app.api.runs.PipelineService.dispatch",
            new=AsyncMock(return_value="12345"),
        )
        patch_count = patch(
            "app.api.runs.PipelineService._count_active_runs",
            new=AsyncMock(return_value=0),
        )
        patch_dispatch.start()
        patch_count.start()
        try:
            payload = {
                "name": "test-run",
                "samplesheet_path": "raw://samplesheets/test.csv",
                "reference": "grch38",
            }
            response = await client.post("/runs", json=payload)
            assert response.status_code == 201
            data = response.json()
            assert data["name"] == "test-run"
            assert data["status"] == "queued"
        finally:
            patch_dispatch.stop()
            patch_count.stop()

    @pytest.mark.asyncio
    async def test_list_runs(self, client: AsyncClient) -> None:
        response = await client.get("/runs")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_list_runs_with_filter(self, client: AsyncClient) -> None:
        response = await client.get("/runs?status=completed")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_run_not_found(self, client: AsyncClient) -> None:
        response = await client.get("/runs/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_cancel_nonexistent_run(self, client: AsyncClient) -> None:
        response = await client.post(
            "/runs/00000000-0000-0000-0000-000000000000/cancel"
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_run_logs_not_found(self, client: AsyncClient) -> None:
        response = await client.get("/runs/00000000-0000-0000-0000-000000000000/logs")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_run_report_not_found(self, client: AsyncClient) -> None:
        patch_dispatch = patch(
            "app.api.runs.PipelineService.dispatch",
            new=AsyncMock(return_value="12345"),
        )
        patch_count = patch(
            "app.api.runs.PipelineService._count_active_runs",
            new=AsyncMock(return_value=0),
        )
        patch_dispatch.start()
        patch_count.start()
        try:
            payload = {
                "name": "report-test",
                "samplesheet_path": "raw://test.csv",
                "reference": "grch38",
            }
            create_resp = await client.post("/runs", json=payload)
            run_id = create_resp.json()["id"]

            response = await client.get(f"/runs/{run_id}/report")
            assert response.status_code == 404
        finally:
            patch_dispatch.stop()
            patch_count.stop()
