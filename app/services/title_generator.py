from app.llm import ProviderFactory
from app.models.agents import Agent
from app.models.messages import Message


class TitleGenerator:

    @staticmethod
    async def generate(
        *,
        agent: Agent,
        messages: list[Message],
    ) -> str:

        provider = ProviderFactory.get_provider(
            agent.provider,
        )

        prompt = [
            {
                "role": "system",
                "content": (
                    "Generate a concise conversation title "
                    "using at most 5 words. "
                    "Return ONLY the title."
                ),
            }
        ]

        for message in messages[:4]:
            prompt.append(
                {
                    "role": message.role.value.lower(),
                    "content": message.content,
                }
            )

        title = await provider.chat(
            messages=prompt,
            model=agent.model,
            temperature=0,
        )

        return title.strip().replace('"', "")