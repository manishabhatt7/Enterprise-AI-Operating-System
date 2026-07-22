from app.models.agents import Agent


def test_agent_model_imports_with_provider_enum():
    assert Agent.__tablename__ == "agents"
