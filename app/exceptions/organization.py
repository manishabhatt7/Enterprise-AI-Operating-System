from fastapi import status

from app.exceptions.base import AIOSException


class OrganizationAlreadyExists(AIOSException):
    status_code = status.HTTP_409_CONFLICT
    detail = "Organization already exists."


class OrganizationNotFound(AIOSException):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "Organization not found."