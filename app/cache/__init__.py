from app.cache.session_store import RedisSessionStore

session_store = RedisSessionStore()

__all__ = [
    "session_store",
]