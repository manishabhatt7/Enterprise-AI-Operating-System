from fastapi import status

from app.exceptions.base import AIOSException

class ConversationNotFound(AIOSException):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "Conversation not found."