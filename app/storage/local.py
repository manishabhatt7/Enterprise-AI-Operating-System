from __future__ import annotations

import os
import shutil
from pathlib import Path
from uuid import UUID

from fastapi import UploadFile
from app.core.config import settings

from app.storage.base import BaseStorage


class LocalStorage(BaseStorage):
    """
    Local filesystem storage.
    """

    ROOT = Path(settings.STORAGE_ROOT)

    async def save(
        self,
        *,
        file: UploadFile,
        organization_id: UUID,
        knowledge_base_id: UUID,
        document_id: UUID,
    ) -> str:

        directory = (
            self.ROOT
            / str(organization_id)
            / str(knowledge_base_id)
        )

        directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        extension = Path(file.filename).suffix

        filepath = (
            directory
            / f"{document_id}{extension}"
        )

        with filepath.open("wb") as buffer:
            shutil.copyfileobj(
                file.file,
                buffer,
            )

        return str(filepath)

    async def delete(
        self,
        *,
        storage_path: str,
    ) -> None:

        path = Path(storage_path)

        if path.exists():
            path.unlink()

    async def exists(
        self,
        *,
        storage_path: str,
    ) -> bool:

        return Path(storage_path).exists()