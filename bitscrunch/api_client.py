import requests
from typing import Dict, Any, List, Optional
from .schemas import WalletBalanceResponse
from config import settings
import logging

# Set up logging to see API responses
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BitsCrunchAPIClient:
    def __init__(self):
        self.base_url = "https://api.unleashnfts.com/api/v1"
        self.api_key = settings.bitscrunch_api_key
        self.headers = {
            "Accept": "application/json",
            "x-api-key": self.api_key
        }

    def get_wallet_balance(self, address: str, offset: int = 0, limit: int = 10) -> WalletBalanceResponse:
        """Get real wallet balance data"""
        try:
            endpoint = f"{self.base_url}/wallet/balance/token"
            params = {
                "address": address,
                "offset": offset,
                "limit": limit
            }
            
            logger.info(f"Calling BitsCrunch API: {endpoint}")
            logger.info(f"Parameters: {params}")
            logger.info(f"Headers: {self.headers}")
            
            response = requests.get(endpoint, headers=self.headers, params=params)
            
            logger.info(f"Response Status: {response.status_code}")
            logger.info(f"Response: {response.text}")
            
            response.raise_for_status()
            return WalletBalanceResponse(**response.json())
            
        except Exception as e:
            logger.error(f"Error getting wallet balance: {str(e)}")
            # Return empty response instead of mock data
            return WalletBalanceResponse(data=[], total_count=0)

    def get_nft_holdings(self, address: str) -> Dict[str, Any]:
        """Get real NFT holdings"""
        try:
            # Try multiple possible endpoints for NFTs
            endpoints_to_try = [
                f"{self.base_url}/wallet/nft",
                f"{self.base_url}/wallet/nfts", 
                f"{self.base_url}/nft/wallet/{address}",
                f"{self.base_url}/wallet/{address}/nfts"
            ]
            
            for endpoint in endpoints_to_try:
                try:
                    params = {"address": address} if "wallet" in endpoint else {}
                    url = endpoint if params else endpoint
                    
                    logger.info(f"Trying NFT endpoint: {url}")
                    response = requests.get(url, headers=self.headers, params=params, timeout=10)
                    
                    logger.info(f"NFT Response Status: {response.status_code}")
                    logger.info(f"NFT Response: {response.text[:500]}...")
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Extract NFTs from different possible response structures
                        nfts = []
                        if 'data' in data:
                            if isinstance(data['data'], list):
                                nfts = data['data']
                            elif isinstance(data['data'], dict) and 'nfts' in data['data']:
                                nfts = data['data']['nfts']
                            elif isinstance(data['data'], dict) and 'tokens' in data['data']:
                                nfts = data['data']['tokens']
                        elif 'nfts' in data:
                            nfts = data['nfts']
                        elif isinstance(data, list):
                            nfts = data
                        
                        return {
                            'nfts': nfts,
                            'total_count': len(nfts),
                            'address': address
                        }
                        
                except requests.exceptions.RequestException as e:
                    logger.warning(f"NFT endpoint {endpoint} failed: {str(e)}")
                    continue
            
            # If all endpoints fail, return empty result
            logger.warning("All NFT endpoints failed")
            return {
                'nfts': [],
                'total_count': 0,
                'address': address
            }
            
        except Exception as e:
            logger.error(f"Error getting NFT holdings: {str(e)}")
            return {
                'nfts': [],
                'total_count': 0,
                'address': address
            }

    def get_transaction_history(self, address: str) -> Dict[str, Any]:
        """Get real transaction history"""
        try:
            # Try multiple possible endpoints for transactions
            endpoints_to_try = [
                f"{self.base_url}/wallet/transactions",
                f"{self.base_url}/wallet/history",
                f"{self.base_url}/transactions/{address}",
                f"{self.base_url}/wallet/{address}/transactions"
            ]
            
            for endpoint in endpoints_to_try:
                try:
                    params = {"address": address} if "wallet" in endpoint else {}
                    url = endpoint if params else endpoint
                    
                    logger.info(f"Trying transaction endpoint: {url}")
                    response = requests.get(url, headers=self.headers, params=params, timeout=10)
                    
                    logger.info(f"Transaction Response Status: {response.status_code}")
                    logger.info(f"Transaction Response: {response.text[:500]}...")
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Extract transactions from different possible response structures
                        transactions = []
                        if 'data' in data:
                            if isinstance(data['data'], list):
                                transactions = data['data']
                            elif isinstance(data['data'], dict) and 'transactions' in data['data']:
                                transactions = data['data']['transactions']
                        elif 'transactions' in data:
                            transactions = data['transactions']
                        elif isinstance(data, list):
                            transactions = data
                        
                        return {
                            'transactions': transactions,
                            'total_count': len(transactions),
                            'address': address
                        }
                        
                except requests.exceptions.RequestException as e:
                    logger.warning(f"Transaction endpoint {endpoint} failed: {str(e)}")
                    continue
            
            # If all endpoints fail, return empty result
            logger.warning("All transaction endpoints failed")
            return {
                'transactions': [],
                'total_count': 0,
                'address': address
            }
            
        except Exception as e:
            logger.error(f"Error getting transaction history: {str(e)}")
            return {
                'transactions': [],
                'total_count': 0,
                'address': address
            }

    def get_risk_assessment(self, address: str) -> Dict[str, Any]:
        """Get risk assessment - try real API first"""
        try:
            endpoints_to_try = [
                f"{self.base_url}/wallet/risk",
                f"{self.base_url}/security/{address}",
                f"{self.base_url}/wallet/{address}/risk"
            ]
            
            for endpoint in endpoints_to_try:
                try:
                    params = {"address": address} if "wallet" in endpoint else {}
                    url = endpoint if params else endpoint
                    
                    response = requests.get(url, headers=self.headers, params=params, timeout=10)
                    
                    if response.status_code == 200:
                        return response.json()
                        
                except requests.exceptions.RequestException:
                    continue
            
            # Return basic assessment if API fails
            return {
                'overall_risk_score': 1.0,
                'risk_level': 'Low',
                'factors': [
                    {
                        'name': 'API Analysis Unavailable',
                        'risk_level': 1,
                        'description': 'Unable to fetch detailed risk analysis from API'
                    }
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting risk assessment: {str(e)}")
            return {
                'overall_risk_score': 0,
                'risk_level': 'Unknown',
                'factors': []
            }

    def get_whale_analysis(self, address: str) -> Dict[str, Any]:
        """Get whale analysis - try real API first"""
        try:
            endpoints_to_try = [
                f"{self.base_url}/wallet/whale",
                f"{self.base_url}/analytics/{address}",
                f"{self.base_url}/wallet/{address}/analytics"
            ]
            
            for endpoint in endpoints_to_try:
                try:
                    params = {"address": address} if "wallet" in endpoint else {}
                    url = endpoint if params else endpoint
                    
                    response = requests.get(url, headers=self.headers, params=params, timeout=10)
                    
                    if response.status_code == 200:
                        return response.json()
                        
                except requests.exceptions.RequestException:
                    continue
            
            # Return basic analysis if API fails
            return {
                'total_value': 0.0,
                'diversity_score': 0,
                'activity_level': 'Unknown',
                'is_whale': False
            }
            
        except Exception as e:
            logger.error(f"Error getting whale analysis: {str(e)}")
            return {
                'total_value': 0.0,
                'diversity_score': 0,
                'activity_level': 'Unknown',
                'is_whale': False
            }

    def verify_contract(self, address: str) -> Dict[str, Any]:
        """Verify contract - try real API first"""
        try:
            endpoints_to_try = [
                f"{self.base_url}/contract/verify",
                f"{self.base_url}/security/contract/{address}",
                f"{self.base_url}/contract/{address}/verify"
            ]
            
            for endpoint in endpoints_to_try:
                try:
                    params = {"address": address} if "contract/verify" in endpoint else {}
                    url = endpoint if params else endpoint
                    
                    response = requests.get(url, headers=self.headers, params=params, timeout=10)
                    
                    if response.status_code == 200:
                        return response.json()
                        
                except requests.exceptions.RequestException:
                    continue
            
            # Return basic verification if API fails
            return {
                'status': 'Unknown',
                'verified': False,
                'audit_status': 'Not Available'
            }
            
        except Exception as e:
            logger.error(f"Error verifying contract: {str(e)}")
            return {
                'status': 'Error',
                'verified': False,
                'audit_status': 'Error'
            }

    def test_api_connection(self) -> Dict[str, Any]:
        """Test API connection and key"""
        try:
            # Test with a simple endpoint
            test_endpoints = [
                f"{self.base_url}/health",
                f"{self.base_url}/status", 
                f"{self.base_url}/wallet/balance/token"
            ]
            
            for endpoint in test_endpoints:
                try:
                    params = {"address": "0x0000000000000000000000000000000000000000"} if "wallet" in endpoint else {}
                    response = requests.get(endpoint, headers=self.headers, params=params, timeout=5)
                    
                    logger.info(f"API Test - Endpoint: {endpoint}")
                    logger.info(f"API Test - Status: {response.status_code}")
                    logger.info(f"API Test - Response: {response.text[:200]}...")
                    
                    return {
                        'status': 'connected',
                        'endpoint': endpoint,
                        'status_code': response.status_code,
                        'response': response.text[:200]
                    }
                    
                except Exception as e:
                    logger.warning(f"Test endpoint {endpoint} failed: {str(e)}")
                    continue
            
            return {
                'status': 'failed',
                'error': 'All test endpoints failed'
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }