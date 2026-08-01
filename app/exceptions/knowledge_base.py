from app.exceptions.base import AIOSException


class KnowledgeBaseNotFound(
    AIOSException,
):
    detail = "Knowledge Base not found."