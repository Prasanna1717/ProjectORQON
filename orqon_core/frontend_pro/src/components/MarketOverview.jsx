import { Tile, Tag, InlineLoading, Button } from '@carbon/react';
import { ArrowUp, ArrowDown, Renew } from '@carbon/icons-react';
import { useState, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'sonner';

const FINNHUB_API_KEY = 'd4h0cd1r01qgvvc5ft20d4h0cd1r01qgvvc5ft2g';

// Symbols to track with their display names
const SYMBOLS = [
  { symbol: 'SPY', name: 'S&P 500' },
  { symbol: 'QQQ', name: 'NASDAQ' },
  { symbol: 'DIA', name: 'DOW' },
  { symbol: 'VXX', name: 'VIX' },
];

export default function MarketOverview() {
  const [marketData, setMarketData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);
  const [currentTime, setCurrentTime] = useState(new Date());

  const fetchMarketData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const promises = SYMBOLS.map(async ({ symbol, name }) => {
        const response = await axios.get(`https://finnhub.io/api/v1/quote`, {
          params: {
            symbol: symbol,
            token: FINNHUB_API_KEY
          }
        });
        
        const data = response.data;
        return {
          symbol: name,
          value: data.c, // current price
          change: data.d, // change
          changePercent: data.dp, // percent change
        };
      });
      
      const results = await Promise.all(promises);
      setMarketData(results);
      setLastUpdate(new Date());
    } catch (err) {
      console.error('Error fetching market data:', err);
      setError('Failed to fetch market data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMarketData();
    // Refresh every 60 seconds
    const interval = setInterval(fetchMarketData, 60000);
    return () => clearInterval(interval);
  }, []);

  // Update clock every second
  useEffect(() => {
    const clockInterval = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);
    return () => clearInterval(clockInterval);
  }, []);

  return (
    <Tile className="border border-blue-600/40 bg-gray-900/90 backdrop-blur-sm">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-2xl text-blue-400" style={{ fontFamily: 'IBM Plex Sans', fontWeight: 300, letterSpacing: '-0.01em' }}>
          Market Overview
        </h3>
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-400 font-mono">
            {currentTime.toLocaleTimeString()}
          </span>
          <button
            onClick={fetchMarketData}
            disabled={loading}
            className="p-1 hover:bg-gray-800/50 rounded transition-colors"
            title="Refresh data"
          >
            <Renew size={16} className={`text-blue-400 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {error && (
        <div className="text-red-400 text-sm mb-4 p-2 bg-red-900/20 rounded border border-red-600/40">
          {error}
        </div>
      )}

      {loading && marketData.length === 0 ? (
        <div className="flex justify-center items-center py-8">
          <InlineLoading description="Loading market data..." />
        </div>
      ) : (
        <div className="space-y-3">
          {marketData.map((market) => (
          <Tile key={market.symbol} className="border border-blue-600/40 bg-gray-800/70 backdrop-blur-sm hover:bg-gray-800/90 hover:border-blue-500/50 transition-all duration-300 shadow-[inset_0_-30px_50px_-15px_rgba(59,130,246,0.12)]">
            <div className="flex justify-between items-start mb-2">
              <span className="text-sm font-semibold text-blue-300">{market.symbol}</span>
              {market.change >= 0 ? (
                <ArrowUp size={16} className="text-green-600" />
              ) : (
                <ArrowDown size={16} className="text-red-600" />
              )}
            </div>
            <div className="flex justify-between items-end">
              <span className="text-2xl font-bold">
                ${market.value?.toFixed(2) || '0.00'}
              </span>
              <div className="text-right">
                <p className={`text-sm font-semibold ${market.change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {market.change >= 0 ? '+' : ''}{market.change?.toFixed(2) || '0.00'}
                </p>
                <p className={`text-xs ${market.changePercent >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {market.changePercent >= 0 ? '+' : ''}{market.changePercent?.toFixed(2) || '0.00'}%
                </p>
              </div>
            </div>
          </Tile>
        ))}
        </div>
      )}
    </Tile>
  );
}



