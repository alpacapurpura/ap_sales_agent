"""Tests for chat parsers (WhatsApp, Instagram, Telegram) — TDD RED → GREEN."""

import json

import pytest

from src.modules.brand.infrastructure.parsers.base import detect_and_parse
from src.modules.brand.infrastructure.parsers.instagram_parser import (
    InstagramParser,
)
from src.modules.brand.infrastructure.parsers.telegram_parser import TelegramParser
from src.modules.brand.infrastructure.parsers.whatsapp_parser import WhatsAppParser

# ---------------------------------------------------------------------------
# WhatsApp
# ---------------------------------------------------------------------------


class TestWhatsAppParser:
    """Tests for WhatsApp .txt chat export parser."""

    def test_basic_parsing_with_user_name(self):
        content = (
            "12/25/23, 3:45 PM - María López: Hola! Cómo estás?\n"
            "12/25/23, 3:46 PM - Juan Pérez: Bien y tú?\n"
            "12/25/23, 3:47 PM - María López: Todo bien!"
        )
        parser = WhatsAppParser()
        msgs = parser.parse(content, user_name="María López")
        assert len(msgs) == 2
        assert msgs[0].text == "Hola! Cómo estás?"
        assert msgs[1].text == "Todo bien!"

    def test_word_count(self):
        content = "12/25/23, 3:45 PM - María López: Hola cómo estás amigo\n"
        parser = WhatsAppParser()
        msgs = parser.parse(content, user_name="María López")
        assert msgs[0].word_count == 4

    def test_emoji_detection(self):
        content = "12/25/23, 3:45 PM - María López: Sin emoji aquí\n12/25/23, 3:46 PM - María López: Con emoji 😊\n"
        parser = WhatsAppParser()
        msgs = parser.parse(content, user_name="María López")
        assert msgs[0].has_emoji is False
        assert msgs[1].has_emoji is True

    def test_skips_system_messages(self):
        content = (
            "Messages and calls are end-to-end encrypted."
            " No one outside of this chat, not even WhatsApp, can read or listen to them.\n"
            "12/25/23, 3:45 PM - María López: Hola!\n"
        )
        parser = WhatsAppParser()
        msgs = parser.parse(content, user_name="María López")
        assert len(msgs) == 1
        assert msgs[0].text == "Hola!"

    def test_skips_media_omitted(self):
        content = (
            "12/25/23, 3:45 PM - María López: <Media omitted>\n"
            "12/25/23, 3:46 PM - Juan Pérez: image omitted\n"
            "12/25/23, 3:47 PM - María López: Texto normal\n"
        )
        parser = WhatsAppParser()
        msgs = parser.parse(content, user_name="María López")
        assert len(msgs) == 1
        assert msgs[0].text == "Texto normal"

    def test_skips_various_media_types(self):
        content = (
            "12/25/23, 3:45 PM - María: audio omitted\n"
            "12/25/23, 3:46 PM - María: sticker omitted\n"
            "12/25/23, 3:47 PM - María: video omitted\n"
            "12/25/23, 3:48 PM - María: Texto real\n"
        )
        parser = WhatsAppParser()
        msgs = parser.parse(content, user_name="María")
        assert len(msgs) == 1

    def test_multiline_messages(self):
        content = (
            "12/25/23, 3:45 PM - María López: Primera línea\n"
            "Segunda línea del mismo mensaje\n"
            "Tercera línea\n"
            "12/25/23, 3:46 PM - Juan Pérez: Otro mensaje\n"
        )
        parser = WhatsAppParser()
        msgs = parser.parse(content, user_name="María López")
        assert len(msgs) == 1
        assert "Primera línea" in msgs[0].text
        assert "Segunda línea" in msgs[0].text
        assert "Tercera línea" in msgs[0].text

    def test_auto_detect_user_most_frequent(self):
        content = (
            "12/25/23, 3:45 PM - María López: Hola\n"
            "12/25/23, 3:46 PM - Juan Pérez: Hey\n"
            "12/25/23, 3:47 PM - María López: Cómo estás?\n"
            "12/25/23, 3:48 PM - María López: Te cuento algo\n"
        )
        parser = WhatsAppParser()
        msgs = parser.parse(content, user_name=None)
        # María López is the most frequent → 3 messages
        assert len(msgs) == 3

    def test_bracket_format(self):
        content = "[12/25/23, 3:45:23 PM] - María López: Hola!\n"
        parser = WhatsAppParser()
        msgs = parser.parse(content, user_name="María López")
        assert len(msgs) == 1
        assert msgs[0].text == "Hola!"

    def test_24h_format(self):
        content = "25/12/2023, 15:45 - María López: Hola en 24h\n"
        parser = WhatsAppParser()
        msgs = parser.parse(content, user_name="María López")
        assert len(msgs) == 1
        assert msgs[0].text == "Hola en 24h"

    def test_sender_stored_in_message(self):
        content = "12/25/23, 3:45 PM - María López: Hola!\n"
        parser = WhatsAppParser()
        msgs = parser.parse(content, user_name="María López")
        assert msgs[0].sender == "María López"

    def test_can_parse_valid_whatsapp(self):
        content = "12/25/23, 3:45 PM - Alguien: Mensaje\n"
        parser = WhatsAppParser()
        assert parser.can_parse(content) is True

    def test_cannot_parse_json(self):
        content = '{"messages": []}'
        parser = WhatsAppParser()
        assert parser.can_parse(content) is False

    def test_timestamp_parsed(self):
        content = "12/25/23, 3:45 PM - María López: Hola!\n"
        parser = WhatsAppParser()
        msgs = parser.parse(content, user_name="María López")
        assert msgs[0].timestamp is not None

    def test_empty_content_returns_empty(self):
        parser = WhatsAppParser()
        msgs = parser.parse("", user_name="Alguien")
        assert msgs == []

    def test_no_matching_user_returns_empty(self):
        content = "12/25/23, 3:45 PM - María López: Hola!\n"
        parser = WhatsAppParser()
        msgs = parser.parse(content, user_name="Persona Inexistente")
        assert msgs == []


