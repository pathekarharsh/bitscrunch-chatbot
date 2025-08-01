import re
from typing import Dict, Any, List, Optional
from decimal import Decimal, InvalidOperation

class DataProcessor:
    def __init__(self):
        self.supported_networks = {
            'ethereum': 1,
            'polygon': 137,
            'bsc': 56,
            'arbitrum': 42161,
            'optimism': 10
        }

    def is_valid_wallet_address(self, address: str) -> bool:
        """Validate Ethereum wallet address format"""
        if not address:
            return False
        
        # Remove any whitespace
        address = address.strip()
        
        # Check if it's a valid Ethereum address
        eth_pattern = r'^0x[a-fA-F0-9]{40}$'
        return bool(re.match(eth_pattern, address))

    def format_wallet_balance(self, response, wallet_address: str) -> str:
        """Format wallet balance data into HTML"""
        try:
            tokens = []
            total_value = 0.0
            
            if hasattr(response, 'data') and response.data:
                for token in response.data:
                    token_data = {
                        'symbol': self._safe_get_attr(token, 'symbol', 'Unknown'),
                        'name': self._safe_get_attr(token, 'name', 'Unknown Token'),
                        'balance': self._format_balance(self._safe_get_attr(token, 'balance', '0')),
                        'usd_value': self._safe_get_attr(token, 'usd_value', '0'),
                        'contract_address': self._safe_get_attr(token, 'contract_address', ''),
                        'network': self._safe_get_attr(token, 'network', 'ethereum'),
                        'decimals': self._safe_get_attr(token, 'decimals', 18)
                    }
                    
                    # Calculate USD value
                    try:
                        usd_val = float(token_data['usd_value']) if token_data['usd_value'] else 0.0
                        total_value += usd_val
                    except (ValueError, TypeError):
                        pass
                    
                    tokens.append(token_data)
            
            return self._generate_wallet_html(tokens, wallet_address, total_value)
            
        except Exception as e:
            return f"<p>Error processing wallet data: {str(e)}</p>"

    def _safe_get_attr(self, obj, attr: str, default: Any = None) -> Any:
        """Safely get attribute from object"""
        try:
            return getattr(obj, attr, default)
        except AttributeError:
            return default

    def _format_balance(self, balance: str) -> str:
        """Format token balance for display"""
        try:
            if not balance or balance == '0':
                return '0'
            
            # Convert to decimal for precise formatting
            decimal_balance = Decimal(str(balance))
            
            # Format based on size
            if decimal_balance == 0:
                return '0'
            elif decimal_balance < Decimal('0.001'):
                return f"{decimal_balance:.8f}".rstrip('0').rstrip('.')
            elif decimal_balance < Decimal('1'):
                return f"{decimal_balance:.6f}".rstrip('0').rstrip('.')
            elif decimal_balance < Decimal('1000'):
                return f"{decimal_balance:.4f}".rstrip('0').rstrip('.')
            else:
                return f"{decimal_balance:,.2f}"
                
        except (InvalidOperation, ValueError, TypeError):
            return str(balance) if balance else '0'

    def _format_usd_value(self, usd_value: str) -> str:
        """Format USD value for display"""
        try:
            if not usd_value or usd_value == '0':
                return '$0.00'
            
            value = float(usd_value)
            if value < 0.01:
                return f"${value:.6f}".rstrip('0').rstrip('.')
            else:
                return f"${value:,.2f}"
                
        except (ValueError, TypeError):
            return '$0.00'

    def _generate_wallet_html(self, tokens: List[Dict], wallet_address: str, total_value: float) -> str:
        """Generate HTML for wallet analysis"""
        
        token_count = len(tokens)
        
        # Generate tokens HTML
        tokens_html = ""
        for token in tokens[:10]:  # Show top 10 tokens
            icon_text = token['symbol'][:1].upper() if token['symbol'] else '?'
            usd_display = self._format_usd_value(token['usd_value'])
            
            tokens_html += f'''
            <div class="token-card">
                <div class="token-header">
                    <div class="token-icon">{icon_text}</div>
                    <div class="token-info">
                        <div class="token-name">{self._escape_html(token['name'])}</div>
                        <span class="token-symbol">{self._escape_html(token['symbol'])}</span>
                    </div>
                </div>
                <div class="token-balance">{token['balance']}</div>
                <div class="token-usd-value">{usd_display}</div>
                <div class="token-details">
                    <div class="detail-item">
                        <div class="detail-label"><i class="fas fa-network-wired"></i> Network</div>
                        <div class="detail-value">{token['network'].title()}</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label"><i class="fas fa-file-contract"></i> Contract</div>
                        <div class="detail-value copy-address" onclick="copyToClipboard('{token['contract_address']}')" title="Click to copy">
                            {self._truncate_address(token['contract_address'])}
                        </div>
                    </div>
                </div>
            </div>
            '''
        
        return f'''
        <div class="wallet-analysis">
            <h3><i class="fas fa-wallet"></i> Wallet Analysis</h3>
            <div class="wallet-address">
                <i class="fas fa-address-card"></i> {wallet_address}
            </div>
            
            <div class="summary-cards">
                <div class="summary-card">
                    <i class="fas fa-coins"></i>
                    <div class="summary-value">{token_count}</div>
                    <div class="summary-label">Total Tokens</div>
                </div>
                <div class="summary-card">
                    <i class="fas fa-dollar-sign"></i>
                    <div class="summary-value">${total_value:,.2f}</div>
                    <div class="summary-label">Estimated Value</div>
                </div>
            </div>
            
            <h4><i class="fas fa-list"></i> Token Holdings</h4>
            <div class="token-grid">
                {tokens_html if tokens_html else '<p>No tokens found in this wallet.</p>'}
            </div>
            
            <div class="wallet-actions">
                <button class="action-btn" onclick="sendMessage('Show transaction history for {wallet_address}')">
                    <i class="fas fa-history"></i> Transaction History
                </button>
                <button class="action-btn" onclick="sendMessage('Show NFT holdings for {wallet_address}')">
                    <i class="fas fa-images"></i> View NFTs
                </button>
                <button class="action-btn" onclick="sendMessage('Check risks for {wallet_address}')">
                    <i class="fas fa-shield-alt"></i> Security Analysis
                </button>
            </div>
        </div>
        '''

    def _truncate_address(self, address: str, length: int = 8) -> str:
        """Truncate blockchain address for display"""
        if not address or len(address) <= length + 8:
            return address
        return f"{address[:length]}...{address[-4:]}"

    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters"""
        if not text:
            return ""
        
        html_escape_table = {
            "&": "&amp;",
            '"': "&quot;",
            "'": "&#x27;",
            ">": "&gt;",
            "<": "&lt;",
        }
        
        return "".join(html_escape_table.get(c, c) for c in str(text))

    def format_token_data(self, token_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format individual token data"""
        return {
            'symbol': token_data.get('symbol', 'Unknown').upper(),
            'name': token_data.get('name', 'Unknown Token'),
            'balance': self._format_balance(token_data.get('balance', '0')),
            'usd_value': self._format_usd_value(token_data.get('usd_value', '0')),
            'contract_address': token_data.get('contract_address', ''),
            'network': token_data.get('network', 'ethereum').lower(),
            'decimals': token_data.get('decimals', 18),
            'logo_url': token_data.get('logo_url', ''),
            'price': token_data.get('price', '0'),
            'price_change_24h': token_data.get('price_change_24h', '0')
        }

    def calculate_portfolio_metrics(self, tokens: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate portfolio metrics"""
        total_value = 0.0
        total_tokens = len(tokens)
        token_distribution = {}
        
        for token in tokens:
            try:
                usd_value = float(token.get('usd_value', 0))
                total_value += usd_value
                
                symbol = token.get('symbol', 'Unknown')
                if symbol not in token_distribution:
                    token_distribution[symbol] = 0
                token_distribution[symbol] += usd_value
                
            except (ValueError, TypeError):
                continue
        
        # Calculate percentages
        for symbol in token_distribution:
            if total_value > 0:
                token_distribution[symbol] = (token_distribution[symbol] / total_value) * 100
        
        # Find largest holdings
        largest_holdings = sorted(
            token_distribution.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:5]
        
        return {
            'total_value': total_value,
            'total_tokens': total_tokens,
            'largest_holdings': largest_holdings,
            'diversity_score': min(10, total_tokens / 2),  # Simple diversity metric
        }

    def validate_transaction_data(self, tx_data: Dict[str, Any]) -> bool:
        """Validate transaction data"""
        required_fields = ['hash', 'from', 'to', 'value']
        return all(field in tx_data for field in required_fields)

    def format_network_name(self, network_id: int) -> str:
        """Format network name from chain ID"""
        network_names = {
            1: 'Ethereum',
            137: 'Polygon',
            56: 'BSC',
            42161: 'Arbitrum',
            10: 'Optimism'
        }
        return network_names.get(network_id, f'Chain {network_id}')

    def detect_wallet_type(self, address: str, transaction_count: int = 0, balance: float = 0) -> str:
        """Detect wallet type based on patterns"""
        if transaction_count > 10000:
            return "High Activity Wallet"
        elif balance > 100000:
            return "Whale Wallet"
        elif transaction_count > 1000:
            return "Active Trader"
        elif transaction_count > 100:
            return "Regular User"
        elif transaction_count > 10:
            return "Casual User"
        elif transaction_count > 0:
            return "New User"
        else:
            return "Inactive Wallet"

    def calculate_risk_score(self, wallet_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate basic risk score"""
        risk_score = 0
        risk_factors = []
        
        # Transaction volume risk
        tx_count = wallet_data.get('transaction_count', 0)
        if tx_count > 10000:
            risk_score += 2
            risk_factors.append("Very high transaction volume")
        elif tx_count > 1000:
            risk_score += 1
            risk_factors.append("High transaction volume")
        
        # Balance risk
        balance = wallet_data.get('total_balance', 0)
        if balance > 1000000:
            risk_score += 3
            risk_factors.append("Very large balance - whale wallet")
        elif balance > 100000:
            risk_score += 2
            risk_factors.append("Large balance")
        
        # Token diversity
        token_count = wallet_data.get('token_count', 0)
        if token_count > 100:
            risk_score += 1
            risk_factors.append("Many different tokens")
        
        return {
            'risk_score': min(risk_score, 10),
            'risk_level': self._get_risk_level(risk_score),
            'risk_factors': risk_factors
        }

    def _get_risk_level(self, score: int) -> str:
        """Convert risk score to level"""
        if score <= 2:
            return "Low"
        elif score <= 5:
            return "Medium"
        elif score <= 7:
            return "High"
        else:
            return "Very High"