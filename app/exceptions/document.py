from app.exceptions.base import AIOSException

class DocumentNotFoundException(AIOSException):
    detail = "Document not found."

class UnsupportedDocumentTypeException(AIOSException):
    detail = "Only PDF documents are supported."

class DocumentTooLargeException(AIOSException):
    detail = "Document exceeds the maximum allowed size."