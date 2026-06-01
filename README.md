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

## Railway Deployment

This project includes Railway support for deployment.

1. Add your Railway API token to `.env`:
   ```env
   RAILWAY_TOKEN=your_railway_token_here
   ```
2. Check connection:
   ```bash
   python railway_connect.py status
   ```
3. List your Railway projects:
   ```bash
   python railway_connect.py projects
   ```
4. Inspect the Railway project created for this repo:
   ```bash
   python railway_connect.py project 6879b6de-c90c-4b35-add9-1d99b9a4f95a
   ```

Railway will use `Procfile` to start the Flask app with:

```text
web: python app.py
```

If you want to inspect the deployed service directly, use:
```bash
python railway_connect.py service fd932ef3-2d37-469f-bbe7-e2cbaf283def
```

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
