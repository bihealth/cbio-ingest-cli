import pytest
from click.testing import CliRunner


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def base_url() -> str:
    return "http://testserver"


@pytest.fixture
def cli_args(base_url: str) -> list[str]:
    """Root CLI args that satisfy --url and --token requirements."""
    return ["--url", base_url, "--token", "test-token"]
