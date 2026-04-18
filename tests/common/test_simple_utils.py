import os
import logging
from unittest.mock import patch
import pytest


from common.logger import setup_logger
from common.utils import load_prompt


import sys
from importlib import reload


# Config Tests
def test_settings_defaults():
    # Force reload of settings to avoid cached values
    with patch.dict(os.environ, {}, clear=True):
        if "common.config" in sys.modules:
            reload(sys.modules["common.config"])

        from common.config import get_settings

        get_settings.cache_clear()

        settings = get_settings()
        assert settings.APP_NAME == "tegmen"
        assert settings.DEFAULT_MODEL == "openrouter/google/gemini-2.0-flash-001"
        assert settings.DEBUG is False


def test_settings_override():
    with patch.dict(os.environ, {"DEBUG": "true", "APP_NAME": "test_app"}):
        if "common.config" in sys.modules:
            reload(sys.modules["common.config"])

        from common.config import get_settings

        get_settings.cache_clear()

        settings = get_settings()
        assert settings.DEBUG is True
        # APP_NAME is hardcoded in class, check if it's overridable or if env var is ignored
        # Looking at config.py: APP_NAME: str = "tegmen" -> it is hardcoded, not from env
        assert settings.APP_NAME == "tegmen"


# Logger Tests
def test_setup_logger():
    logger_name = "test_logger"
    logger = setup_logger(logger_name)

    assert logger.name == logger_name
    assert logger.level == logging.INFO
    assert len(logger.handlers) > 0
    assert isinstance(logger.handlers[0], logging.StreamHandler)

    # Test idempotency (calling twice doesn't add duplicate handlers)
    logger2 = setup_logger(logger_name)
    assert len(logger2.handlers) == 1


# Utils Tests (load_prompt)
def test_load_prompt_success(tmp_path):
    # Create a dummy prompt file
    # load_prompt expects file relative to project root
    # accessing via absolute path should work if it invokes jinja correctly

    # We need to mock how load_prompt calculates paths or create a fake project root structure
    # load_prompt logic:
    # current_dir = .../src/common
    # project_root = .../
    # env = FileSystemLoader(project_root)
    # template_path = relpath(file_path, project_root)

    # To test this without relying on actual file system layout too much,
    # we can create a file in a temporary directory and patch os.path.abspath/join?
    # Or just create a file that is reachable.

    # Simpler: Test exception for non-existent file
    with pytest.raises(FileNotFoundError):
        load_prompt("/non/existent/path.md")

    # For success, we can try to load a known file, e.g., README.md if it was a prompt?
    # Or mock Environment.get_template

    with patch("common.utils.Environment") as MockEnv:
        mock_env_instance = MockEnv.return_value
        mock_template = mock_env_instance.get_template.return_value
        mock_template.render.return_value = "Rendered Prompt"

        # We also need os.path.exists to return True
        with patch("os.path.exists", return_value=True):
            result = load_prompt("/path/to/prompt.md")
            assert result == "Rendered Prompt"
            # Verify get_template was called
            mock_env_instance.get_template.assert_called()
