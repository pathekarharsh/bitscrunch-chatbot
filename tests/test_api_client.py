# Tests for api_client
import pytest
from bitscrunch.api_client import BitsCrunchAPIClient
from bitscrunch.schemas import WalletBalanceResponse

@pytest.fixture
def api_client():
    return BitsCrunchAPIClient()

def test_get_wallet_balance(api_client):
    # Test with a known wallet address
    response = api_client.get_wallet_balance(
        address="0x9656911585799e7129668a1e79a0C8b43dbB7EA9",
        limit=1
    )
    assert isinstance(response, WalletBalanceResponse)
    assert response.address == "0x9656911585799e7129668a1e79a0C8b43dbB7EA9"
    assert len(response.balances) > 0