import { Tile } from '@carbon/react';
import { useState, useEffect } from 'react';
import axios from 'axios';
import { LineChart, AreaChart, SimpleBarChart, DonutChart } from '@carbon/charts-react';
import '@carbon/charts-react/styles.css';
export default function ComplianceCharts() {
  const [analytics, setAnalytics] = useState(null);
  const generateTimeSeriesData = () => {
    const data = [];
    const today = new Date();
    for (let i = 30; i >= 0; i--) {
      const date = new Date(today);
      date.setDate(date.getDate() - i);
      data.push({
        group: 'Portfolio',
        date: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
        value: 50000 + Math.random() * 10000,
      });
    }
    return data;
  };
  const generateVolumeData = () => {
    return ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'].flatMap(day => [
      { group: 'Buy', key: day, value: Math.floor(Math.random() * 1000) + 500 },
      { group: 'Sell', key: day, value: Math.floor(Math.random() * 800) + 400 },
    ]);
  };
  const generateAssetAllocation = () => {
    const assets = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'AMZN'];
    return assets.map(asset => ({
      group: asset,
      value: Math.floor(Math.random() * 30) + 10,
    }));
  };
  const generatePLData = () => {
    const data = [];
    const today = new Date();
    for (let i = 30; i >= 0; i--) {
      const date = new Date(today);
      date.setDate(date.getDate() - i);
      data.push({
        group: 'P&L',
        date: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
        value: Math.random() * 5000 + 2000,
      });
    }
    return data;
  };
  useEffect(() => {
    const fetchData = async () => {
      try {
        console.log('ComplianceCharts: Fetching CSV data...');
        const response = await axios.get('http:
        console.log('ComplianceCharts: CSV data received:', response.data);
        if (response.data.success) {
          calculateAnalytics(response.data.rows);
        } else {
          console.error('ComplianceCharts: API returned success=false');
        }
      } catch (error) {
        console.error('ComplianceCharts: Failed to fetch CSV data:', error);
      }
    };
    fetchData();
  }, []);
  const calculateAnalytics = (rows) => {
    if (!rows || rows.length === 0) return;
    const buys = rows.filter(r => r.Side?.toLowerCase() === 'buy').length;
    const sells = rows.filter(r => r.Side?.toLowerCase() === 'sell').length;
    const solicited = rows.filter(r => r.Solicited?.toLowerCase() === 'yes').length;
    const unsolicited = rows.filter(r => r.Solicited?.toLowerCase() === 'no').length;
    const marketOrders = rows.filter(r => r.Type?.toLowerCase() === 'market').length;
    const limitOrders = rows.filter(r => r.Type?.toLowerCase() === 'limit').length;
    const pending = rows.filter(r => r.Stage?.toLowerCase().includes('pending') || !r.Stage).length;
    const followUp = rows.filter(r => r.Stage?.toLowerCase().includes('follow')).length;
    const compliance = rows.filter(r => r.Stage?.toLowerCase().includes('compliance')).length;
    const needsMeeting = rows.filter(r => r.MeetingNeeded?.toLowerCase() === 'yes').length;
    const tickerCount = {};
    rows.forEach(r => {
      if (r.Ticker) tickerCount[r.Ticker] = (tickerCount[r.Ticker] || 0) + 1;
    });
    const topTickers = Object.entries(tickerCount).sort((a, b) => b[1] - a[1]).slice(0, 5);
    const clientCount = {};
    rows.forEach(r => {
      if (r.Client) clientCount[r.Client] = (clientCount[r.Client] || 0) + 1;
    });
    const topClients = Object.entries(clientCount).sort((a, b) => b[1] - a[1]).slice(0, 5);
    const totalVolume = rows.reduce((sum, r) => sum + (parseInt(r.Qty) || 0), 0);
    const avgVolume = Math.round(totalVolume / rows.length);
    const highRiskTrades = rows.filter(r => 
      r.Stage?.toLowerCase().includes('compliance') || 
      r.MeetingNeeded?.toLowerCase() === 'yes' ||
      r.Notes?.toLowerCase().includes('risk') ||
      r.Notes?.toLowerCase().includes('panic') ||
      r.Notes?.toLowerCase().includes('emotional')
    ).length;
    const avgPrice = rows.filter(r => parseFloat(r.Price) > 0).reduce((sum, r, _, arr) => 
      sum + parseFloat(r.Price) / arr.length, 0
    );
    const analyticsData = {
      total: rows.length, buys, sells, solicited, unsolicited, marketOrders,
      limitOrders, pending, followUp, compliance, needsMeeting, topTickers,
      topClients, totalVolume, avgVolume, highRiskTrades, avgPrice
    };
    console.log('ComplianceCharts: Analytics calculated:', analyticsData);
    setAnalytics(analyticsData);
  };
  if (!analytics) {
    return null;
  }
  return (
    <div className="space-y-4">
      {}
      <div className="grid grid-cols-4 gap-4">
        <Tile className="border border-blue-600/40 bg-gray-900/90 backdrop-blur-sm hover:border-blue-500/50 transition-all">
          <p className="text-xs text-gray-400 mb-1">Total Trades</p>
          <p className="text-3xl font-bold text-blue-400">{analytics.total}</p>
        </Tile>
        <Tile className="border border-green-600/40 bg-gray-900/90 backdrop-blur-sm">
          <p className="text-xs text-gray-400 mb-1">Buy Orders</p>
          <p className="text-3xl font-bold text-green-400">{analytics.buys}</p>
          <p className="text-xs text-gray-500">{((analytics.buys/analytics.total)*100).toFixed(0)}%</p>
        </Tile>
        <Tile className="border border-red-600/40 bg-gray-900/90 backdrop-blur-sm">
          <p className="text-xs text-gray-400 mb-1">Sell Orders</p>
          <p className="text-3xl font-bold text-red-400">{analytics.sells}</p>
          <p className="text-xs text-gray-500">{((analytics.sells/analytics.total)*100).toFixed(0)}%</p>
        </Tile>
        <Tile className="border border-yellow-600/40 bg-gray-900/90 backdrop-blur-sm">
          <p className="text-xs text-gray-400 mb-1">High Risk</p>
          <p className="text-3xl font-bold text-yellow-400">{analytics.highRiskTrades}</p>
        </Tile>
      </div>
      <div className="grid grid-cols-2 gap-4">
        {}
        <Tile className="border border-blue-600/40 bg-gray-900/90 backdrop-blur-sm">
          <h3 className="text-xl mb-4 text-blue-400" style={{ fontFamily: 'IBM Plex Sans' }}>Buy vs Sell Distribution</h3>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between mb-1">
                <span className="text-xs text-gray-300">Buy Orders</span>
                <span className="text-xs text-green-400">{analytics.buys} ({((analytics.buys/analytics.total)*100).toFixed(0)}%)</span>
              </div>
              <div className="w-full bg-gray-700 h-8">
                <div className="bg-gradient-to-r from-green-600 to-green-500 h-8 flex items-center justify-center text-white text-sm font-bold"
                  style={{width: `${((analytics.buys/analytics.total)*100).toFixed(0)}%`}}>
                  {((analytics.buys/analytics.total)*100).toFixed(0)}%
                </div>
              </div>
            </div>
            <div>
              <div className="flex justify-between mb-1">
                <span className="text-xs text-gray-300">Sell Orders</span>
                <span className="text-xs text-red-400">{analytics.sells} ({((analytics.sells/analytics.total)*100).toFixed(0)}%)</span>
              </div>
              <div className="w-full bg-gray-700 h-8">
                <div className="bg-gradient-to-r from-red-600 to-red-500 h-8 flex items-center justify-center text-white text-sm font-bold"
                  style={{width: `${((analytics.sells/analytics.total)*100).toFixed(0)}%`}}>
                  {((analytics.sells/analytics.total)*100).toFixed(0)}%
                </div>
              </div>
            </div>
          </div>
        </Tile>
        {}
        <Tile className="border border-blue-600/40 bg-gray-900/90 backdrop-blur-sm">
          <h3 className="text-xl mb-4 text-blue-400" style={{ fontFamily: 'IBM Plex Sans' }}>Solicitation Analysis</h3>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between mb-1">
                <span className="text-xs text-gray-300">Solicited</span>
                <span className="text-xs text-orange-400">{analytics.solicited} ({((analytics.solicited/analytics.total)*100).toFixed(0)}%)</span>
              </div>
              <div className="w-full bg-gray-700 h-8">
                <div className="bg-gradient-to-r from-orange-600 to-orange-500 h-8 flex items-center justify-center text-white text-sm font-bold"
                  style={{width: `${((analytics.solicited/analytics.total)*100).toFixed(0)}%`}}>
                  {((analytics.solicited/analytics.total)*100).toFixed(0)}%
                </div>
              </div>
            </div>
            <div>
              <div className="flex justify-between mb-1">
                <span className="text-xs text-gray-300">Unsolicited</span>
                <span className="text-xs text-green-400">{analytics.unsolicited} ({((analytics.unsolicited/analytics.total)*100).toFixed(0)}%)</span>
              </div>
              <div className="w-full bg-gray-700 h-8">
                <div className="bg-gradient-to-r from-green-600 to-green-500 h-8 flex items-center justify-center text-white text-sm font-bold"
                  style={{width: `${((analytics.unsolicited/analytics.total)*100).toFixed(0)}%`}}>
                  {((analytics.unsolicited/analytics.total)*100).toFixed(0)}%
                </div>
              </div>
            </div>
          </div>
          <div className="mt-4 p-2 bg-yellow-900/40 border-l-4 border-yellow-500/60">
            <p className="text-xs text-yellow-300" style={{ fontFamily: 'IBM Plex Sans' }}>
              {((analytics.solicited/analytics.total)*100)>50 ? 'High solicited ratio - Monitor churning' : 'Healthy ratio'}
            </p>
          </div>
        </Tile>
        {}
        <Tile className="border border-blue-600/40 bg-gray-900/90 backdrop-blur-sm">
          <h3 className="text-xl mb-4 text-blue-400" style={{ fontFamily: 'IBM Plex Sans' }}>Order Type Distribution</h3>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between mb-1">
                <span className="text-xs text-gray-300">Market Orders</span>
                <span className="text-xs text-purple-400">{analytics.marketOrders}</span>
              </div>
              <div className="w-full bg-gray-700 h-8">
                <div className="bg-gradient-to-r from-purple-600 to-purple-500 h-8 flex items-center justify-center text-white text-sm font-bold"
                  style={{width: `${((analytics.marketOrders/analytics.total)*100).toFixed(0)}%`}}>
                  {((analytics.marketOrders/analytics.total)*100).toFixed(0)}%
                </div>
              </div>
            </div>
            <div>
              <div className="flex justify-between mb-1">
                <span className="text-xs text-gray-300">Limit Orders</span>
                <span className="text-xs text-cyan-400">{analytics.limitOrders}</span>
              </div>
              <div className="w-full bg-gray-700 h-8">
                <div className="bg-gradient-to-r from-cyan-600 to-cyan-500 h-8 flex items-center justify-center text-white text-sm font-bold"
                  style={{width: `${((analytics.limitOrders/analytics.total)*100).toFixed(0)}%`}}>
                  {((analytics.limitOrders/analytics.total)*100).toFixed(0)}%
                </div>
              </div>
            </div>
          </div>
          <div className="mt-4 grid grid-cols-2 gap-2">
            <div className="p-2 bg-gray-800/50 rounded">
              <p className="text-xs text-gray-400">Total Volume</p>
              <p className="text-lg font-bold text-blue-400">{analytics.totalVolume.toLocaleString()}</p>
            </div>
            <div className="p-2 bg-gray-800/50 rounded">
              <p className="text-xs text-gray-400">Avg Size</p>
              <p className="text-lg font-bold text-blue-400">{analytics.avgVolume.toLocaleString()}</p>
            </div>
          </div>
        </Tile>
        {}
        <Tile className="border border-blue-600/40 bg-gray-900/90 backdrop-blur-sm">
          <h3 className="text-xl mb-4 text-blue-400" style={{ fontFamily: 'IBM Plex Sans' }}>Trade Stage Pipeline</h3>
          <div className="space-y-3">
            <div>
              <div className="flex justify-between mb-1">
                <span className="text-xs text-gray-300">Pending</span>
                <span className="text-xs text-gray-400">{analytics.pending}</span>
              </div>
              <div className="w-full bg-gray-700 h-6">
                <div className="bg-gray-600 h-6 flex items-center justify-center text-white text-xs"
                  style={{width: `${((analytics.pending/analytics.total)*100).toFixed(0)}%`}}>
                  {analytics.pending}
                </div>
              </div>
            </div>
            <div>
              <div className="flex justify-between mb-1">
                <span className="text-xs text-gray-300">Follow-up Scheduled</span>
                <span className="text-xs text-blue-400">{analytics.followUp}</span>
              </div>
              <div className="w-full bg-gray-700 h-6">
                <div className="bg-blue-600 h-6 flex items-center justify-center text-white text-xs"
                  style={{width: `${((analytics.followUp/analytics.total)*100).toFixed(0)}%`}}>
                  {analytics.followUp}
                </div>
              </div>
            </div>
            <div>
              <div className="flex justify-between mb-1">
                <span className="text-xs text-gray-300">Compliance Review</span>
                <span className="text-xs text-yellow-400">{analytics.compliance}</span>
              </div>
              <div className="w-full bg-gray-700 h-6">
                <div className="bg-yellow-600 h-6 flex items-center justify-center text-white text-xs"
                  style={{width: `${((analytics.compliance/analytics.total)*100).toFixed(0)}%`}}>
                  {analytics.compliance}
                </div>
              </div>
            </div>
            <div>
              <div className="flex justify-between mb-1">
                <span className="text-xs text-gray-300">Meeting Required</span>
                <span className="text-xs text-red-400">{analytics.needsMeeting}</span>
              </div>
              <div className="w-full bg-gray-700 h-6">
                <div className="bg-red-600 h-6 flex items-center justify-center text-white text-xs"
                  style={{width: `${((analytics.needsMeeting/analytics.total)*100).toFixed(0)}%`}}>
                  {analytics.needsMeeting}
                </div>
              </div>
            </div>
          </div>
        </Tile>
        {}
        <Tile className="border border-blue-600/40 bg-gray-900/90 backdrop-blur-sm">
          <h3 className="text-xl mb-4 text-blue-400" style={{ fontFamily: 'IBM Plex Sans' }}>Top 5 Most Traded Tickers</h3>
          <div className="space-y-3">
            {analytics.topTickers.map(([ticker, count], idx) => (
              <div key={ticker} className="flex items-center gap-3">
                <div className="w-8 h-8 rounded bg-blue-600/20 flex items-center justify-center text-blue-400 font-bold text-sm">
                  {idx+1}
                </div>
                <div className="flex-1">
                  <div className="flex justify-between mb-1">
                    <span className="text-sm font-bold text-gray-200">{ticker}</span>
                    <span className="text-xs text-gray-400">{count} trades</span>
                  </div>
                  <div className="w-full bg-gray-700 h-2 rounded">
                    <div className="bg-blue-600 h-2 rounded"
                      style={{width: `${(count/analytics.topTickers[0][1])*100}%`}} />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Tile>
        {}
        <Tile className="border border-blue-600/40 bg-gray-900/90 backdrop-blur-sm">
          <h3 className="text-xl mb-4 text-blue-400" style={{ fontFamily: 'IBM Plex Sans' }}>Top 5 Most Active Clients</h3>
          <div className="space-y-3">
            {analytics.topClients.map(([client, count], idx) => (
              <div key={client} className="flex items-center gap-3">
                <div className="w-8 h-8 rounded bg-green-600/20 flex items-center justify-center text-green-400 font-bold text-sm">
                  {idx+1}
                </div>
                <div className="flex-1">
                  <div className="flex justify-between mb-1">
                    <span className="text-sm font-bold text-gray-200">{client}</span>
                    <span className="text-xs text-gray-400">{count} trades</span>
                  </div>
                  <div className="w-full bg-gray-700 h-2 rounded">
                    <div className="bg-green-600 h-2 rounded"
                      style={{width: `${(count/analytics.topClients[0][1])*100}%`}} />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Tile>
        {}
        <Tile className="border border-red-600/40 bg-gray-900/90 backdrop-blur-sm col-span-2">
          <h3 className="text-xl mb-4 text-red-400" style={{ fontFamily: 'IBM Plex Sans' }}>Risk Assessment & Compliance Summary</h3>
          <div className="grid grid-cols-4 gap-4">
            <div className="p-4 bg-gray-800/50 rounded">
              <p className="text-xs text-gray-400 mb-2">Compliance Score</p>
              <p className="text-3xl font-bold text-green-400">
                {(((analytics.total-analytics.highRiskTrades)/analytics.total)*100).toFixed(0)}
              </p>
              <p className="text-xs text-gray-500">/ 100</p>
            </div>
            <div className="p-4 bg-gray-800/50 rounded">
              <p className="text-xs text-gray-400 mb-2">High Risk Trades</p>
              <p className="text-3xl font-bold text-yellow-400">{analytics.highRiskTrades}</p>
              <p className="text-xs text-gray-500">{((analytics.highRiskTrades/analytics.total)*100).toFixed(1)}%</p>
            </div>
            <div className="p-4 bg-gray-800/50 rounded">
              <p className="text-xs text-gray-400 mb-2">Meetings Required</p>
              <p className="text-3xl font-bold text-orange-400">{analytics.needsMeeting}</p>
              <p className="text-xs text-gray-500">Immediate action</p>
            </div>
            <div className="p-4 bg-gray-800/50 rounded">
              <p className="text-xs text-gray-400 mb-2">Avg Limit Price</p>
              <p className="text-3xl font-bold text-blue-400">
                ${analytics.avgPrice>0 ? analytics.avgPrice.toFixed(2) : '0.00'}
              </p>
              <p className="text-xs text-gray-500">For limit orders</p>
            </div>
          </div>
          <div className="mt-4 p-3 bg-red-900/30 border-l-4 border-red-500/80 rounded">
            <p className="text-sm font-semibold text-red-300 mb-1" style={{ fontFamily: 'IBM Plex Sans' }}>Compliance Alerts</p>
            <ul className="text-xs text-gray-300 space-y-1">
              {analytics.highRiskTrades>0 && <li>• {analytics.highRiskTrades} trade(s) flagged for compliance review</li>}
              {analytics.needsMeeting>0 && <li>• {analytics.needsMeeting} client(s) require follow-up meetings</li>}
              {((analytics.solicited/analytics.total)*100)>50 && <li>• High solicited trade ratio - Review for churning patterns</li>}
              {analytics.compliance>0 && <li>• {analytics.compliance} trade(s) currently under compliance review</li>}
              {analytics.highRiskTrades===0 && analytics.needsMeeting===0 && 
                <li className="text-green-400">No critical compliance issues detected</li>}
            </ul>
          </div>
        </Tile>
      </div>
      {}
      <div className="mt-8">
        <h2 className="text-2xl font-bold text-white mb-4" style={{ fontFamily: 'IBM Plex Sans' }}>Performance Charts</h2>
        <div className="grid grid-cols-2 gap-4">
          {}
          <Tile className="border border-blue-600/40 bg-gray-900/90 backdrop-blur-sm">
            <h3 className="text-lg mb-3 text-blue-400" style={{ fontFamily: 'IBM Plex Sans' }}>Portfolio Performance</h3>
            <LineChart
              data={generateTimeSeriesData()}
              options={{
                title: '',
                axes: {
                  bottom: { title: 'Date', mapsTo: 'date', scaleType: 'labels' },
                  left: { title: 'Value ($)', mapsTo: 'value', scaleType: 'linear' }
                },
                curve: 'curveMonotoneX',
                height: '300px',
                theme: 'g90',
                color: { scale: { Portfolio: '#4589ff' } }
              }}
            />
          </Tile>
          {}
          <Tile className="border border-blue-600/40 bg-gray-900/90 backdrop-blur-sm">
            <h3 className="text-lg mb-3 text-blue-400" style={{ fontFamily: 'IBM Plex Sans' }}>Weekly Volume</h3>
            <SimpleBarChart
              data={generateVolumeData()}
              options={{
                title: '',
                axes: {
                  bottom: { title: 'Day', mapsTo: 'key', scaleType: 'labels' },
                  left: { title: 'Volume', mapsTo: 'value', scaleType: 'linear' }
                },
                height: '300px',
                theme: 'g90',
                color: { scale: { Buy: '#42be65', Sell: '#fa4d56' } }
              }}
            />
          </Tile>
          {}
          <Tile className="border border-blue-600/40 bg-gray-900/90 backdrop-blur-sm">
            <h3 className="text-lg mb-3 text-blue-400" style={{ fontFamily: 'IBM Plex Sans' }}>Asset Allocation</h3>
            <DonutChart
              data={generateAssetAllocation()}
              options={{
                title: '',
                resizable: true,
                donut: { center: { label: 'Assets' } },
                height: '300px',
                theme: 'g90'
              }}
            />
          </Tile>
          {}
          <Tile className="border border-blue-600/40 bg-gray-900/90 backdrop-blur-sm">
            <h3 className="text-lg mb-3 text-blue-400" style={{ fontFamily: 'IBM Plex Sans' }}>P&L Timeline</h3>
            <AreaChart
              data={generatePLData()}
              options={{
                title: '',
                axes: {
                  bottom: { title: 'Date', mapsTo: 'date', scaleType: 'labels' },
                  left: { title: 'P&L ($)', mapsTo: 'value', scaleType: 'linear' }
                },
                curve: 'curveNatural',
                height: '300px',
                theme: 'g90',
                color: { scale: { 'P&L': '#42be65' } }
              }}
            />
          </Tile>
        </div>
      </div>
    </div>
  );
}
