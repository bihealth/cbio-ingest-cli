import tomllib
from pathlib import Path

DEFAULT_CONFIG_PATH = Path.home() / ".config" / "cbio-ingest" / "config.toml"

# Expected config.toml structure:
# [default]
# url = "http://localhost:8080"
# token = "your-bearer-token"


def load_config(config_path: Path) -> dict:
    if config_path.exists():
        with open(config_path, "rb") as f:
            return tomllib.load(f)
    return {}