# ---------------------------------------------------------------------------
# Instagram
# ---------------------------------------------------------------------------


class TestInstagramParser:
    """Tests for Instagram DM JSON (Meta Data Export) parser."""

    def _make_ig_json(self, messages: list, participants: list | None = None) -> str:
        if participants is None:
            participants = [{"name": "user1"}, {"name": "user2"}]
        data = {"participants": participants, "messages": messages}
        return json.dumps(data)

    def test_basic_parsing(self):
        raw = self._make_ig_json(
            messages=[
                {
                    "sender_name": "user1",
                    "timestamp_ms": 1637366520000,
                    "content": "Hola!",
                    "type": "Generic",
                },
                {
                    "sender_name": "user2",
                    "timestamp_ms": 1637366580000,
                    "content": "Hey!",
                    "type": "Generic",
                },
                {
                    "sender_name": "user1",
                    "timestamp_ms": 1637366640000,
                    "content": "Cómo vas?",
                    "type": "Generic",
                },
            ]
        )
        parser = InstagramParser()
        msgs = parser.parse(raw, user_name="user1")
        assert len(msgs) == 2
        assert msgs[0].text == "Hola!"
        assert msgs[1].text == "Cómo vas?"

    def test_skips_non_generic_type(self):
        raw = self._make_ig_json(
            messages=[
                {
                    "sender_name": "user1",
                    "timestamp_ms": 1637366520000,
                    "content": "Compartió algo",
                    "type": "Share",
                },
                {
                    "sender_name": "user1",
                    "timestamp_ms": 1637366580000,
                    "content": "Mensaje real",
                    "type": "Generic",
                },
            ]
        )
        parser = InstagramParser()
        msgs = parser.parse(raw, user_name="user1")
        assert len(msgs) == 1
        assert msgs[0].text == "Mensaje real"

    def test_skips_call_type(self):
        raw = self._make_ig_json(
            messages=[
                {
                    "sender_name": "user1",
                    "timestamp_ms": 1637366520000,
                    "type": "Call",
                },
                {
                    "sender_name": "user1",
                    "timestamp_ms": 1637366580000,
                    "content": "Texto",
                    "type": "Generic",
                },
            ]
        )
        parser = InstagramParser()
        msgs = parser.parse(raw, user_name="user1")
        assert len(msgs) == 1

    def test_skips_media_only_messages(self):
        raw = self._make_ig_json(
            messages=[
                {
                    "sender_name": "user1",
                    "timestamp_ms": 1637366520000,
                    "type": "Generic",
                    # No "content" key — media only
                },
                {
                    "sender_name": "user1",
                    "timestamp_ms": 1637366580000,
                    "content": "Texto",
                    "type": "Generic",
                },
            ]
        )
        parser = InstagramParser()
        msgs = parser.parse(raw, user_name="user1")
        assert len(msgs) == 1
        assert msgs[0].text == "Texto"

    def test_auto_detect_user_uses_first_participant(self):
        raw = self._make_ig_json(
            participants=[{"name": "user1"}, {"name": "user2"}],
            messages=[
                {
                    "sender_name": "user1",
                    "timestamp_ms": 1637366520000,
                    "content": "Hola",
                    "type": "Generic",
                },
                {
                    "sender_name": "user2",
                    "timestamp_ms": 1637366580000,
                    "content": "Hey",
                    "type": "Generic",
                },
            ],
        )
        parser = InstagramParser()
        msgs = parser.parse(raw, user_name=None)
        assert len(msgs) == 1
        assert msgs[0].text == "Hola"

    def test_can_parse_valid_ig_json(self):
        raw = self._make_ig_json(messages=[])
        parser = InstagramParser()
        assert parser.can_parse(raw) is True

    def test_cannot_parse_whatsapp_text(self):
        content = "12/25/23, 3:45 PM - Alguien: Mensaje"
        parser = InstagramParser()
        assert parser.can_parse(content) is False

    def test_cannot_parse_invalid_json(self):
        parser = InstagramParser()
        assert parser.can_parse("not json at all") is False

    def test_timestamp_is_parsed(self):
        raw = self._make_ig_json(
            messages=[
                {
                    "sender_name": "user1",
                    "timestamp_ms": 1637366520000,
                    "content": "Hola",
                    "type": "Generic",
                }
            ]
        )
        parser = InstagramParser()
        msgs = parser.parse(raw, user_name="user1")
        assert msgs[0].timestamp is not None

    def test_sender_stored(self):
        raw = self._make_ig_json(
            messages=[
                {
                    "sender_name": "user1",
                    "timestamp_ms": 1637366520000,
                    "content": "Hola",
                    "type": "Generic",
                }
            ]
        )
        parser = InstagramParser()
        msgs = parser.parse(raw, user_name="user1")
        assert msgs[0].sender == "user1"

    def test_word_count(self):
        raw = self._make_ig_json(
            messages=[
                {
                    "sender_name": "user1",
                    "timestamp_ms": 1637366520000,
                    "content": "hola cómo estás amigo",
                    "type": "Generic",
                }
            ]
        )
        parser = InstagramParser()
        msgs = parser.parse(raw, user_name="user1")
        assert msgs[0].word_count == 4

    def test_emoji_detection(self):
        raw = self._make_ig_json(
            messages=[
                {
                    "sender_name": "user1",
                    "timestamp_ms": 1637366520000,
                    "content": "Hola 😊",
                    "type": "Generic",
                }
            ]
        )
        parser = InstagramParser()
        msgs = parser.parse(raw, user_name="user1")
        assert msgs[0].has_emoji is True


