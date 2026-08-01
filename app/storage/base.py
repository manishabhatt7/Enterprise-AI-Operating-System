from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from fastapi import UploadFile


class BaseStorage(ABC):
    """
    Base interface for all storage providers.
    """

    @abstractmethod
    async def save(
        self,
        *,
        file: UploadFile,
        organization_id: UUID,
        knowledge_base_id: UUID,
        document_id: UUID,
    ) -> str:
        """
        Save a file.

        Returns:
            Storage path.
        """
        raise NotImplementedError

    @abstractmethod
    async def delete(
        self,
        *,
        storage_path: str,
    ) -> None:
        """
        Delete a file.
        """
        raise NotImplementedError

    @abstractmethod
    async def exists(
        self,
        *,
        storage_path: str,
    ) -> bool:
        """
        Check whether a file exists.
        """
        raise NotImplementedError