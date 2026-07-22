from app.models.agents import Agent
from app.models.messages import Message


class PromptBuilder:

    @staticmethod
    def build(
        *,
        agent: Agent,
        messages: list[Message],
    ) -> list[dict]:

        prompt = [
            {
                "role": "system",
                "content": agent.system_prompt,
            }
        ]

        for message in messages:
            prompt.append(
                {
                    "role": message.role.value.lower(),
                    "content": message.content,
                }
            )

        return prompt