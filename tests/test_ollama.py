import asyncio
from langchain_ollama import ChatOllama
from app.core.config import settings


async def main():
    llm = ChatOllama(
        model="qwen2.5:1.5b",
        base_url="http://localhost:11434",
        temperature=0.2,
    )

    response = await llm.ainvoke("Hello!")
    logger.info(response.content)


asyncio.run(main())
