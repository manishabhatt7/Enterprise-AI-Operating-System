from pydantic import BaseModel, Field

from app.clients.open_meteo import open_meteo_client
from app.tools.base import BaseTool
from app.schemas.tool import ToolResult


class WeatherInput(BaseModel):
    city: str = Field(
        description="City name to retrieve the weather for.",
    )


class WeatherTool(BaseTool):

    retryable = True

    @property
    def name(self) -> str:
        return "get_weather"

    @property
    def description(self) -> str:
        return "Get the current weather for a given city."

    @property
    def input_model(self) -> type[BaseModel]:
        return WeatherInput

    async def execute(
        self,
        *,
        city: str,
    ) -> ToolResult:
        """
        Execute the weather tool.
        """

        weather = await open_meteo_client.get_weather(
            city,
        )

        return ToolResult(
            success=True,
            data=weather,
        )