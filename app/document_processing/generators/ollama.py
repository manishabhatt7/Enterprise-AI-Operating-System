from app.core.config import settings
from app.document_processing.models.chat_model import get_llm


class OllamaGenerator:

    async def generate(
        self,
        prompt: str,
    ) -> str:

        llm = get_llm()
        
        response = await llm.ainvoke(prompt)

        return response.content