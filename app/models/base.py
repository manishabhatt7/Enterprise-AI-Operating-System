from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDMixin


class BaseModel(
    Base,
    UUIDMixin,
    TimestampMixin,
):
    """
    Base model inherited by all database models.
    """

    __abstract__ = True