from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.modules.connections.infrastructure.channels.instagram import InstagramChannel
from src.shared.domain.messages import OutgoingMessage


@pytest.fixture
def instagram_channel():
    client_config = {"client_id": "123", "client_secret": "abc"}
    credentials_data = {"access_token": "mock_token"}
    return InstagramChannel(client_config, credentials_data)


def test_normalize_payload(instagram_channel):
    payload = {
        "object": "instagram",
        "entry": [
            {
                "id": "123456789",
                "time": 1693333333333,
                "messaging": [
                    {
                        "sender": {"id": "user_123"},
                        "recipient": {"id": "123456789"},
                        "timestamp": 1693333333333,
                        "message": {"mid": "mid_123", "text": "Hello Instagram"},
                    }
                ],
            }
        ],
    }

    incoming = instagram_channel.normalize_payload(payload)

    assert incoming is not None
    assert incoming.user_id == "user_123"
    assert incoming.text == "Hello Instagram"
    assert incoming.channel_type == "instagram"
    assert incoming.metadata["recipient_id"] == "123456789"


@pytest.mark.anyio
async def test_send_message(instagram_channel):
    message = OutgoingMessage(user_id="user_123", text="Hello back")

    # Mock Response object
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "recipient_id": "user_123",
        "message_id": "mid_response",
    }
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response

        response = await instagram_channel.send_message(message)

        assert response["message_id"] == "mid_response"

        # Verify URL and Headers
        args, kwargs = mock_post.call_args
        assert "graph.facebook.com" in args[0]
        assert kwargs["json"]["recipient"]["id"] == "user_123"
        assert kwargs["json"]["message"]["text"] == "Hello back"
        assert kwargs["headers"]["Authorization"] == "Bearer mock_token"


@pytest.mark.anyio
async def test_set_typing_status(instagram_channel):
    user_id = "user_123"

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response

        await instagram_channel.set_typing_status(user_id)

        _args, kwargs = mock_post.call_args
        assert kwargs["json"]["sender_action"] == "typing_on"
        assert kwargs["json"]["recipient"]["id"] == "user_123"
