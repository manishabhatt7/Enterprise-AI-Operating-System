from typing import Any

from fastapi.responses import JSONResponse


class APIResponse:
    @staticmethod
    def success(
        *,
        data: Any = None,
        message: str = "Success",
        status_code: int = 200,
    ) -> JSONResponse:

        return JSONResponse(
            status_code=status_code,
            content={
                "success": True,
                "message": message,
                "data": data,
            },
        )