import pandas as pd
from datetime import datetime, timedelta

# Create fresh, realistic trade data
clients = [
    'Michael Rodriguez', 'Sarah Chen', 'David Thompson', 'Emily Johnson', 'Robert Martinez',
    'Jennifer Lee', 'James Wilson', 'Lisa Anderson', 'William Brown', 'Jessica Davis',
    'Christopher Garcia', 'Amanda Martinez', 'Daniel Rodriguez', 'Michelle Thompson', 'Kevin White',
    'Stephanie Harris', 'Brian Clark', 'Nicole Lewis', 'Andrew Walker', 'Megan Hall',
    'Thomas Allen', 'Rebecca Young', 'Joseph King', 'Laura Wright', 'Mark Lopez',
    'Karen Hill', 'Steven Scott', 'Patricia Green', 'Ryan Adams', 'Angela Baker',
    'Eric Nelson', 'Sandra Carter', 'Timothy Mitchell', 'Catherine Perez', 'Gregory Roberts'
]

tickers = [
    'AAPL', 'TSLA', 'MSFT', 'GOOGL', 'NVDA', 'AMD', 'META', 'AMZN', 'NFLX', 'JPM',
    'BAC', 'WMT', 'DIS', 'COST', 'V', 'MA', 'PYPL', 'INTC', 'CRM', 'ORCL',
    'IBM', 'CSCO', 'HPQ', 'ADBE', 'NOW', 'SNOW', 'UBER', 'ABNB', 'LYFT', 'SQ',
    'SHOP', 'EBAY', 'SPOT', 'ROKU', 'PINS'
]

notes_list = [
    'Tech sector diversification', 'Profit taking after 40% gain', 'Cloud computing exposure',
    'AI and search dominance', 'Portfolio rebalancing', 'Semiconductor opportunity',
    'Social media growth', 'Cloud services profits', 'Streaming content investment',
    'Banking diversification', 'Reducing banking exposure', 'Retail sector stability',
    'Entertainment streaming', 'Retail profits', 'Payments processing growth',
    'Digital payments', 'Fintech rebalancing', 'Semiconductor turnaround',
    'Cloud CRM leadership', 'Database software', 'AI quantum computing',
    'Networking infrastructure', 'Hardware reduction', 'Creative software',
    'Enterprise software', 'Cloud data profits', 'Rideshare recovery',
    'Travel rebound', 'Rideshare exit', 'Fintech innovation',
    'E-commerce growth', 'Marketplace exit', 'Music streaming', 'Streaming platform', 'Social media rebalancing'
]

data = {
    'TicketID': [f'TKT-2025-{str(i+1).zfill(3)}' for i in range(35)],
    'Client': clients,
    'Acct#': [f'ACC-{10001+i}' for i in range(35)],
    'Side': ['Buy', 'Sell', 'Buy', 'Buy', 'Sell'] * 7,
    'Ticker': tickers,
    'Qty': [250, 150, 300, 175, 100, 400, 200, 125, 180, 350, 275, 320, 225, 150, 275, 240, 190, 425, 180, 210, 300, 380, 245, 165, 145, 120, 355, 195, 280, 310, 185, 225, 270, 340, 195],
    'Type': ['Market', 'Limit', 'Market', 'Limit', 'Market'] * 7,
    'Price': ['0.0', '295.50', '0.0', '142.25', '0.0'] * 7,
    'Solicited': ['Yes', 'No'] * 17 + ['Yes'],
    'Timestamp': [(datetime(2025, 11, 20) + timedelta(hours=i*2.5)).strftime('%Y-%m-%d %H:%M:%S') for i in range(35)],
    'Notes': notes_list,
    'FollowUpDate': [(datetime(2025, 11, 25) + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(35)],
    'Email': [name.lower().replace(' ', '.') + '@email.com' for name in clients],
    'Stage': ['Completed', 'Completed', 'Pending', 'Completed', 'Completed'] * 7,
    'MeetingNeeded': ['No', 'No', 'Yes', 'No', 'No'] * 7
}

df = pd.DataFrame(data)
df.to_csv('data/trade_blotter.csv', index=False)
print(f'✅ Created CSV with {len(df)} trades')
print(f'Columns: {list(df.columns)}')
print(f'\nSample rows:')
print(df.head(3)[['TicketID', 'Client', 'Side', 'Ticker', 'Qty', 'Email']].to_string())
