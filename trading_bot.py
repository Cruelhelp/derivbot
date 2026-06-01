import os
import json
import asyncio
import websockets
from datetime import datetime
from dotenv import load_dotenv
import random

# Load environment variables
load_dotenv()
DERIV_TOKEN = os.getenv('DERIV_TOKEN')
DEMO_MODE = os.getenv('DEMO_MODE', 'True').lower() == 'true'  # Set to False for real trading

class DerivTradingBot:
    def __init__(self, token):
        self.token = token
        self.uri = "wss://ws.deriv.com/websockets/v3"
        self.websocket = None
        self.balance = 0
        self.request_id = 0

    async def connect(self):
        """Connect to Deriv WebSocket API"""
        try:
            if DEMO_MODE:
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Connected to Deriv API (DEMO MODE)")
                self.balance = 10000  # Demo balance
                print(f"Account Balance: ${self.balance} (Demo)")
                return True
            
            self.websocket = await websockets.connect(self.uri)
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Connected to Deriv API")
            
            # Authorize with token
            auth_message = {
                "authorize": self.token
            }
            await self.websocket.send(json.dumps(auth_message))
            response = await self.websocket.recv()
            auth_response = json.loads(response)
            
            if "authorize" in auth_response:
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Authorized successfully")
                self.balance = auth_response["authorize"].get("balance", 0)
                print(f"Account Balance: ${self.balance}")
            else:
                print("Authorization failed:", auth_response)
                return False
            
            return True
        except Exception as e:
            print(f"Connection error: {e}")
            if DEMO_MODE:
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Falling back to DEMO MODE")
                self.balance = 10000
                print(f"Account Balance: ${self.balance} (Demo)")
                return True
            return False

    async def get_tick(self, symbol):
        """Get current price of a symbol"""
        self.request_id += 1
        
        if DEMO_MODE:
            # Generate fake tick data for demo
            base_prices = {
                "frxEURUSD": 1.0850,
                "frxGBPUSD": 1.2650,
                "frxUSDJPY": 150.50
            }
            base_price = base_prices.get(symbol, 1.0)
            # Add random movement
            price = base_price + random.uniform(-0.01, 0.01)
            return {
                "tick": {
                    "symbol": symbol,
                    "quote": price,
                    "epoch": int(datetime.now().timestamp())
                }
            }
        
        message = {
            "ticks": symbol,
            "subscribe": 1,
            "req_id": self.request_id
        }
        try:
            await self.websocket.send(json.dumps(message))
            response = await asyncio.wait_for(self.websocket.recv(), timeout=5)
            return json.loads(response)
        except Exception as e:
            print(f"Error getting tick for {symbol}: {e}")
            return None

    async def place_trade(self, symbol, amount, direction, duration):
        """Place a trade on Deriv"""
        self.request_id += 1
        
        if DEMO_MODE:
            # Simulate a trade in demo mode
            trade_id = f"DEMO-{self.request_id}-{int(datetime.now().timestamp())}"
            entry_price = random.uniform(1.0, 1.2)
            result = random.choice([True, False])  # 50% win rate for demo
            pnl = amount if result else -amount
            
            demo_response = {
                "buy": {
                    "contract_id": trade_id,
                    "payout": amount * 2 if result else amount * 0.5,
                    "status": "purchased"
                }
            }
            print(f"[DEMO] Trade placed: {trade_id}")
            print(f"[DEMO] Entry Price: {entry_price:.4f}")
            print(f"[DEMO] Result: {'WIN' if result else 'LOSS'} | P&L: ${pnl}")
            self.balance += pnl
            print(f"[DEMO] New Balance: ${self.balance}")
            return demo_response
        
        message = {
            "buy": 1,
            "subscribe": 1,
            "req_id": self.request_id,
            "contract_type": direction,  # "CALL" or "PUT"
            "currency": "USD",
            "duration": duration,
            "duration_unit": "m",  # minutes
            "symbol": symbol,
            "amount": amount,
            "basis": "stake"
        }
        try:
            await self.websocket.send(json.dumps(message))
            response = await asyncio.wait_for(self.websocket.recv(), timeout=5)
            trade_response = json.loads(response)
            print(f"Trade placed: {trade_response}")
            return trade_response
        except Exception as e:
            print(f"Error placing trade: {e}")
            return None

    async def simple_strategy(self):
        """Simple automated trading strategy"""
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting trading strategy...")
        
        # Example: Trade EUR/USD with CALL direction, $10 stake, 5 minute duration
        symbol = "frxEURUSD"  # EUR/USD
        amount = 10  # $10
        direction = "CALL"  # You can also use "PUT"
        duration = 5  # 5 minutes
        
        # Get current price
        tick = await self.get_tick(symbol)
        if tick:
            if "tick" in tick:
                print(f"Current price: {tick['tick']['quote']:.4f}")
            else:
                print(f"Tick data: {tick}")
        
        # Place trade
        print(f"\nPlacing {direction} trade on {symbol}...")
        trade = await self.place_trade(symbol, amount, direction, duration)
        
        # Simulate running multiple trades in demo mode
        if DEMO_MODE:
            print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Running 5 more demo trades...")
            for i in range(5):
                await asyncio.sleep(1)
                direction = random.choice(["CALL", "PUT"])
                amount = random.randint(5, 25)
                trade = await self.place_trade(symbol, amount, direction, duration)
        
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Strategy execution completed")

    async def disconnect(self):
        """Close WebSocket connection"""
        if DEMO_MODE:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Demo mode ended | Final Balance: ${self.balance}")
        elif self.websocket:
            await self.websocket.close()
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Disconnected from Deriv API")

    async def run(self):
        """Main execution method"""
        if not self.token:
            print("Error: DERIV_TOKEN not found in .env file")
            return
        
        if await self.connect():
            try:
                await self.simple_strategy()
            finally:
                await self.disconnect()


async def main():
    bot = DerivTradingBot(DERIV_TOKEN)
    await bot.run()


if __name__ == "__main__":
    print("Deriv Automated Trading Bot")
    print("=" * 50)
    asyncio.run(main())
