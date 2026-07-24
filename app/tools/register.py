from app.tools.implementations import WeatherTool
from app.tools.registry import tool_registry


def register_tools() -> None:
    """
    Register all built-in tools.
    """

    tool_registry.register(
        WeatherTool(),
    )
