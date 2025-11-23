import { Tile } from '@carbon/react';
import { LineChart, AreaChart, SimpleBarChart, DonutChart } from '@carbon/charts-react';
import '@carbon/charts-react/styles.css';
import { ChartLine, ChartBar, ChartPie } from '@carbon/icons-react';
export default function PerformanceCharts({ trades }) {
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
  const timeSeriesData = generateTimeSeriesData();
  const volumeData = generateVolumeData();
  const assetData = generateAssetAllocation();
  const plData = generatePLData();
  return (
    <div className="space-y-6">
      {}
      <Tile className="border border-blue-600/40 bg-gray-900/90 backdrop-blur-sm hover:border-blue-500/50 transition-all shadow-[inset_0_-40px_60px_-20px_rgba(59,130,246,0.15)]">
        <div className="flex items-center gap-2 mb-6">
          <ChartLine size={20} className="text-blue-400" />
          <h3 className="text-2xl text-blue-400" style={{ fontFamily: 'IBM Plex Sans', fontWeight: 300, letterSpacing: '-0.01em' }}>Portfolio Performance</h3>
        </div>
        <div style={{ height: '300px' }}>
          <AreaChart
            data={timeSeriesData}
            options={{
              title: '',
              axes: {
                bottom: {
                  title: 'Date',
                  mapsTo: 'date',
                  scaleType: 'labels',
                },
                left: {
                  title: 'Portfolio Value ($)',
                  mapsTo: 'value',
                  scaleType: 'linear',
                },
              },
              curve: 'curveMonotoneX',
              height: '300px',
              theme: 'g100',
            }}
          />
        </div>
      </Tile>
      <div className="grid grid-cols-2 gap-6">
        {}
        <Tile className="border border-blue-600/40 bg-gray-900/90 backdrop-blur-sm hover:border-blue-500/50 transition-all shadow-[inset_0_-40px_60px_-20px_rgba(59,130,246,0.15)]">
          <div className="flex items-center gap-2 mb-6">
            <ChartBar size={20} className="text-blue-400" />
            <h3 className="text-2xl text-blue-400" style={{ fontFamily: 'IBM Plex Sans', fontWeight: 300, letterSpacing: '-0.01em' }}>Weekly Volume</h3>
          </div>
          <div style={{ height: '250px' }}>
            <SimpleBarChart
              data={volumeData}
              options={{
                title: '',
                axes: {
                  bottom: {
                    title: 'Day',
                    mapsTo: 'key',
                    scaleType: 'labels',
                  },
                  left: {
                    title: 'Volume',
                    mapsTo: 'value',
                    scaleType: 'linear',
                  },
                },
                height: '250px',
                theme: 'g100',
              }}
            />
          </div>
        </Tile>
        {}
        <Tile className="border border-blue-600/40 bg-gray-900/90 backdrop-blur-sm hover:border-blue-500/50 transition-all shadow-[inset_0_-40px_60px_-20px_rgba(59,130,246,0.15)]">
          <div className="flex items-center gap-2 mb-6">
            <ChartPie size={20} className="text-blue-400" />
            <h3 className="text-2xl text-blue-400" style={{ fontFamily: 'IBM Plex Sans', fontWeight: 300, letterSpacing: '-0.01em' }}>Asset Allocation</h3>
          </div>
          <div style={{ height: '250px' }}>
            <DonutChart
              data={assetData}
              options={{
                title: '',
                resizable: true,
                donut: {
                  center: {
                    label: 'Assets',
                  },
                },
                height: '250px',
                theme: 'g100',
              }}
            />
          </div>
        </Tile>
      </div>
      {}
      <Tile className="border border-blue-600/40 bg-gray-900/90 backdrop-blur-sm hover:border-blue-500/50 transition-all shadow-[inset_0_-40px_60px_-20px_rgba(59,130,246,0.15)]">
        <div className="flex items-center gap-2 mb-6">
          <ChartLine size={20} className="text-blue-400" />
          <h3 className="text-2xl text-blue-400" style={{ fontFamily: 'IBM Plex Sans', fontWeight: 300, letterSpacing: '-0.01em' }}>Profit & Loss Timeline</h3>
        </div>
        <div style={{ height: '200px' }}>
          <LineChart
            data={plData}
            options={{
              title: '',
              axes: {
                bottom: {
                  title: 'Date',
                  mapsTo: 'date',
                  scaleType: 'labels',
                },
                left: {
                  title: 'P&L ($)',
                  mapsTo: 'value',
                  scaleType: 'linear',
                },
              },
              curve: 'curveMonotoneX',
              height: '200px',
              theme: 'g100',
            }}
          />
        </div>
      </Tile>
    </div>
  );
}
