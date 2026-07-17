from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.exceptions.base import AIOSException


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AIOSException)
    async def handle_aios_exception(
        request: Request,
        exc: AIOSException,
    ):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "type": exc.__class__.__name__,
                    "message": exc.detail,
                },
            },
        )