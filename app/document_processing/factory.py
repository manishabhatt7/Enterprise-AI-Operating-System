from app.document_processing.parsers.document_parsers.pdf import PDFParser
from app.document_processing.stages.parser import ParserStage
from app.document_processing.pipeline import DocumentProcessingPipeline
from app.document_processing.section_builders.markdown import MarkdownSectionBuilder
from app.document_processing.stages.section_builder import SectionBuilderStage
from app.document_processing.chunkers.recursive import RecursiveChunker
from app.document_processing.stages.chunker import ChunkingStage
from app.document_processing.embedders.ollama import OllamaEmbedder 
from app.document_processing.stages.embedding import EmbeddingStage
from app.document_processing.indexers.qdrant import QdrantIndexer 
from app.document_processing.stages.indexing import IndexingStage


def get_processing_pipeline() -> DocumentProcessingPipeline:
    
    return DocumentProcessingPipeline(
        stages=[
            ParserStage(
                parser=PDFParser(),
            ),
            SectionBuilderStage(
                MarkdownSectionBuilder(),
            ),
            ChunkingStage(
                RecursiveChunker(),
            ),
            EmbeddingStage(
                OllamaEmbedder(),
            ),
            IndexingStage(
                QdrantIndexer(),
            ),
        ]
    )