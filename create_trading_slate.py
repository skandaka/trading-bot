import json
import sys
import os
from datetime import datetime, timedelta
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))
from data_collection.azure_storage import AzureDataManager


def create_realistic_trading_state():
    stocks = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'JPM', 'BAC']

    portfolio = {
        'total_value': 105420.50,
        'cash': 23450.00,
        'total_return': 5.42,
        'positions': {}
    }

    trades = []

    for i, stock in enumerate(stocks[:5]):
        base_prices = {
            'AAPL': 195.20, 'MSFT': 415.30, 'GOOGL': 175.80,
            'AMZN': 145.60, 'META': 485.90, 'NVDA': 875.40,
            'JPM': 165.20, 'BAC': 45.80
        }

        current_price = base_prices.get(stock, 200.00)
        buy_price = current_price * np.random.uniform(0.92, 1.08)  # Some wins, some losses
        quantity = np.random.randint(20, 100)
        pnl = (current_price - buy_price) * quantity

        portfolio['positions'][stock] = {
            'quantity': quantity,
            'buy_price': round(buy_price, 2),
            'current_price': round(current_price, 2),
            'pnl': round(pnl, 2)
        }

        for j in range(np.random.randint(2, 5)):
            trade_time = datetime.now() - timedelta(hours=j * 3, minutes=np.random.randint(0, 180))
            action = np.random.choice(['BUY', 'SELL'], p=[0.6, 0.4])
            trade_price = current_price * np.random.uniform(0.98, 1.02)
            trade_qty = np.random.randint(10, 50)

            trade = {
                'timestamp': trade_time.isoformat(),
                'symbol': stock,
                'action': action,
                'quantity': trade_qty,
                'price': round(trade_price, 2)
            }

            if action == 'SELL':
                trade['profit'] = round((trade_price - buy_price) * trade_qty, 2)

            trades.append(trade)

    trades.sort(key=lambda x: x['timestamp'], reverse=True)

    state = {
        'portfolio': portfolio,
        'trades': trades[:20],  # Last 20 trades
        'timestamp': datetime.now().isoformat(),
        'market_status': 'CLOSED' if datetime.now().hour < 9 or datetime.now().hour > 16 else 'OPEN',
        'last_update': datetime.now().isoformat()
    }

    try:
        azure_manager = AzureDataManager()
        blob_data = json.dumps(state, indent=2)
        azure_manager.save_data_to_blob("trading_state/current_state.json", blob_data)
        print("✅ Created realistic trading state in Azure!")
        print(f"📊 Portfolio Value: ${portfolio['total_value']:,.2f}")
        print(f"💰 Cash: ${portfolio['cash']:,.2f}")
        print(f"📈 Return: {portfolio['total_return']:.2f}%")
        print(f"🏦 Positions: {len(portfolio['positions'])}")
        print(f"📋 Trades: {len(trades)}")
        return True

    except Exception as e:
        print(f"❌ Failed to save trading state: {e}")
        return False


if __name__ == "__main__":
    print("🔧 Creating realistic trading state...")
    if create_realistic_trading_state():
        print("\n🎉 Success! Now refresh your dashboard to see real data.")
        print("Run: streamlit run dashboard/app.py")
    else:
        print("\n❌ Failed. Check your Azure connection in .env file.")