# Deriv Automated Trading Bot

A simple automated trading script for Deriv using Python and the Deriv WebSocket API.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Ensure your `.env` file contains your Deriv token:
   ```
   DERIV_TOKEN=your_token_here
   ```

## Usage

Run the Flask dashboard:
```bash
python app.py
```

Open your browser at:
```bash
http://localhost:5000
```

## Features

- Connects to Deriv WebSocket API using your token
- Retrieves real account balance and demo balance
- Displays live trade history and P&L in a browser dashboard
- Starts and stops the bot from the web interface
- Exports trade history to JSON

## Configuration

To customize the trading strategy, edit the `simple_strategy()` method in `trading_bot.py`:

- **symbol**: Change to different currency pairs (e.g., "frxEURUSD", "frxGBPUSD")
- **amount**: Adjust stake amount
- **direction**: Set to "CALL" or "PUT"
- **duration**: Modify trade duration in minutes

## Available Symbols

- `frxEURUSD` - EUR/USD
- `frxGBPUSD` - GBP/USD
- `frxUSDJPY` - USD/JPY
- And many more...

## Important Notes

- The `place_trade()` method is commented out by default for safety
- Uncomment it in the strategy to actually place real trades
- Always test thoroughly in a demo account first
- This is a basic template - expand with your own trading logic

## Disclaimer

Trading involves risk. Use at your own risk and ensure you understand the markets before placing real trades.
