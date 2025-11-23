import { Tile } from '@carbon/react';
import { ArrowUp, ArrowDown, ChartPie, Document } from '@carbon/icons-react';
import { formatCurrency, formatPercentage } from '../lib/utils';
import axios from 'axios';
import { toast } from 'sonner';
import { useState, useEffect } from 'react';
export default function PortfolioSummary({ trades }) {
  const [csvData, setCsvData] = useState([]);
  useEffect(() => {
    fetchCSVData();
  }, []);
  const fetchCSVData = async () => {
    try {
      const response = await axios.get('http:
      const csvText = response.data;
      const rows = csvText.split('\n').slice(1).filter(row => row.trim());
      const parsed = rows.map(row => {
        const cols = row.split(',');
        return {
          client: cols[1]?.trim() || '',
          side: cols[3]?.trim()?.toUpperCase() || '',
          ticker: cols[4]?.trim() || '',
          qty: parseFloat(cols[5]) || 0,
          price: parseFloat(cols[7]) || 0
        };
      }).filter(row => row.client && row.ticker && row.qty > 0);
      setCsvData(parsed);
    } catch (error) {
      console.error('Error fetching CSV:', error);
    }
  };
  const calculatePortfolioValue = () => {
    const stockPrices = {
      'AAPL': 175.50,
      'TSLA': 245.00,
      'MSFT': 380.25,
      'GOOGL': 142.50,
      'NVDA': 495.75,
      'AMZN': 155.30,
      'DUK': 95.20,
      'PLTR': 28.90,
      'RIVN': 18.50,
      'DAL': 48.75
    };
    let totalCost = 0;
    let totalCurrentValue = 0;
    const clientTotals = {};
    const holdings = {};
    csvData.forEach(trade => {
      const currentPrice = stockPrices[trade.ticker] || trade.price || 100;
      const costPrice = trade.price || currentPrice * 0.95;
      if (trade.side === 'BUY') {
        const cost = trade.qty * costPrice;
        totalCost += cost;
        if (!holdings[trade.ticker]) {
          holdings[trade.ticker] = { qty: 0, cost: 0 };
        }
        holdings[trade.ticker].qty += trade.qty;
        holdings[trade.ticker].cost += cost;
        if (!clientTotals[trade.client]) {
          clientTotals[trade.client] = 0;
        }
        clientTotals[trade.client] += trade.qty * currentPrice;
      } else if (trade.side === 'SELL') {
        if (!holdings[trade.ticker]) {
          holdings[trade.ticker] = { qty: 0, cost: 0 };
        }
        const avgCost = holdings[trade.ticker].cost / (holdings[trade.ticker].qty || 1);
        holdings[trade.ticker].qty -= trade.qty;
        holdings[trade.ticker].cost -= trade.qty * avgCost;
      }
    });
    Object.entries(holdings).forEach(([ticker, data]) => {
      if (data.qty > 0) {
        const currentPrice = stockPrices[ticker] || 100;
        totalCurrentValue += data.qty * currentPrice;
      }
    });
    const profitLoss = totalCurrentValue - totalCost;
    const profitLossPercent = totalCost > 0 ? (profitLoss / totalCost) : 0;
    const commission = totalCost * 0.05;
    const topClients = Object.entries(clientTotals)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 3);
    return { 
      totalValue: totalCurrentValue, 
      totalCost, 
      profitLoss, 
      profitLossPercent,
      commission,
      topClients
    };
  };
  const stats = calculatePortfolioValue();
  return (
    <Tile className="border border-blue-600/40 bg-gray-900/90 backdrop-blur-sm h-full overflow-y-auto">
      <div className="flex justify-between items-center mb-4">
        <div className="flex items-center gap-2">
          <ChartPie size={20} className="text-blue-400" />
          <h3 className="text-2xl text-blue-400" style={{ fontFamily: 'IBM Plex Sans', fontWeight: 300, letterSpacing: '-0.01em' }}>Portfolio</h3>
        </div>
        <button
          onClick={async () => {
            try {
              const response = await axios.get('http:
              if (response.data.success) {
                toast.success('Opening trade blotter CSV...');
              }
            } catch (error) {
              console.error('Error opening CSV:', error);
              toast.error('Failed to open CSV file');
            }
          }}
          className="p-1 hover:bg-gray-800/50 rounded transition-colors"
          title="Open CSV"
        >
          <Document size={16} className="text-blue-400" />
        </button>
      </div>
      <div className="space-y-4">
        <Tile className="border border-blue-600/40 bg-gray-800/70 backdrop-blur-sm hover:bg-gray-800/90 hover:border-blue-500/50 shadow-[inset_0_-25px_40px_-10px_rgba(59,130,246,0.12)] transition-all">
          <p className="text-xs text-gray-400 mb-1">Total Value</p>
          <p className="text-2xl font-bold text-blue-400">{formatCurrency(stats.totalValue)}</p>
        </Tile>
        <div className="grid grid-cols-2 gap-3">
          <Tile className="border border-blue-600/40 bg-gray-800/70 backdrop-blur-sm hover:bg-gray-800/90 hover:border-blue-500/50 shadow-[inset_0_-30px_50px_-15px_rgba(59,130,246,0.12)] transition-all">
            <p className="text-xs text-gray-400 mb-1">Cost Basis</p>
            <p className="text-sm font-semibold text-blue-300">{formatCurrency(stats.totalCost)}</p>
          </Tile>
          <Tile className={`border bg-gray-800/70 backdrop-blur-sm hover:bg-gray-800/90 transition-all ${
            stats.profitLoss >= 0 ? 'border-green-600/40 hover:border-green-500/50 shadow-[inset_0_-25px_40px_-10px_rgba(34,197,94,0.12)]' : 'border-red-600/40 hover:border-red-500/50 shadow-[inset_0_-25px_40px_-10px_rgba(239,68,68,0.12)]'
          }`}>
            <p className="text-xs text-gray-400 mb-1">P&L</p>
            <div className="flex items-center gap-1">
              {stats.profitLoss >= 0 ? (
                <ArrowUp size={12} className="text-green-400" />
              ) : (
                <ArrowDown size={12} className="text-red-400" />
              )}
              <p className={`text-sm font-semibold ${
                stats.profitLoss >= 0 ? 'text-green-400' : 'text-red-400'
              }`}>
                {formatCurrency(Math.abs(stats.profitLoss))}
              </p>
            </div>
          </Tile>
        </div>
        <Tile light className="bg-blue-50 border-2 border-blue-400">
          <p className="text-xs text-blue-700 mb-2">Return</p>
          <p className={`text-2xl font-bold ${
            stats.profitLossPercent >= 0 ? 'text-green-600' : 'text-red-600'
          }`}>
            {stats.profitLossPercent >= 0 ? '+' : ''}{formatPercentage(stats.profitLossPercent)}
          </p>
        </Tile>
        <Tile className="border border-purple-600/40 bg-gray-800/70 backdrop-blur-sm hover:bg-gray-800/90 hover:border-purple-500/50 shadow-[inset_0_-25px_40px_-10px_rgba(168,85,247,0.12)] transition-all">
          <p className="text-xs text-gray-400 mb-1">Total Commission (5%)</p>
          <p className="text-lg font-semibold text-purple-300">{formatCurrency(stats.commission)}</p>
        </Tile>
        <Tile className="border border-blue-600/40 bg-gray-800/70 backdrop-blur-sm hover:bg-gray-800/90 hover:border-blue-500/50 shadow-[inset_0_-25px_40px_-10px_rgba(59,130,246,0.12)] transition-all">
          <p className="text-xs text-gray-400 mb-2">Top Stock Buyers</p>
          <div className="space-y-2">
            {stats.topClients.length > 0 ? (
              stats.topClients.map(([client, value], index) => (
                <div key={index} className="flex justify-between items-center">
                  <span className="text-xs text-blue-300">{index + 1}. {client}</span>
                  <span className="text-xs font-semibold text-blue-400">{formatCurrency(value)}</span>
                </div>
              ))
            ) : (
              <p className="text-xs text-gray-500">No data available</p>
            )}
          </div>
        </Tile>
      </div>
    </Tile>
  );
}
