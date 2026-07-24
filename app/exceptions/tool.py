from __future__ import annotations


class ToolException(Exception):
    """Base exception for all tool-related errors."""


class ToolNotFoundException(ToolException):

    def __init__(self, tool_name: str):
        super().__init__(
            f"Tool '{tool_name}' is not registered."
        )


class ToolExecutionException(ToolException):

    def __init__(
        self,
        tool_name: str,
        reason: str,
    ):
        super().__init__(
            f"Failed to execute tool '{tool_name}': {reason}"
        )


class ToolExecutionLimitExceeded(ToolException):

    def __init__(self):
        super().__init__(
            "Maximum number of tool iterations exceeded."
        )

class ToolValidationException(ToolException):

    def __init__(
        self,
        tool_name: str,
        reason: str,
    ):
        super().__init__(
            f"Invalid arguments for tool '{tool_name}': {reason}"
        )