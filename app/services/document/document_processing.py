# class DocumentProcessingService:

#     def __init__(
#         self,
#         uow: UnitOfWork,
#         pipeline: DocumentProcessingPipeline,
#     ):
#         self.uow = uow
#         self.pipeline = pipeline

#     async def process(
#         self,
#         document: Document,
#     ) -> None:

#         await self.pipeline.run(
#             document=document,
#             uow=self.uow,
#         )