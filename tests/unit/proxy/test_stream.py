"""
Tests unitaires pour le streaming proxy.

Pourquoi: le streaming est critique et complexe (async, erreurs réseau,
extraction tokens). Ces tests vérifient la robustesse.
"""
import pytest
from unittest.mock import MagicMock

import httpx

from kimi_proxy.proxy.stream import (
    stream_generator,
    extract_usage_from_stream,
    extract_usage_from_response
)


class TestExtractUsageFromStream:
    """Tests extraction des tokens depuis le buffer SSE."""

    def test_extract_openai_standard(self):
        """Extraction format OpenAI standard."""
        buffer = b'data: {"usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150}}\n\n'
        result = extract_usage_from_stream(buffer, "openai")

        assert result is not None
        assert result["prompt_tokens"] == 100
        assert result["completion_tokens"] == 50
        assert result["total_tokens"] == 150

    def test_extract_gemini_format(self):
        """Extraction format Gemini."""
        buffer = b'data: {"usageMetadata": {"promptTokenCount": 200, "candidatesTokenCount": 100, "totalTokenCount": 300}}\n\n'
        result = extract_usage_from_stream(buffer, "gemini")

        assert result is not None
        assert result["prompt_tokens"] == 200
        assert result["completion_tokens"] == 100
        assert result["total_tokens"] == 300

    def test_extract_multiple_chunks(self):
        """Extraction avec plusieurs chunks SSE."""
        buffer = (
            b'data: {"choices": [{"delta": {"content": "Hello"}}]}\n\n'
            b'data: {"choices": [{"delta": {"content": " World"}}]}\n\n'
            b'data: {"usage": {"prompt_tokens": 10, "completion_tokens": 2, "total_tokens": 12}}\n\n'
            b'data: [DONE]\n\n'
        )
        result = extract_usage_from_stream(buffer, "openai")

        assert result is not None
        assert result["total_tokens"] == 12

    def test_extract_empty_buffer(self):
        """Buffer vide retourne None."""
        result = extract_usage_from_stream(b"")
        assert result is None

    def test_extract_no_usage(self):
        """Pas d'usage dans le stream retourne None."""
        buffer = b'data: {"choices": [{"delta": {"content": "Hello"}}]}\n\n'
        result = extract_usage_from_stream(buffer, "openai")
        assert result is None

    def test_extract_malformed_json(self):
        """JSON malformé est ignoré gracieusement."""
        buffer = (
            b'data: {invalid json}\n\n'
            b'data: {"usage": {"total_tokens": 100}}\n\n'
        )
        result = extract_usage_from_stream(buffer, "openai")
        assert result is not None
        assert result["total_tokens"] == 100


class TestExtractUsageFromResponse:
    """Tests extraction depuis réponse complète."""

    def test_extract_response(self):
        """Extraction standard."""
        response = {
            "usage": {
                "prompt_tokens": 50,
                "completion_tokens": 25,
                "total_tokens": 75
            }
        }
        result = extract_usage_from_response(response)

        assert result is not None
        assert result["prompt_tokens"] == 50
        assert result["completion_tokens"] == 25
        assert result["total_tokens"] == 75

    def test_extract_no_usage(self):
        """Pas d'usage retourne None."""
        response = {"choices": [{"message": {"content": "Hello"}}]}
        result = extract_usage_from_response(response)
        assert result is None


class TestStreamGenerator:
    """Tests du générateur de streaming."""

    @pytest.mark.anyio
    async def test_stream_yields_chunks(self):
        """Le stream yield tous les chunks."""
        # Mock response
        response = MagicMock()
        response.status_code = 200

        async def mock_aiter():
            yield b'chunk1'
            yield b'chunk2'
            yield b'chunk3'

        response.aiter_bytes = MagicMock(return_value=mock_aiter())

        chunks = []
        async for chunk in stream_generator(
            response,
            session_id=1,
            metric_id=1,
            provider_type="openai",
            models={}
        ):
            chunks.append(chunk)

        assert len(chunks) == 3
        assert chunks == [b'chunk1', b'chunk2', b'chunk3']

    @pytest.mark.anyio
    async def test_stream_handles_read_error(self):
        """ReadError est géré gracieusement."""
        response = MagicMock()
        response.status_code = 200

        async def error_iter():
            yield b'chunk1'
            raise httpx.ReadError("Connexion perdue")

        response.aiter_bytes = MagicMock(return_value=error_iter())

        # Ne doit pas lever d'exception
        chunks = []
        async for chunk in stream_generator(
            response,
            session_id=1,
            metric_id=1,
            provider_type="openai",
            models={}
        ):
            chunks.append(chunk)

        # Les chunks avant l'erreur sont conservés
        assert len(chunks) == 1
        assert chunks[0] == b'chunk1'

    @pytest.mark.anyio
    async def test_stream_handles_timeout(self):
        """TimeoutException est géré gracieusement."""
        response = MagicMock()
        response.status_code = 200

        async def timeout_iter():
            yield b'data'
            raise httpx.TimeoutException("Timeout")

        response.aiter_bytes = MagicMock(return_value=timeout_iter())

        chunks = []
        async for chunk in stream_generator(
            response,
            session_id=1,
            metric_id=1,
            provider_type="openai",
            models={}
        ):
            chunks.append(chunk)

        assert len(chunks) == 1
