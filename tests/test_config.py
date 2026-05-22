from pathlib import Path

from cbio_ingest.config import load_config


def test_load_config_missing_file(tmp_path: Path) -> None:
    assert load_config(tmp_path / "nonexistent.toml") == {}


def test_load_config_returns_parsed_toml(tmp_path: Path) -> None:
    config_file = tmp_path / "config.toml"
    config_file.write_text('[cbio-ingest]\nurl = "http://example.com"\ntoken = "abc"\n')
    result = load_config(config_file)
    assert result == {"cbio-ingest": {"url": "http://example.com", "token": "abc"}}


def test_load_config_empty_file(tmp_path: Path) -> None:
    config_file = tmp_path / "config.toml"
    config_file.write_text("")
    assert load_config(config_file) == {}
