import pytest
from unittest.mock import patch, Mock
import requests

from ollama.client import (
    chat,
    chat_stream,
    health_check,
    OllamaConnectionError,
    _base_url,
)


class TestBaseUrl:
    """Tests for _base_url helper."""

    def test_default_url(self):
        with patch.dict("os.environ", {}, clear=True):
            assert _base_url() == "http://localhost:11434"

    def test_custom_url_from_env(self):
        with patch.dict("os.environ", {"OLLAMA_URL": "http://custom:8080"}):
            assert _base_url() == "http://custom:8080"

    def test_trailing_slash_stripped(self):
        with patch.dict("os.environ", {"OLLAMA_URL": "http://custom:8080/"}):
            assert _base_url() == "http://custom:8080"


class TestHealthCheck:
    """Tests for health_check function."""

    @patch("ollama.client.requests.get")
    def test_healthy_server_returns_true(self, mock_get):
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.raise_for_status = Mock()
        
        assert health_check() is True
        mock_get.assert_called_once()

    @patch("ollama.client.requests.get")
    def test_connection_error_raises(self, mock_get):
        mock_get.side_effect = requests.exceptions.ConnectionError()
        
        with pytest.raises(OllamaConnectionError, match="Cannot connect"):
            health_check()

    @patch("ollama.client.requests.get")
    def test_timeout_raises(self, mock_get):
        mock_get.side_effect = requests.exceptions.Timeout()
        
        with pytest.raises(OllamaConnectionError, match="not responding"):
            health_check()


class TestChat:
    """Tests for chat function."""

    @patch("ollama.client.requests.post")
    def test_successful_chat_returns_content(self, mock_post):
        mock_response = Mock()
        mock_response.json.return_value = {
            "message": {"content": "Hello, adventurer!"}
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        result = chat(
            model="llama3.2",
            system_prompt="You are a mage.",
            messages=[{"role": "user", "content": "Hello"}],
        )

        assert result == "Hello, adventurer!"
        mock_post.assert_called_once()

    @patch("ollama.client.requests.post")
    def test_chat_includes_system_prompt_in_messages(self, mock_post):
        mock_response = Mock()
        mock_response.json.return_value = {"message": {"content": "OK"}}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        chat(
            model="llama3.2",
            system_prompt="Be helpful.",
            messages=[{"role": "user", "content": "Hi"}],
        )

        call_args = mock_post.call_args
        payload = call_args.kwargs["json"]
        
        assert payload["messages"][0]["role"] == "system"
        assert payload["messages"][0]["content"] == "Be helpful."
        assert payload["messages"][1]["role"] == "user"

    @patch("ollama.client.requests.post")
    def test_connection_error_retries_and_raises(self, mock_post):
        mock_post.side_effect = requests.exceptions.ConnectionError()

        with pytest.raises(OllamaConnectionError, match="Cannot connect"):
            chat(
                model="llama3.2",
                system_prompt="Test",
                messages=[],
                max_retries=2,
                retry_delay=0.01,  # Fast for testing
            )

        # Should have retried
        assert mock_post.call_count == 2

    @patch("ollama.client.requests.post")
    def test_timeout_error_raises(self, mock_post):
        mock_post.side_effect = requests.exceptions.Timeout()

        with pytest.raises(OllamaConnectionError, match="timed out"):
            chat(
                model="llama3.2",
                system_prompt="Test",
                messages=[],
                max_retries=1,
            )

    @patch("ollama.client.requests.post")
    def test_retry_succeeds_on_second_attempt(self, mock_post):
        # First call fails, second succeeds
        mock_response = Mock()
        mock_response.json.return_value = {"message": {"content": "Success!"}}
        mock_response.raise_for_status = Mock()

        mock_post.side_effect = [
            requests.exceptions.ConnectionError(),
            mock_response,
        ]

        result = chat(
            model="llama3.2",
            system_prompt="Test",
            messages=[],
            max_retries=3,
            retry_delay=0.01,
        )

        assert result == "Success!"
        assert mock_post.call_count == 2


class TestChatStream:
    """Tests for chat_stream function."""

    @patch("ollama.client.requests.post")
    def test_stream_yields_content_chunks(self, mock_post):
        # Simulate streaming response
        mock_response = Mock()
        mock_response.iter_lines.return_value = [
            b'{"message": {"content": "Hello"}, "done": false}',
            b'{"message": {"content": " world"}, "done": false}',
            b'{"message": {"content": "!"}, "done": true}',
        ]
        mock_response.raise_for_status = Mock()
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_post.return_value = mock_response

        chunks = list(chat_stream(
            model="llama3.2",
            system_prompt="Test",
            messages=[],
        ))

        assert chunks == ["Hello", " world", "!"]

    @patch("ollama.client.requests.post")
    def test_stream_connection_error_raises(self, mock_post):
        mock_post.side_effect = requests.exceptions.ConnectionError()

        with pytest.raises(OllamaConnectionError, match="Cannot connect"):
            list(chat_stream(
                model="llama3.2",
                system_prompt="Test",
                messages=[],
            ))


class TestPresets:
    """Tests for preset configurations."""

    def test_all_presets_have_valid_class(self):
        from personas.presets import PRESETS, CLASS_FLAVOR
        
        for preset in PRESETS:
            assert preset.cls in CLASS_FLAVOR, f"Preset {preset.key} has invalid class {preset.cls}"

    def test_all_presets_have_valid_spec(self):
        from personas.presets import PRESETS, SPEC_BEHAVIOR
        
        for preset in PRESETS:
            assert preset.spec in SPEC_BEHAVIOR, f"Preset {preset.key} has invalid spec {preset.spec}"

    def test_all_presets_have_valid_mode(self):
        from personas.presets import PRESETS
        
        for preset in PRESETS:
            assert preset.mode in ("Work", "Play"), f"Preset {preset.key} has invalid mode"

    def test_all_presets_have_valid_slider_values(self):
        from personas.presets import PRESETS
        
        for preset in PRESETS:
            assert 1 <= preset.verbosity <= 10, f"Preset {preset.key} has invalid verbosity"
            assert 0 <= preset.humor <= 10, f"Preset {preset.key} has invalid humor"
            assert 1 <= preset.assertiveness <= 10, f"Preset {preset.key} has invalid assertiveness"
            assert 0 <= preset.creativity <= 10, f"Preset {preset.key} has invalid creativity"
