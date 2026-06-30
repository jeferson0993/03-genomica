from __future__ import annotations

import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class DataLakeService:
    def __init__(self) -> None:
        self.base_url = settings.datalake_api_url

    async def register_dataset(
        self,
        name: str,
        source: str,
        layer: str,
        object_path: str,
        metadata: dict[str, object] | None = None,
    ) -> str | None:
        payload = {
            "name": name,
            "source": source,
            "layer": layer,
            "object_path": object_path,
            "metadata": metadata or {},
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/catalog",
                    json=payload,
                    timeout=30,
                )
                response.raise_for_status()
                data = response.json()
                dataset_id = str(data.get("id", "")) if data.get("id") else None
                logger.info(
                    "Registered dataset '%s' in Data Lake catalog: %s",
                    name,
                    dataset_id,
                )
                return dataset_id
            except httpx.HTTPError as exc:
                logger.error(
                    "Failed to register dataset in Data Lake: %s", exc
                )
                return None
