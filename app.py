from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from services.chat_service import ChatService
from bitscrunch.api_client import BitsCrunchAPIClient
import uvicorn
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

chat_service = ChatService()

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/verify/{address}")
async def verify_wallet_data(address: str):
    """Verify wallet data across multiple sources"""
    try:
        client = BitsCrunchAPIClient()
        
        # Get BitsCrunch data
        bitscrunch_data = client.get_wallet_balance(address)
        
        # Also try to get data from other sources for comparison
        verification_data = {
            "wallet_address": address,
            "bitscrunch_api": {
                "status": "success",
                "token_count": len(bitscrunch_data.token) if hasattr(bitscrunch_data, 'token') else 0,
                "tokens": []
            },
            "polygonscan_link": f"https://polygonscan.com/address/{address}",
            "etherscan_link": f"https://etherscan.io/address/{address}",
            "raw_bitscrunch_response": str(bitscrunch_data)[:1000]
        }
        
        # Extract token details
        if hasattr(bitscrunch_data, 'token') and bitscrunch_data.token:
            for token in bitscrunch_data.token:
                verification_data["bitscrunch_api"]["tokens"].append({
                    "name": token.token_name,
                    "symbol": token.token_symbol,
                    "quantity": float(token.quantity),
                    "network": token.blockchain,
                    "contract": token.token_address,
                    "decimals": token.decimal
                })
        
        # Try Moralis API for comparison (if you have a key)
        try:
            import requests
            # This is a free endpoint that might work
            moralis_url = f"https://deep-index.moralis.io/api/v2/{address}/erc20"
            moralis_headers = {
                "X-API-Key": "demo"  # Replace with real key if you have one
            }
            moralis_response = requests.get(moralis_url, headers=moralis_headers, timeout=5)
            
            if moralis_response.status_code == 200:
                verification_data["moralis_comparison"] = {
                    "status": "success",
                    "data": moralis_response.json()
                }
            else:
                verification_data["moralis_comparison"] = {
                    "status": "failed",
                    "error": f"Status: {moralis_response.status_code}"
                }
        except:
            verification_data["moralis_comparison"] = {
                "status": "not_available",
                "error": "Moralis API not accessible"
            }
        
        # Add manual verification steps
        verification_data["manual_verification_steps"] = [
            f"1. Visit PolygonScan: https://polygonscan.com/address/{address}",
            f"2. Visit Etherscan: https://etherscan.io/address/{address}",
            "3. Check if token quantities match",
            "4. Compare contract addresses",
            "5. Verify network information"
        ]
        
        return JSONResponse(verification_data)
        
    except Exception as e:
        return JSONResponse({
            "error": str(e),
            "wallet_address": address,
            "manual_verification": f"Check manually at: https://polygonscan.com/address/{address}"
        })

@app.post("/chat")
async def chat(message: str = Form(...)):
    try:
        logger.info(f"Received message: {message}")
        response = chat_service.generate_response(message)
        logger.info(f"Generated response: {str(response)[:200]}...")
        return JSONResponse(content=response)
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "html": f"""
                <div class="message bot-message">
                    <div class="message-content error">
                        <i class="fas fa-exclamation-triangle"></i>
                        <p>Error: {str(e)}</p>
                    </div>
                </div>
                """
            }
        )

# Add debug endpoint to test API
@app.get("/debug/api/{address}")
async def debug_api(address: str):
    """Debug endpoint to test BitsCrunch API"""
    try:
        client = BitsCrunchAPIClient()
        
        # Test API connection
        connection_test = client.test_api_connection()
        
        # Test wallet balance
        try:
            balance_response = client.get_wallet_balance(address)
            balance_data = {
                "status": "success",
                "data": str(balance_response)[:500]
            }
        except Exception as e:
            balance_data = {
                "status": "error", 
                "error": str(e)
            }
        
        # Test NFT holdings
        try:
            nft_response = client.get_nft_holdings(address)
            nft_data = {
                "status": "success",
                "count": len(nft_response.get('nfts', [])),
                "data": str(nft_response)[:500]
            }
        except Exception as e:
            nft_data = {
                "status": "error",
                "error": str(e)
            }
        
        return JSONResponse({
            "wallet_address": address,
            "api_connection": connection_test,
            "wallet_balance": balance_data,
            "nft_holdings": nft_data,
            "api_key_configured": bool(client.api_key),
            "api_key_length": len(client.api_key) if client.api_key else 0
        })
        
    except Exception as e:
        return JSONResponse({
            "error": str(e),
            "wallet_address": address
        })

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)