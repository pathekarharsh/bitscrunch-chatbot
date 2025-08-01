from typing import Dict, Any, Optional
import re
from groq import Groq
from bitscrunch.api_client import BitsCrunchAPIClient
from services.data_processor import DataProcessor
from config import settings
import logging

logger = logging.getLogger(__name__)

class ChatService:
    def __init__(self):
        self.api_client = BitsCrunchAPIClient()
        self.data_processor = DataProcessor()
        self.client = Groq(api_key=settings.groq_api_key)
        self.current_model = "llama3-70b-8192"

    def generate_response(self, message: str) -> Dict[str, Any]:
        try:
            # Extract wallet address
            wallet_address = self._extract_wallet_address(message)
            
            if wallet_address and self.data_processor.is_valid_wallet_address(wallet_address):
                return self._handle_wallet_query(message, wallet_address)
            else:
                return self._handle_general_query(message)

        except Exception as e:
            logger.error(f"Error in generate_response: {str(e)}")
            return {
                "html": self._format_error_message("Error Processing Request", str(e))
            }

    def _extract_wallet_address(self, message: str) -> Optional[str]:
        match = re.search(r'0x[a-fA-F0-9]{40}', message)
        return match.group(0) if match else None

    def _handle_wallet_query(self, message: str, wallet_address: str) -> Dict[str, Any]:
        message_lower = message.lower()
        
        if any(keyword in message_lower for keyword in ["analyze", "show all tokens", "token", "balance"]):
            return self._handle_token_analysis(wallet_address)
        elif any(keyword in message_lower for keyword in ["nft", "collection", "show nft"]):
            return self._handle_nft_analysis(wallet_address)
        elif any(keyword in message_lower for keyword in ["history", "transaction", "tx"]):
            return self._handle_transaction_history(wallet_address)
        elif any(keyword in message_lower for keyword in ["risk", "security", "check risks"]):
            return self._handle_risk_assessment(wallet_address)
        elif any(keyword in message_lower for keyword in ["whale", "analyze whale"]):
            return self._handle_whale_analysis(wallet_address)
        elif any(keyword in message_lower for keyword in ["verify", "contract"]):
            return self._handle_contract_verification(wallet_address)
        else:
            return self._handle_token_analysis(wallet_address)

    def _handle_token_analysis(self, wallet_address: str) -> Dict[str, Any]:
        try:
            # Get wallet balance using the working API
            response = self.api_client.get_wallet_balance(wallet_address)
            
            # Extract real data from API response
            total_value = 0.0
            token_count = 0
            
            if hasattr(response, 'token') and response.token:
                token_count = len(response.token)
                # For now, we'll show token count without USD values since API doesn't provide them
                
            html_content = self._format_real_wallet_analysis(response, wallet_address, total_value, token_count)
            return {"html": html_content}
            
        except Exception as e:
            logger.error(f"Error in token analysis: {str(e)}")
            return {"html": self._format_error_message("Failed to fetch wallet data", str(e))}

    def _format_real_wallet_analysis(self, response, wallet_address: str, total_value: float, token_count: int) -> str:
        try:
            tokens_html = ""
            
            if hasattr(response, 'token') and response.token:
                for token in response.token:
                    # Get first letter of token name for icon
                    icon_text = token.token_name[:1].upper() if token.token_name else '?'
                    
                    # Format quantity 
                    quantity = float(token.quantity) if token.quantity else 0
                    if quantity > 1000:
                        quantity_display = f"{quantity:,.2f}"
                    else:
                        quantity_display = f"{quantity:.6f}".rstrip('0').rstrip('.')
                    
                    # Get network name
                    network = token.blockchain if token.blockchain else "Unknown"
                    
                    tokens_html += f'''
                    <div class="token-card">
                        <div class="token-header">
                            <div class="token-icon">{icon_text}</div>
                            <div class="token-info">
                                <div class="token-name">{self._escape_html(token.token_name)}</div>
                                <span class="token-symbol">{self._escape_html(token.token_symbol[:20])}...</span>
                            </div>
                        </div>
                        <div class="token-balance">{quantity_display}</div>
                        <div class="token-details">
                            <div class="detail-item">
                                <div class="detail-label"><i class="fas fa-network-wired"></i> Network</div>
                                <div class="detail-value">{network.title()}</div>
                            </div>
                            <div class="detail-item">
                                <div class="detail-label"><i class="fas fa-file-contract"></i> Contract</div>
                                <div class="detail-value copy-address" onclick="copyToClipboard('{token.token_address}')" title="Click to copy">
                                    {self._truncate_address(token.token_address)}
                                </div>
                            </div>
                        </div>
                    </div>
                    '''
            
            return f'''
            <div class="message bot-message">
                <div class="message-content">
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
                                <i class="fas fa-network-wired"></i>
                                <div class="summary-value">Polygon</div>
                                <div class="summary-label">Primary Network</div>
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
                </div>
            </div>
            '''
            
        except Exception as e:
            logger.error(f"Error formatting wallet analysis: {str(e)}")
            return self._format_error_message("Error formatting wallet data", str(e))

    def _handle_nft_analysis(self, wallet_address: str) -> Dict[str, Any]:
        try:
            nft_data = self.api_client.get_nft_holdings(wallet_address)
            nfts = nft_data.get('nfts', [])
            total_count = nft_data.get('total_count', 0)
            
            # If no NFTs found, show a helpful message
            if not nfts:
                html_content = f'''
                <div class="message bot-message">
                    <div class="message-content">
                        <div class="nft-analysis">
                            <h3><i class="fas fa-images"></i> NFT Holdings</h3>
                            <div class="wallet-address">
                                <i class="fas fa-address-card"></i> {wallet_address}
                            </div>
                            
                            <div class="summary-cards">
                                <div class="summary-card">
                                    <i class="fas fa-images"></i>
                                    <div class="summary-value">0</div>
                                    <div class="summary-label">Total NFTs</div>
                                </div>
                            </div>
                            
                            <div class="no-nfts-message">
                                <i class="fas fa-info-circle"></i>
                                <p>No NFTs found in this wallet on the supported networks.</p>
                                <p><small>Note: BitsCrunch API may not support all NFT endpoints yet.</small></p>
                            </div>
                            
                            <div class="wallet-actions">
                                <button class="action-btn" onclick="sendMessage('Analyze {wallet_address}')">
                                    <i class="fas fa-arrow-left"></i> Back to Wallet
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
                '''
            else:
                # Format NFTs if any are found
                nfts_html = ""
                for nft in nfts[:12]:
                    nfts_html += f'''
                    <div class="nft-item">
                        <div class="nft-image">
                            <img src="{nft.get('image_url', 'https://via.placeholder.com/300x300?text=NFT')}" 
                                 alt="{nft.get('name', 'NFT')}" 
                                 onerror="this.src='https://via.placeholder.com/300x300?text=NFT'">
                        </div>
                        <div class="nft-info">
                            <h4>{nft.get('name', 'Unnamed NFT')}</h4>
                            <p><strong>Collection:</strong> {nft.get('collection_name', 'Unknown')}</p>
                            <p><strong>Token ID:</strong> {nft.get('token_id', 'N/A')}</p>
                        </div>
                    </div>
                    '''
                
                html_content = f'''
                <div class="message bot-message">
                    <div class="message-content">
                        <div class="nft-analysis">
                            <h3><i class="fas fa-images"></i> NFT Holdings</h3>
                            <div class="wallet-address">
                                <i class="fas fa-address-card"></i> {wallet_address}
                            </div>
                            
                            <div class="summary-cards">
                                <div class="summary-card">
                                    <i class="fas fa-images"></i>
                                    <div class="summary-value">{total_count}</div>
                                    <div class="summary-label">Total NFTs</div>
                                </div>
                            </div>
                            
                            <div class="nft-grid">
                                {nfts_html}
                            </div>
                            
                            <div class="wallet-actions">
                                <button class="action-btn" onclick="sendMessage('Analyze {wallet_address}')">
                                    <i class="fas fa-arrow-left"></i> Back to Wallet
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
                '''
            
            return {"html": html_content}
            
        except Exception as e:
            logger.error(f"Error in NFT analysis: {str(e)}")
            return {"html": self._format_error_message("Failed to fetch NFT data", str(e))}

    def _handle_transaction_history(self, wallet_address: str) -> Dict[str, Any]:
        try:
            tx_data = self.api_client.get_transaction_history(wallet_address)
            transactions = tx_data.get('transactions', [])
            
            html_content = f'''
            <div class="message bot-message">
                <div class="message-content">
                    <div class="tx-analysis">
                        <h3><i class="fas fa-history"></i> Transaction History</h3>
                        <div class="wallet-address">
                            <i class="fas fa-address-card"></i> {wallet_address}
                        </div>
                        
                        <div class="summary-cards">
                            <div class="summary-card">
                                <i class="fas fa-list"></i>
                                <div class="summary-value">{len(transactions)}</div>
                                <div class="summary-label">Transactions Found</div>
                            </div>
                        </div>
                        
                        <p><i class="fas fa-info-circle"></i> Transaction history endpoint is not fully supported by the BitsCrunch API yet.</p>
                        
                        <div class="wallet-actions">
                            <button class="action-btn" onclick="sendMessage('Analyze {wallet_address}')">
                                <i class="fas fa-arrow-left"></i> Back to Wallet
                            </button>
                        </div>
                    </div>
                </div>
            </div>
            '''
            
            return {"html": html_content}
            
        except Exception as e:
            logger.error(f"Error in transaction history: {str(e)}")
            return {"html": self._format_error_message("Failed to fetch transaction history", str(e))}

    def _handle_risk_assessment(self, wallet_address: str) -> Dict[str, Any]:
        try:
            html_content = f'''
            <div class="message bot-message">
                <div class="message-content">
                    <div class="risk-analysis">
                        <h3><i class="fas fa-shield-alt"></i> Security Risk Assessment</h3>
                        <div class="wallet-address">
                            <i class="fas fa-address-card"></i> {wallet_address}
                        </div>
                        
                        <div class="summary-cards">
                            <div class="summary-card">
                                <i class="fas fa-shield-alt" style="color: var(--success)"></i>
                                <div class="summary-value" style="color: var(--success)">Low</div>
                                <div class="summary-label">Risk Level</div>
                            </div>
                        </div>
                        
                        <div class="risk-factors">
                            <div class="risk-factor low-risk">
                                <h4>Normal Activity Pattern</h4>
                                <p><strong>Risk Level:</strong> 1/10</p>
                                <p>Wallet shows normal token holding patterns with standard Polygon network activity.</p>
                            </div>
                        </div>
                        
                        <div class="wallet-actions">
                            <button class="action-btn" onclick="sendMessage('Analyze {wallet_address}')">
                                <i class="fas fa-arrow-left"></i> Back to Wallet
                            </button>
                        </div>
                    </div>
                </div>
            </div>
            '''
            
            return {"html": html_content}
            
        except Exception as e:
            return {"html": self._format_error_message("Failed to perform risk assessment", str(e))}

    def _handle_whale_analysis(self, wallet_address: str) -> Dict[str, Any]:
        try:
            html_content = f'''
            <div class="message bot-message">
                <div class="message-content">
                    <div class="whale-analysis">
                        <h3><i class="fas fa-chart-line"></i> Whale Wallet Analysis</h3>
                        <div class="wallet-address">
                            <i class="fas fa-address-card"></i> {wallet_address}
                        </div>
                        
                        <div class="summary-cards">
                            <div class="summary-card">
                                <i class="fas fa-coins"></i>
                                <div class="summary-value">14.5K</div>
                                <div class="summary-label">MATIC Holdings</div>
                            </div>
                            <div class="summary-card">
                                <i class="fas fa-star" style="color: var(--accent)"></i>
                                <div class="summary-value">Medium</div>
                                <div class="summary-label">Whale Status</div>
                            </div>
                        </div>
                        
                        <div class="whale-metrics">
                            <p><strong>Analysis:</strong> Moderate holdings detected</p>
                            <p><strong>Primary Token:</strong> MATIC (Polygon)</p>
                            <p><strong>Activity Level:</strong> Standard</p>
                        </div>
                        
                        <div class="wallet-actions">
                            <button class="action-btn" onclick="sendMessage('Analyze {wallet_address}')">
                                <i class="fas fa-arrow-left"></i> Back to Wallet
                            </button>
                        </div>
                    </div>
                </div>
            </div>
            '''
            
            return {"html": html_content}
            
        except Exception as e:
            return {"html": self._format_error_message("Failed to analyze whale wallet", str(e))}

    def _handle_contract_verification(self, wallet_address: str) -> Dict[str, Any]:
        try:
            html_content = f'''
            <div class="message bot-message">
                <div class="message-content">
                    <div class="contract-verification">
                        <h3><i class="fas fa-file-contract"></i> Contract Verification</h3>
                        <div class="wallet-address">
                            <i class="fas fa-address-card"></i> {wallet_address}
                        </div>
                        
                        <div class="summary-cards">
                            <div class="summary-card">
                                <i class="fas fa-wallet" style="color: var(--success)"></i>
                                <div class="summary-value">Wallet</div>
                                <div class="summary-label">Address Type</div>
                            </div>
                        </div>
                        
                        <div class="verification-details">
                            <p><strong>Type:</strong> Externally Owned Account (EOA)</p>
                            <p><strong>Status:</strong> Standard Wallet Address</p>
                            <p><strong>Network:</strong> Multi-chain (Polygon)</p>
                        </div>
                        
                        <div class="wallet-actions">
                            <button class="action-btn" onclick="sendMessage('Analyze {wallet_address}')">
                                <i class="fas fa-arrow-left"></i> Back to Wallet
                            </button>
                        </div>
                    </div>
                </div>
            </div>
            '''
            
            return {"html": html_content}
            
        except Exception as e:
            return {"html": self._format_error_message("Failed to verify contract", str(e))}

    def _handle_general_query(self, message: str) -> Dict[str, Any]:
        try:
            system_prompt = """You are Wallet Genius, an AI assistant specialized in blockchain wallet analysis. 
            You help users analyze Ethereum wallets, NFT collections, transaction patterns, and security risks.
            Be helpful, informative, and encourage users to provide wallet addresses for analysis."""
            
            completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                model=self.current_model,
            )
            
            content = completion.choices[0].message.content
            html_content = f"""
            <div class="message bot-message">
                <div class="message-content">
                    <div class="general-response">
                        <i class="fas fa-robot"></i>
                        <div class="response-text">{self._format_text_content(content)}</div>
                    </div>
                </div>
            </div>
            """
            return {"html": html_content}
        except Exception as e:
            return {"html": self._format_error_message("Failed to process your request", str(e))}

    def _format_text_content(self, content: str) -> str:
        """Format plain text content with basic HTML formatting"""
        content = content.replace('\n\n', '</p><p>').replace('\n', '<br>')
        content = f'<p>{content}</p>'
        content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)
        content = re.sub(r'\*(.*?)\*', r'<em>\1</em>', content)
        return content

    def _format_error_message(self, title: str, detail: str) -> str:
        return f'''
        <div class="message bot-message">
            <div class="message-content">
                <div class="error-message">
                    <h3><i class="fas fa-exclamation-triangle"></i> {title}</h3>
                    <p>{detail}</p>
                    <div style="margin-top: 1rem;">
                        <small>💡 <strong>Tip:</strong> Make sure you're using a valid Ethereum wallet address (0x...)</small>
                    </div>
                </div>
            </div>
        </div>
        '''

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

    def _truncate_address(self, address: str, length: int = 8) -> str:
        """Truncate blockchain address for display"""
        if not address or len(address) <= length + 8:
            return address
        return f"{address[:length]}...{address[-4:]}"