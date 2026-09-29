from pydantic import BaseModel


class QueryRequest(BaseModel):
    query: str
    knowledge_base_id: str

class SourceChunk(BaseModel):
    text: str
    page_numbers: list[int]


class QueryResponse(BaseModel):
    context: str
    sources: list[SourceChunk]