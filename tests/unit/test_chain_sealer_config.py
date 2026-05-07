import pytest

from src.api.chain_sealer import ChainSealer


def test_chain_sealer_rejects_non_hex_signing_key_with_safe_message(
    monkeypatch, tmp_path
):
    monkeypatch.setenv("UATP_SIGNING_KEY", "not-a-hex-key")

    with pytest.raises(ValueError) as exc:
        ChainSealer(seals_dir=str(tmp_path))

    message = str(exc.value)
    assert "UATP_SIGNING_KEY" in message
    assert "hex" in message.lower()
    assert "not-a-hex-key" not in message


def test_chain_sealer_rejects_wrong_length_signing_key_with_safe_message(
    monkeypatch, tmp_path
):
    monkeypatch.setenv("UATP_SIGNING_KEY", "deadbeef")

    with pytest.raises(ValueError) as exc:
        ChainSealer(seals_dir=str(tmp_path))

    message = str(exc.value)
    assert "UATP_SIGNING_KEY" in message
    assert "32-byte" in message
    assert "deadbeef" not in message


def test_chain_sealer_accepts_valid_hex_signing_key(monkeypatch, tmp_path):
    monkeypatch.setenv("UATP_SIGNING_KEY", "00" * 32)

    sealer = ChainSealer(seals_dir=str(tmp_path))

    assert sealer.verify_key_hex


def test_chain_sealer_rejects_missing_signing_key_in_production(monkeypatch, tmp_path):
    monkeypatch.delenv("UATP_SIGNING_KEY", raising=False)
    monkeypatch.setenv("ENVIRONMENT", "production")

    with pytest.raises(ValueError) as exc:
        ChainSealer(seals_dir=str(tmp_path))

    message = str(exc.value)
    assert "UATP_SIGNING_KEY" in message
    assert "required" in message.lower()
    assert "production" in message.lower()
    assert "Generated" not in message


def test_chain_sealer_rejects_missing_signing_key_without_explicit_environment(
    monkeypatch, tmp_path
):
    monkeypatch.delenv("UATP_SIGNING_KEY", raising=False)
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    monkeypatch.delenv("UATP_ENV", raising=False)
    monkeypatch.delenv("APP_ENV", raising=False)

    with pytest.raises(ValueError) as exc:
        ChainSealer(seals_dir=str(tmp_path))

    message = str(exc.value)
    assert "UATP_SIGNING_KEY" in message
    assert "required" in message.lower()
    assert "Generated" not in message


def test_chain_sealer_allows_ephemeral_key_only_in_testing(
    monkeypatch, tmp_path, capsys
):
    monkeypatch.delenv("UATP_SIGNING_KEY", raising=False)
    monkeypatch.setenv("ENVIRONMENT", "testing")

    sealer = ChainSealer(seals_dir=str(tmp_path))

    assert sealer.verify_key_hex
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
