# app/storage/factory.py

from app.core.config import settings
from app.storage.base import BaseStorage
from app.storage.local import LocalStorage
# from app.storage.s3 import S3Storage

def get_storage() -> BaseStorage:
    if settings.STORAGE_PROVIDER == "local":
        return LocalStorage()

    # elif settings.STORAGE_PROVIDER == "s3":
    #     return S3Storage()

    raise ValueError("Unknown storage provider")