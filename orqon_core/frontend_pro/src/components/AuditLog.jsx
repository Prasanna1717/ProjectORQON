import { 
  Tile, 
  Tag, 
  Button,
  DataTable,
  TableContainer,
  Table,
  TableHead,
  TableRow,
  TableHeader,
  TableBody,
  TableCell
} from '@carbon/react';
import { Document, Checkmark, WarningAlt, MisuseOutline } from '@carbon/icons-react';

export default function AuditLog({ trades, auditTrail = [] }) {
  // Transform trades into audit log format
  const auditLogData = trades.map((trade, idx) => ({
    id: idx,
    instructionIntent: `${trade.action} ${trade.quantity} shares of ${trade.asset || trade.ticker} ${
      trade.order_type === 'LIMIT' && trade.price ? `@ Limit $${trade.price}` : '@ Market'
    }`,
    executionStatus: trade.compliance_status || 'COMPLIANT',
    riskScore: trade.risk_score || Math.floor(Math.random() * 30) + 10,
    auditTrail: `${new Date(trade.timestamp).toLocaleTimeString()} - ${
      trade.client_name || 'Client'
    } ${trade.order_type} order`,
    slippage: trade.slippage_percent || null,
    trade: trade
  }));

  const getStatusIcon = (status) => {
    switch (status) {
      case 'COMPLIANT':
        return <Checkmark size={20} className="text-green-600" />;
      case 'SLIPPAGE_WARNING':
        return <WarningAlt size={20} className="text-yellow-600" />;
      case 'VIOLATION':
        return <MisuseOutline size={20} className="text-red-600" />;
      default:
        return <Checkmark size={20} className="text-gray-600" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'COMPLIANT':
        return 'green';
      case 'SLIPPAGE_WARNING':
        return 'yellow';
      case 'VIOLATION':
        return 'red';
      default:
        return 'gray';
    }
  };

  const getRiskColor = (score) => {
    if (score >= 70) return 'bg-red-100 text-red-700 border-red-400';
    if (score >= 40) return 'bg-yellow-100 text-yellow-700 border-yellow-400';
    return 'bg-green-100 text-green-700 border-green-400';
  };

  const headers = [
    { key: 'instructionIntent', header: 'Instruction Intent' },
    { key: 'executionStatus', header: 'Execution Status' },
    { key: 'riskScore', header: 'Risk Score' },
    { key: 'auditTrail', header: 'Audit Trail' },
  ];

  return (
    <Tile className="border border-blue-600/40 bg-gray-900/60 backdrop-blur-sm">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Document size={20} className="text-blue-400" />
          <h3 className="text-2xl text-blue-400" style={{ fontFamily: 'IBM Plex Sans', fontWeight: 300, letterSpacing: '-0.01em' }}>Compliance Audit Log</h3>
        </div>
        <Button kind="ghost" size="sm">
          Export Audit Trail
        </Button>
      </div>

      {auditLogData.length === 0 ? (
        <div className="py-8 text-center">
          <p className="text-gray-600 text-sm">No trades to audit</p>
        </div>
      ) : (
        <div className="bg-white border-2 border-gray-400 rounded-lg overflow-hidden">
          <DataTable rows={auditLogData} headers={headers}>
            {({ rows, headers, getTableProps, getHeaderProps, getRowProps }) => (
              <TableContainer>
                <Table {...getTableProps()}>
                  <TableHead>
                    <TableRow>
                      {headers.map((header) => (
                        <TableHeader key={header.key} {...getHeaderProps({ header })}>
                          {header.header}
                        </TableHeader>
                      ))}
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {rows.map((row) => {
                      const rowData = auditLogData.find(d => d.id === row.id);
                      return (
                        <TableRow key={row.id} {...getRowProps({ row })}>
                          <TableCell>
                            <div className="font-mono text-sm">{rowData.instructionIntent}</div>
                          </TableCell>
                          <TableCell>
                            <div className="flex items-center gap-2">
                              {getStatusIcon(rowData.executionStatus)}
                              <Tag type={getStatusColor(rowData.executionStatus)}>
                                {rowData.executionStatus}
                              </Tag>
                              {rowData.slippage && (
                                <span className="text-xs text-red-600 font-semibold">
                                  ({rowData.slippage.toFixed(2)}% slippage)
                                </span>
                              )}
                            </div>
                          </TableCell>
                          <TableCell>
                            <div className={`inline-block px-3 py-1 rounded-full border-2 text-sm font-bold ${
                              getRiskColor(rowData.riskScore)
                            }`}>
                              {rowData.riskScore}
                            </div>
                          </TableCell>
                          <TableCell>
                            <div className="text-sm text-gray-700">{rowData.auditTrail}</div>
                            {rowData.trade.client_name && (
                              <div className="text-xs text-gray-500 mt-1">
                                Client: {rowData.trade.client_name}
                              </div>
                            )}
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </DataTable>
        </div>
      )}
    </Tile>
  );
}
