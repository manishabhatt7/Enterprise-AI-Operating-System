from app.schemas.organization import OrganizationCreate


def test_organization_schema_examples_are_strings():
    schema = OrganizationCreate.model_json_schema()

    assert schema["properties"]["name"]["example"] == "AIOS"
    assert (
        schema["properties"]["description"]["example"]
        == "AI-powered enterprise platform"
    )
