import json
import uuid

from sqlalchemy import text

from src.modules.connections.infrastructure.models.channel_connection_model import (
    ChannelConnectionModel,
)


def test_channel_credentials_encryption(db):
    """
    Test that channel credentials are encrypted in the database but decrypted on access.
    """
    # 1. Create a channel with sensitive credentials
    credentials = {"api_key": "secret_123", "token": "abc-def"}
    tenant_id = uuid.uuid4()
    channel = ChannelConnectionModel(
        tenant_id=tenant_id,
        channel_type="whatsapp",
        credentials=credentials,
        config={"some": "config"},
    )
    db.add(channel)
    db.commit()
    db.refresh(channel)

    # 2. Verify we can access it normally
    assert channel.credentials == credentials
    assert channel.credentials["api_key"] == "secret_123"

    # 3. Verify it is encrypted in the database using raw SQL
    # Note: In SQLite (tests), JSONB is stored as TEXT.
    result = db.execute(
        text("SELECT credentials FROM channel_connections WHERE id = :cid"),
        {"cid": str(channel.id)},
    ).scalar()

    print(f"Raw DB value: {result}")

    stored_json = json.loads(result) if isinstance(result, str) else result

    assert "_encrypted" in stored_json
    # Ensure it's not just the plain JSON
    assert stored_json["_encrypted"] != json.dumps(credentials)


def test_channel_credentials_legacy_support(db):
    """
    Test that legacy plaintext credentials can still be read.
    """
    # 1. Insert raw plaintext JSON using SQL
    channel_id = uuid.uuid4()
    tenant_id = uuid.uuid4()
    legacy_creds = {"legacy": "true", "key": "old_secret"}
    legacy_creds_json = json.dumps(legacy_creds)

    # We use raw SQL to bypass the ORM encryption
    db.execute(
        text(
            "INSERT INTO channel_connections (id, tenant_id, channel_type, credentials, config, is_active)"
            " VALUES (:cid, :tid, 'telegram', :creds, '{}', 1)",
        ),
        {"cid": str(channel_id), "tid": str(tenant_id), "creds": legacy_creds_json},
    )
    db.commit()

    # 2. Retrieve using ORM
    channel = db.query(ChannelConnectionModel).filter(ChannelConnectionModel.id == channel_id).first()

    assert channel is not None
    # Should be read as is (no _encrypted key) because it lacks the marker
    assert channel.credentials == legacy_creds

    # 3. Save it again (should encrypt now because we are going through ORM)
    channel.credentials = {"new": "value"}
    db.commit()
    db.refresh(channel)

    assert channel.credentials == {"new": "value"}

    # Verify encryption
    result = db.execute(
        text("SELECT credentials FROM channel_connections WHERE id = :cid"),
        {"cid": str(channel_id)},
    ).scalar()

    stored_json = json.loads(result) if isinstance(result, str) else result

    assert "_encrypted" in stored_json
