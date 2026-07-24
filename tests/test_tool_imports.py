import importlib


def test_tool_package_imports_without_circular_error() -> None:
    module = importlib.import_module("app.tools")
    assert module.tool_registry is not None
    assert module.tool_executor is not None
