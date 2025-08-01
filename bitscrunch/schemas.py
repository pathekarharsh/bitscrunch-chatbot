from typing import List
from pydantic import BaseModel

class TokenBalance(BaseModel):
    blockchain: str
    chain_id: int
    decimal: int
    quantity: float
    token_address: str
    token_name: str
    token_symbol: str

class Pagination(BaseModel):
    total_items: int
    offset: int
    limit: int
    has_next: bool

class WalletBalanceResponse(BaseModel):
    token: List[TokenBalance]
    pagination: Pagination