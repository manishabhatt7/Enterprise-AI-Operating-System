from fastapi import status

from app.exceptions.base import AIOSException


class InvalidCredentials(AIOSException):
    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "Invalid email or password."


class InvalidToken(AIOSException):
    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "Invalid or expired token."


class UserAlreadyExists(AIOSException):
    status_code = status.HTTP_409_CONFLICT
    detail = "User already exists."


class Forbidden(AIOSException):
    status_code = status.HTTP_403_FORBIDDEN
    detail = "Permission denied."