class AIOSException(Exception):
    """Base exception for AIOS."""

    status_code = 500
    detail = "Internal Server Error"

    def __init__(self, detail: str | None = None):
        if detail:
            self.detail = detail