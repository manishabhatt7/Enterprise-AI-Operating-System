from enum import Enum

class DocumentStatus(str, Enum):
    """
    Current indexing status of a document.
    """

    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    READY = "READY"
    FAILED = "FAILED"