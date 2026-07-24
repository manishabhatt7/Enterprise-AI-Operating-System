from __future__ import annotations

import asyncio
import logging
import time

from pydantic import ValidationError

from app.exceptions.tool import (
    ToolExecutionException,
    ToolNotFoundException,
    ToolValidationException,
)
from app.tools.registry import tool_registry
from app.tools.retry import is_retryable_exception

logger = logging.getLogger(__name__)


class ToolExecutor:
    """
    Executes registered tools with validation,
    retry logic, logging and timing.
    """

    async def execute(
        self,
        *,
        tool_name: str,
        arguments: dict,
    ) -> dict:

        tool = tool_registry.get(tool_name)

        if tool is None:
            raise ToolNotFoundException(tool_name)

        attempt = 0
        max_retries = (
            tool.max_retries
            if tool.retryable
            else 1
        )
        backoff = tool.initial_backoff

        while attempt < max_retries:

            start = time.perf_counter()

            try:

                logger.info(
                    "Executing tool '%s' (attempt %d/%d)",
                    tool_name,
                    attempt + 1,
                    max_retries,
                )

                # Validate arguments
                validated = tool.input_model.model_validate(
                    arguments,
                )

                # Execute tool
                result = await tool.execute(
                    **validated.model_dump(),
                )

                elapsed = (
                    time.perf_counter()
                    - start
                ) * 1000

                logger.info(
                    "Tool '%s' completed successfully in %.2f ms",
                    tool_name,
                    elapsed,
                )

                return result

            except ValidationError as exc:

                logger.warning(
                    "Validation failed for tool '%s': %s",
                    tool_name,
                    exc,
                )

                raise ToolValidationException(
                    tool_name,
                    str(exc),
                ) from exc

            except Exception as exc:

                elapsed = (
                    time.perf_counter()
                    - start
                ) * 1000

                logger.exception(
                    "Tool '%s' failed after %.2f ms",
                    tool_name,
                    elapsed,
                )

                attempt += 1

                should_retry = (
                    tool.retryable
                    and attempt < max_retries
                    and is_retryable_exception(exc)
                )

                if not should_retry:

                    raise ToolExecutionException(
                        tool_name,
                        str(exc),
                    ) from exc

                logger.info(
                    "Retrying tool '%s' in %.1f seconds "
                    "(attempt %d/%d)...",
                    tool_name,
                    backoff,
                    attempt + 1,
                    max_retries,
                )

                await asyncio.sleep(
                    backoff,
                )

                backoff *= 2


tool_executor = ToolExecutor()