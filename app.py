from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import threading
import json
import os
import asyncio
import websockets
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
DERIV_TOKEN = os.getenv('DERIV_TOKEN')

app = Flask(__name__)
CORS(app)

# Bot state
class BotState:
    def __init__(self):
        self.is_running = False
        self.real_balance = 0
        self.demo_balance = 0
        self.current_balance = 0  # Active account balance
        self.trade_history = []
        self.total_pnl = 0
        self.trades_count = 0
        self.wins = 0
        self.losses = 0
        self.websocket = None
        self.request_id = 0
        self.loop = None
        self.is_real_account = True

bot_state = BotState()


@app.route('/')
def index():
    return render_template('dashboard.html')


@app.route('/api/stats', methods=['GET'])
def get_stats():
    win_rate = 0
    if bot_state.trades_count > 0:
        win_rate = (bot_state.wins / bot_state.trades_count) * 100
    
    connection_status = "Connected" if bot_state.real_balance > 0 or bot_state.is_running else "Disconnected"
    
    return jsonify({
        'real_balance': bot_state.real_balance,
        'demo_balance': bot_state.demo_balance,
        'current_balance': bot_state.current_balance,
        'total_pnl': bot_state.total_pnl,
        'trades_count': bot_state.trades_count,
        'win_rate': round(win_rate, 1),
        'wins': bot_state.wins,
        'losses': bot_state.losses,
        'is_running': bot_state.is_running,
        'is_real_account': bot_state.is_real_account,
        'mode': 'LIVE' if bot_state.is_real_account else 'DEMO',
        'connection_status': connection_status
    })


@app.route('/api/trades', methods=['GET'])
def get_trades():
    return jsonify({
        'trades': bot_state.trade_history
    })


@app.route('/api/start', methods=['POST'])
def start_bot():
    if not bot_state.is_running:
        bot_state.is_running = True
        # Check if we can connect first
        bot_thread = threading.Thread(target=test_and_trade, daemon=True)
        bot_thread.start()
    return jsonify({'status': 'started'})


def test_and_trade():
    """Test connection first, then start trading"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(test_connection())
    finally:
        loop.close()


async def test_connection():
    """Test Deriv API connection"""
    uri = "wss://ws.deriv.com/websockets/v3"
    try:
        print("Testing connection to Deriv API...")
        async with websockets.connect(uri, ping_interval=20, ping_timeout=10) as websocket:
            auth_msg = {"authorize": DERIV_TOKEN}
            await websocket.send(json.dumps(auth_msg))
            auth_response = json.loads(await asyncio.wait_for(websocket.recv(), timeout=10))
            
            if "authorize" in auth_response:
                bot_state.real_balance = auth_response["authorize"].get("balance", 0)
                bot_state.current_balance = bot_state.real_balance
                print(f"✓ Connected! Real Balance: ${bot_state.real_balance}")
                
                # Now run trading
                await real_trading_loop(websocket)
            else:
                print(f"✗ Auth failed: {auth_response}")
                bot_state.is_running = False
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        print("Is your work firewall blocking Deriv? Switch to personal WiFi or use demo mode.")
        bot_state.is_running = False


@app.route('/api/stop', methods=['POST'])
def stop_bot():
    bot_state.is_running = False
    return jsonify({'status': 'stopped'})


@app.route('/api/clear', methods=['POST'])
def clear_history():
    bot_state.trade_history = []
    return jsonify({'status': 'cleared'})


@app.route('/api/reset', methods=['POST'])
def reset_stats():
    bot_state.current_balance = bot_state.real_balance if bot_state.is_real_account else bot_state.demo_balance
    bot_state.total_pnl = 0
    bot_state.trades_count = 0
    bot_state.wins = 0
    bot_state.losses = 0
    bot_state.trade_history = []
    return jsonify({'status': 'reset'})


@app.route('/api/export', methods=['POST'])
def export_trades():
    export_data = {
        'export_date': datetime.now().isoformat(),
        'final_balance': bot_state.balance,
        'total_pnl': bot_state.total_pnl,
        'total_trades': bot_state.trades_count,
        'trades': bot_state.trade_history
    }
    
    filename = f"trades_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    filepath = os.path.join(os.path.dirname(__file__), filename)
    
    with open(filepath, 'w') as f:
        json.dump(export_data, f, indent=2)
    
    return jsonify({'status': 'exported', 'filename': filename})


def trading_loop():
    """Main trading loop with real Deriv API"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(real_trading_loop())
    except Exception as e:
        print(f"Trading loop error: {e}")
    finally:
        loop.close()


