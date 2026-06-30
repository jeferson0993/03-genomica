from __future__ import annotations

from app.services.datalake_service import DataLakeService
from app.services.minio_service import MinioService
from app.services.monitor_service import MonitorService
from app.services.pipeline_service import PipelineService


class TestPipelineService:
    def test_init(self) -> None:
        svc = PipelineService()
        assert svc.worker_container == "03-genomica-worker-1"


class TestMinioService:
    def test_init(self) -> None:
        svc = MinioService()
        assert svc.client is not None


class TestDataLakeService:
    def test_init(self) -> None:
        svc = DataLakeService()
        assert svc.base_url == "http://api-data-lake:8000"


class TestMonitorService:
    def test_init(self) -> None:
        svc = MonitorService()
        assert svc.worker_container == "03-genomica-worker-1"
