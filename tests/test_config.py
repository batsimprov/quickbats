from quickbats.config import CONFIG
from quickbats.config import AUTH
from quickbats.config import TOKENS

def test_config_sections():
    assert "stripe" in CONFIG

def test_auth_keys():
    assert isinstance(AUTH, dict)
    assert "quickbooks_client_id" in AUTH

def test_tokens_keys():
    assert "access_token" in TOKENS
