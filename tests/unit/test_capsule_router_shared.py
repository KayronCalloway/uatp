import uuid

from src.api.capsules._shared import to_uuid


def test_to_uuid_returns_uuid_input_unchanged():
    user_id = uuid.uuid4()

    assert to_uuid(user_id) == user_id


def test_to_uuid_converts_uuid_string():
    user_id = uuid.uuid4()

    assert to_uuid(str(user_id)) == user_id