async def real_trading_loop(websocket=None):
    """Real async trading loop"""
    uri = "wss://ws.deriv.com/websockets/v3"
    
    # If websocket provided, use it; otherwise create new
    if websocket is None:
        try:
            websocket = await websockets.connect(uri, ping_interval=20, ping_timeout=10)
        except Exception as e:
            print(f"Connection error: {e}")
            return
    
    try:
        # If we need to authorize (no websocket passed)
        if websocket is None:
            auth_msg = {"authorize": DERIV_TOKEN}
            await websocket.send(json.dumps(auth_msg))
            auth_response = json.loads(await websocket.recv())
            
            if "authorize" in auth_response:
                bot_state.real_balance = auth_response["authorize"].get("balance", 0)
                bot_state.current_balance = bot_state.real_balance
                print(f"Connected! Balance: ${bot_state.real_balance}")
            else:
                print("Authorization failed")
                return
        
        symbols = ["frxEURUSD", "frxGBPUSD", "frxUSDJPY"]
        
        while bot_state.is_running:
            try:
                import random
                symbol = random.choice(symbols)
                amount = random.randint(5, 25)
                direction = random.choice(["CALL", "PUT"])
                
                await execute_real_trade(websocket, symbol, amount, direction)
                
                # Wait before next trade
                await asyncio.sleep(5)
                
            except Exception as e:
                print(f"Trade error: {e}")
                await asyncio.sleep(2)
                
    except Exception as e:
        print(f"Trading loop error: {e}")
    finally:
        if websocket:
            await websocket.close()


async def execute_real_trade(websocket, symbol, amount, direction):
    """Execute a real trade on Deriv"""
    bot_state.request_id += 1
    trade_id = f"TRADE-{bot_state.trades_count + 1}"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        # Get tick
        bot_state.request_id += 1
        tick_msg = {
            "ticks": symbol,
            "subscribe": 0,
            "req_id": bot_state.request_id
        }
        await websocket.send(json.dumps(tick_msg))
        tick_response = json.loads(await asyncio.wait_for(websocket.recv(), timeout=5))
        
        # Place trade
        bot_state.request_id += 1
        trade_msg = {
            "buy": 1,
            "subscribe": 1,
            "req_id": bot_state.request_id,
            "contract_type": direction,
            "currency": "USD",
            "duration": 5,
            "duration_unit": "m",
            "symbol": symbol,
            "amount": amount,
            "basis": "stake"
        }
        
        await websocket.send(json.dumps(trade_msg))
        trade_response = json.loads(await asyncio.wait_for(websocket.recv(), timeout=10))
        
        # Process response
        if "buy" in trade_response:
            contract_id = trade_response["buy"].get("contract_id")
            payout = trade_response["buy"].get("payout", amount * 2)
            
            # Update state
            bot_state.trades_count += 1
            pnl = payout - amount  # Simple P&L calculation
            bot_state.total_pnl += pnl
            bot_state.current_balance += pnl
            
            if bot_state.is_real_account:
                bot_state.real_balance = bot_state.current_balance
            else:
                bot_state.demo_balance = bot_state.current_balance
            
            if pnl > 0:
                bot_state.wins += 1
            else:
                bot_state.losses += 1
            
            # Add to history
            bot_state.trade_history.insert(0, {
                "id": trade_id,
                "time": timestamp,
                "symbol": symbol,
                "type": direction,
                "amount": amount,
                "result": "WIN" if pnl > 0 else "LOSS",
                "pnl": pnl
            })
            
            print(f"Trade {trade_id}: {direction} on {symbol} - P&L: ${pnl}")
        
    except Exception as e:
        print(f"Trade execution error: {e}")


if __name__ == '__main__':
    print(f"Starting Deriv Trading Bot Dashboard - LIVE MODE")
    print(f"Open browser: http://localhost:5000")
    app.run(debug=False, host='localhost', port=5000)