# ---------------------------------------------------------------------------
# Telegram
# ---------------------------------------------------------------------------


class TestTelegramParser:
    """Tests for Telegram Desktop JSON export parser."""

    def _make_tg_json(self, messages: list, name: str = "Mi Chat") -> str:
        data = {"name": name, "type": "personal_chat", "messages": messages}
        return json.dumps(data)

    def test_basic_parsing(self):
        raw = self._make_tg_json(
            messages=[
                {
                    "id": 1,
                    "type": "message",
                    "date": "2024-01-15T10:30:00",
                    "from": "User Name",
                    "text": "Hola!",
                },
                {
                    "id": 2,
                    "type": "message",
                    "date": "2024-01-15T10:31:00",
                    "from": "Other",
                    "text": "Hey!",
                },
                {
                    "id": 3,
                    "type": "message",
                    "date": "2024-01-15T10:32:00",
                    "from": "User Name",
                    "text": "Cómo estás?",
                },
            ]
        )
        parser = TelegramParser()
        msgs = parser.parse(raw, user_name="User Name")
        assert len(msgs) == 2
        assert msgs[0].text == "Hola!"
        assert msgs[1].text == "Cómo estás?"

    def test_text_entities_list(self):
        raw = self._make_tg_json(
            messages=[
                {
                    "id": 1,
                    "type": "message",
                    "date": "2024-01-15T10:30:00",
                    "from": "User Name",
                    "text": [
                        {"type": "plain", "text": "Hola "},
                        {"type": "bold", "text": "mundo"},
                        {"type": "plain", "text": "!"},
                    ],
                }
            ]
        )
        parser = TelegramParser()
        msgs = parser.parse(raw, user_name="User Name")
        assert len(msgs) == 1
        assert msgs[0].text == "Hola mundo!"

    def test_skips_service_messages(self):
        raw = self._make_tg_json(
            messages=[
                {
                    "id": 1,
                    "type": "service",
                    "date": "2024-01-15T10:30:00",
                    "text": "User joined the group",
                },
                {
                    "id": 2,
                    "type": "message",
                    "date": "2024-01-15T10:31:00",
                    "from": "User Name",
                    "text": "Hola!",
                },
            ]
        )
        parser = TelegramParser()
        msgs = parser.parse(raw, user_name="User Name")
        assert len(msgs) == 1
        assert msgs[0].text == "Hola!"

    def test_auto_detect_user_most_frequent(self):
        raw = self._make_tg_json(
            messages=[
                {
                    "id": 1,
                    "type": "message",
                    "date": "2024-01-15T10:30:00",
                    "from": "User Name",
                    "text": "Msg 1",
                },
                {
                    "id": 2,
                    "type": "message",
                    "date": "2024-01-15T10:31:00",
                    "from": "Other",
                    "text": "Resp",
                },
                {
                    "id": 3,
                    "type": "message",
                    "date": "2024-01-15T10:32:00",
                    "from": "User Name",
                    "text": "Msg 2",
                },
                {
                    "id": 4,
                    "type": "message",
                    "date": "2024-01-15T10:33:00",
                    "from": "User Name",
                    "text": "Msg 3",
                },
            ]
        )
        parser = TelegramParser()
        msgs = parser.parse(raw, user_name=None)
        assert len(msgs) == 3

    def test_can_parse_valid_telegram(self):
        raw = self._make_tg_json(
            messages=[
                {
                    "id": 1,
                    "type": "message",
                    "date": "2024-01-15T10:30:00",
                    "from": "User",
                    "text": "Hola",
                }
            ]
        )
        parser = TelegramParser()
        assert parser.can_parse(raw) is True

    def test_cannot_parse_whatsapp(self):
        content = "12/25/23, 3:45 PM - Alguien: Mensaje"
        parser = TelegramParser()
        assert parser.can_parse(content) is False

    def test_cannot_parse_ig_json(self):
        raw = json.dumps(
            {
                "participants": [{"name": "u1"}],
                "messages": [
                    {
                        "sender_name": "u1",
                        "timestamp_ms": 123,
                        "content": "x",
                        "type": "Generic",
                    }
                ],
            }
        )
        parser = TelegramParser()
        assert parser.can_parse(raw) is False

    def test_timestamp_parsed(self):
        raw = self._make_tg_json(
            messages=[
                {
                    "id": 1,
                    "type": "message",
                    "date": "2024-01-15T10:30:00",
                    "from": "User Name",
                    "text": "Hola",
                }
            ]
        )
        parser = TelegramParser()
        msgs = parser.parse(raw, user_name="User Name")
        assert msgs[0].timestamp is not None

    def test_sender_stored(self):
        raw = self._make_tg_json(
            messages=[
                {
                    "id": 1,
                    "type": "message",
                    "date": "2024-01-15T10:30:00",
                    "from": "User Name",
                    "text": "Hola",
                }
            ]
        )
        parser = TelegramParser()
        msgs = parser.parse(raw, user_name="User Name")
        assert msgs[0].sender == "User Name"

    def test_word_count(self):
        raw = self._make_tg_json(
            messages=[
                {
                    "id": 1,
                    "type": "message",
                    "date": "2024-01-15T10:30:00",
                    "from": "User Name",
                    "text": "hola cómo estás",
                }
            ]
        )
        parser = TelegramParser()
        msgs = parser.parse(raw, user_name="User Name")
        assert msgs[0].word_count == 3

    def test_emoji_detection(self):
        raw = self._make_tg_json(
            messages=[
                {
                    "id": 1,
                    "type": "message",
                    "date": "2024-01-15T10:30:00",
                    "from": "User Name",
                    "text": "Hola 🎉",
                }
            ]
        )
        parser = TelegramParser()
        msgs = parser.parse(raw, user_name="User Name")
        assert msgs[0].has_emoji is True

    def test_skips_empty_text_messages(self):
        raw = self._make_tg_json(
            messages=[
                {
                    "id": 1,
                    "type": "message",
                    "date": "2024-01-15T10:30:00",
                    "from": "User Name",
                    "text": "",
                },
                {
                    "id": 2,
                    "type": "message",
                    "date": "2024-01-15T10:31:00",
                    "from": "User Name",
                    "text": "Texto real",
                },
            ]
        )
        parser = TelegramParser()
        msgs = parser.parse(raw, user_name="User Name")
        assert len(msgs) == 1
        assert msgs[0].text == "Texto real"


