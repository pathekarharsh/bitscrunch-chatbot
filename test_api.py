from bitscrunch.api_client import BitsCrunchAPIClient

client = BitsCrunchAPIClient()

# Test with the wallet address you confirmed works
response = client.get_wallet_balance(
    address="0x9656911585799e7129668a1e79a0C8b43dbB7EA9",
    limit=1
)

print("\nWallet Balance Response:")
print(f"Total Items: {response.pagination.total_items}")
print(f"Offset: {response.pagination.offset}")
print(f"Limit: {response.pagination.limit}")
print(f"Has Next: {response.pagination.has_next}\n")

print("Token Balances:")
for token in response.token:
    print(f"- Blockchain: {token.blockchain}")
    print(f"  Chain ID: {token.chain_id}")
    print(f"  Token: {token.token_name} ({token.token_symbol})")
    print(f"  Address: {token.token_address}")
    print(f"  Quantity: {token.quantity}")
    print(f"  Decimals: {token.decimal}\n")