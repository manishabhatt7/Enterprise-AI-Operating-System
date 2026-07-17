from app.cache import redis as redis_module


def test_build_redis_client_uses_resp2_protocol():
    client = redis_module.build_redis_client()

    assert client.connection_pool.connection_kwargs["protocol"] == 2