# ---------------------------------------------------------------------------
# Auto-detect — detect_and_parse dispatcher
# ---------------------------------------------------------------------------


class TestAutoDetect:
    """Tests for the auto-format detection dispatcher."""

    def test_detects_whatsapp(self):
        content = (
            "12/25/23, 3:45 PM - María López: Hola!\n"
            "12/25/23, 3:46 PM - Juan Pérez: Hey!\n"
            "12/25/23, 3:47 PM - María López: Bye!\n"
        )
        msgs = detect_and_parse(content, user_name="María López")
        assert len(msgs) == 2

    def test_detects_instagram(self):
        data = {
            "participants": [{"name": "user1"}, {"name": "user2"}],
            "messages": [
                {
                    "sender_name": "user1",
                    "timestamp_ms": 1637366520000,
                    "content": "Hola",
                    "type": "Generic",
                }
            ],
        }
        msgs = detect_and_parse(json.dumps(data), user_name="user1")
        assert len(msgs) == 1

    def test_detects_telegram(self):
        data = {
            "name": "Chat",
            "type": "personal_chat",
            "messages": [
                {
                    "id": 1,
                    "type": "message",
                    "date": "2024-01-15T10:30:00",
                    "from": "User",
                    "text": "Hola",
                }
            ],
        }
        msgs = detect_and_parse(json.dumps(data), user_name="User")
        assert len(msgs) == 1

    def test_unknown_format_raises_value_error(self):
        with pytest.raises(ValueError, match="Unsupported chat format"):
            detect_and_parse("Este texto no tiene formato conocido", user_name=None)

    def test_random_json_raises_value_error(self):
        data = {"foo": "bar", "baz": 123}
        with pytest.raises(ValueError, match="Unsupported chat format"):
            detect_and_parse(json.dumps(data), user_name=None)
