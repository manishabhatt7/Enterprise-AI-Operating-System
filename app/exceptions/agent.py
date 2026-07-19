from fastapi import status

from app.exceptions.base import AIOSException

class ConflictException(AIOSException):
    status_code = status.HTTP_409_CONFLICT
    detail = "Agent with this name already exists."

class NotFoundException(AIOSException):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "Agent not found."