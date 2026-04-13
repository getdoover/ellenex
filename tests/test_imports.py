"""
Basic tests to ensure all modules are importable.
"""


def test_import_integration():
    from integration.application import TtsIntegration
    assert TtsIntegration
    assert TtsIntegration.config_cls is not None


def test_import_processor():
    from processor.application import TtsProcessor
    assert TtsProcessor
    assert TtsProcessor.config_cls is not None
    assert TtsProcessor.tags_cls is not None
    assert TtsProcessor.ui_cls is not None


def test_integration_config():
    from integration.app_config import TtsIntegrationConfig
    schema = TtsIntegrationConfig.to_schema()
    assert isinstance(schema, dict)


def test_processor_config():
    from processor.app_config import TtsProcessorConfig
    schema = TtsProcessorConfig.to_schema()
    assert isinstance(schema, dict)


def test_processor_tags():
    from processor.app_tags import TtsTags
    assert TtsTags


def test_processor_ui():
    from processor.app_ui import TtsUI
    assert TtsUI
