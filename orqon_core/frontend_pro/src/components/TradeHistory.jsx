import { Tile, Tag, Button } from '@carbon/react';
import { Time, ArrowUp, ArrowDown } from '@carbon/icons-react';
import { formatCurrency } from '../lib/utils';

export default function TradeHistory({ trades, expanded = false }) {
  const displayTrades = expanded ? trades : trades.slice(0, 5);

  return (
    <Tile className="border border-blue-600/40 bg-gray-900/60 backdrop-blur-sm h-full overflow-y-auto">
      <div className="flex items-center gap-2 mb-4">
        <Time size={20} className="text-blue-400" />
        <h3 className="text-2xl text-blue-400" style={{ fontFamily: 'IBM Plex Sans', fontWeight: 300, letterSpacing: '-0.01em' }}>Recent Trades</h3>
      </div>

      {displayTrades.length === 0 ? (
        <div className="space-y-3">
          {/* Empty state - no message */}
        </div>
      ) : (
        <div className="space-y-3">
          {displayTrades.map((trade, idx) => (
            <Tile 
              key={idx}
              className="border border-blue-600/40 bg-gray-800/40 backdrop-blur-sm hover:bg-gray-800/60 hover:border-blue-500/50 transition-all duration-300 shadow-[inset_0_-30px_50px_-15px_rgba(59,130,246,0.12)]"
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  {(trade.action === 'BUY' || trade.side === 'Buy') ? (
                    <ArrowUp size={16} className="text-green-600" />
                  ) : (
                    <ArrowDown size={16} className="text-red-600" />
                  )}
                  <Tag type={(trade.action === 'BUY' || trade.side === 'Buy') ? 'green' : 'red'}>
                    {trade.action || trade.side || 'TRADE'}
                  </Tag>
                </div>
                <span className="text-xs text-gray-600">
                  {trade.timestamp ? new Date(trade.timestamp).toLocaleTimeString() : 'N/A'}
                </span>
              </div>

              <div className="grid grid-cols-2 gap-2 text-sm">
                <div>
                  <p className="text-gray-600 text-xs">Ticker</p>
                  <p className="font-bold">{trade.asset || trade.ticker || 'N/A'}</p>
                </div>
                <div>
                  <p className="text-gray-600 text-xs">Quantity</p>
                  <p className="font-semibold">{trade.quantity ? Number(trade.quantity).toLocaleString() : 'N/A'}</p>
                </div>
                <div>
                  <p className="text-gray-600 text-xs">Type</p>
                  <p className="font-semibold">{trade.order_type || trade.type || 'N/A'}</p>
                </div>
                {trade.price && (
                  <div>
                    <p className="text-gray-600 text-xs">Price</p>
                    <p className="font-semibold">{formatCurrency(trade.price)}</p>
                  </div>
                )}
              </div>

              {trade.client_name && (
                <div className="mt-2 pt-2 border-t border-gray-200">
                  <p className="text-xs text-gray-600">Client: <span className="font-semibold">{trade.client_name}</span></p>
                </div>
              )}
            </Tile>
          ))}
        </div>
      )}

      {!expanded && trades.length > 5 && (
        <Button kind="ghost" size="sm" className="w-full mt-4">
          View All {trades.length} Trades
        </Button>
      )}
    </Tile>
  );
}
