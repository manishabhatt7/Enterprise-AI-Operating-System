from __future__ import annotations

from abc import ABC, abstractmethod

from app.models.documents import Document
from app.uow.unit_of_work import UnitOfWork

from app.document_processing.context import ProcessingContext


class ProcessingStage(ABC):
    """
    Base class for every document processing stage.
    """

    @abstractmethod
    async def run(
        self,
        *,
        uow: UnitOfWork,
        context: ProcessingContext,
    ) -> None:
        """
        Execute the processing stage.

        The context dictionary is shared across
        every stage in the pipeline.
        """
        raise NotImplementedError