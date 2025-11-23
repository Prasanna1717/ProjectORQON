/**
 * Professional Chat Interface for Trade Parsing
 * IBM Carbon Design System
 */
import { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { useAudioRecorder } from 'react-audio-voice-recorder';
import { useDropzone } from 'react-dropzone';
import {
  TextInput,
  Button,
  Tile,
  ProgressBar,
  Tag,
  DataTable,
  TableContainer,
  Table,
  TableHead,
  TableRow,
  TableHeader,
  TableBody,
  TableCell
} from '@carbon/react';
import {
  Send,
  Microphone,
  MicrophoneOff,
  Upload,
  ArrowUp,
  Currency
} from '@carbon/icons-react';
import { toast } from 'sonner';

const API_BASE = 'http://localhost:8003';

export default function ChatInterface({ onTradeCreated }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [token, setToken] = useState(null);
  const [conversationId, setConversationId] = useState(null);
  const [savingTrades, setSavingTrades] = useState(false);
  const messagesEndRef = useRef(null);
  
  // Audio recording
  const {
    startRecording,
    stopRecording,
    recordingBlob,
    isRecording,
  } = useAudioRecorder();
  
  // File upload
  const onDrop = (acceptedFiles) => {
    handleFileUpload(acceptedFiles[0]);
  };
  
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/plain': ['.txt'],
      'application/pdf': ['.pdf'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'image/jpeg': ['.jpg', '.jpeg'],
      'image/png': ['.png']
    },
    maxFiles: 1,
    maxSize: 10 * 1024 * 1024
  });

  // Authenticate on mount
  useEffect(() => {
    authenticateUser();
  }, []);

  // Handle recording blob
  useEffect(() => {
    if (recordingBlob) {
      handleAudioTranscription(recordingBlob);
    }
  }, [recordingBlob]);

  // Auto-scroll messages - contained within chat container only
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'nearest' });
    }
  }, [messages]);

  const authenticateUser = async () => {
    try {
      const response = await axios.post(`${API_BASE}/auth/token`, {
        user_email: 'trader@orqon.com',
        user_id: 'trader_001'
      });
      setToken(response.data.access_token);
    } catch (error) {
      console.error('Authentication failed:', error);
      // Set a dummy token to allow the app to work anyway
      setToken('demo_token_trader_001');
    }
  };

  const sendMessage = async (messageText) => {
    if (!messageText.trim()) return;

    const userMessage = {
      type: 'user',
      text: messageText,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await axios.post(
        `${API_BASE}/chat`,
        {
          message: messageText,
          conversation_id: conversationId
        },
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );

      const { response: responseText, parsed_trade, conversation_id, tableData } = response.data;
      
      console.log('=== BACKEND RESPONSE DEBUG ===');
      console.log('Full response.data:', JSON.stringify(response.data, null, 2));
      console.log('responseText value:', responseText);
      console.log('responseText type:', typeof responseText);
      console.log('responseText length:', responseText?.length);
      console.log('TableData received:', tableData);
      console.log('===========================');
      
      // Determine message type - check if it's an actual error message
      const isError = responseText && responseText.includes('❌') && responseText.includes('Could not parse trade command');
      const messageType = isError ? 'error' : 'assistant';
      
      const assistantMessage = {
        type: messageType,
        text: responseText || 'No response text received',
        trade: parsed_trade,
        tableData: tableData,
        timestamp: new Date().toISOString()
      };
      
      console.log('Assistant message created:', JSON.stringify(assistantMessage, null, 2));

      setMessages(prev => [...prev, assistantMessage]);
      setConversationId(conversation_id);

      if (parsed_trade && onTradeCreated) {
        onTradeCreated(parsed_trade);
        toast.success('Trade parsed successfully');
      }
      // Don't show warning for conversational messages - only for actual parse failures
    } catch (error) {
      console.error('Chat error:', error);
      const errorMessage = {
        type: 'error',
        text: 'Failed to process message. Please try again.',
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMessage]);
      toast.error('Failed to send message');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    sendMessage(input);
  };

  const toggleRecording = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
      toast.info('Recording started...');
    }
  };

  const handleAudioTranscription = async (audioBlob) => {
    if (!audioBlob) return;
    
    const loadingToast = toast.loading('Transcribing audio with IBM Watson...');
    
    try {
      const formData = new FormData();
      formData.append('file', audioBlob, 'recording.webm');
      
      const response = await axios.post(`${API_BASE}/transcribe-audio`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      
      toast.dismiss(loadingToast);
      
      if (response.data.success) {
        const { transcript, confidence } = response.data;
        
        // Fill input field with transcribed text for user confirmation
        setInput(transcript);
        
        // Show confidence level
        if (confidence < 0.7) {
          toast.warning(`Transcribed with ${Math.round(confidence * 100)}% confidence - Please review`);
        } else {
          toast.success(`Transcribed (${Math.round(confidence * 100)}% confidence) - Review and send`);
        }
      } else {
        toast.error(response.data.error || 'Failed to transcribe audio');
      }
      
    } catch (error) {
      toast.dismiss(loadingToast);
      console.error('Audio transcription error:', error);
      toast.error(error.response?.data?.detail || 'Failed to transcribe audio');
    }
  };

  const handleFileUpload = async (file) => {
    if (!file) return;
    
    const loadingToast = toast.loading(`Parsing document: ${file.name}`);
    
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await axios.post(`${API_BASE}/parse-document`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      
      toast.dismiss(loadingToast);
      
      if (response.data.success) {
        const { parsed_trades, extracted_text, filename, response: backendResponse } = response.data;
        
        if (parsed_trades && parsed_trades.length > 0) {
          toast.success(`Extracted ${parsed_trades.length} trade(s) from ${filename}`);
          
          // Format trades to match expected structure
          const formattedTrades = parsed_trades.map(trade => ({
            ticker: trade.ticker?.toUpperCase() || '',
            action: trade.side?.toUpperCase() || '',
            quantity: trade.quantity || 0,
            order_type: trade.order_type || 'Market',
            price: trade.price || 0,
            client_name: trade.client_name || '',
            account_number: trade.account_number || '',
            solicited: trade.solicited ? 'Solicited' : 'Unsolicited',
            ticket_id: trade.ticket_id || '',
            timestamp: trade.timestamp || new Date().toISOString(),
            notes: trade.notes || '',
            stage: trade.stage || 'Pending',
            meeting_needed: trade.meeting_needed ? 'Yes' : 'No'
          }));
          
          const botMessage = {
            id: Date.now(),
            text: backendResponse || `Successfully extracted ${parsed_trades.length} trade(s) from document.`,
            sender: 'bot',
            timestamp: new Date().toISOString(),
            parsed_trade: { trades: formattedTrades }
          };
          
          setMessages(prev => [...prev, botMessage]);
        } else {
          toast.info(`Document parsed but no trades found in ${filename}`);
          
          const botMessage = {
            id: Date.now(),
            text: `I've read the document "${filename}" but couldn't find any trade information. The document contains:\n\n${extracted_text.substring(0, 300)}...`,
            sender: 'bot',
            timestamp: new Date().toISOString()
          };
          
          setMessages(prev => [...prev, botMessage]);
        }
      } else {
        toast.error(response.data.error || 'Failed to parse document');
      }
      
    } catch (error) {
      toast.dismiss(loadingToast);
      console.error('Document upload error:', error);
      toast.error(error.response?.data?.detail || 'Failed to process document');
    }
  };

  const handleSaveTrades = async (trades) => {
    setSavingTrades(true);
    try {
      const response = await axios.post(`${API_BASE}/save-trades`, {
        trades: trades
      });
      
      if (response.data.success) {
        toast.success(`Successfully saved ${response.data.count} trade(s) to CSV`);
        if (onTradeCreated) {
          trades.forEach(trade => onTradeCreated(trade));
        }
      }
    } catch (error) {
      console.error('Error saving trades:', error);
      toast.error('Failed to save trades to CSV');
    } finally {
      setSavingTrades(false);
    }
  };

  const renderTradeCard = (trade) => {
    if (!trade) return null;

    // Check if this is multiple trades
    if (trade.trades && Array.isArray(trade.trades)) {
      return (
        <div className="mt-3 space-y-3">
          {trade.trades.map((t, idx) => (
            <Tile key={idx} className="bg-gray-800/50 backdrop-blur-sm border border-blue-600/40 shadow-[inset_0_-30px_50px_-15px_rgba(59,130,246,0.12)]">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <ArrowUp size={16} className="text-blue-400" />
                  <h4 className="text-sm font-semibold text-blue-400">Trade {idx + 1}</h4>
                </div>
                <Tag type={t.action === 'BUY' ? 'green' : 'red'}>
                  {t.action}
                </Tag>
              </div>
              
              <div className="grid grid-cols-2 gap-3 text-sm">
                {/* Core Trade Info */}
                <div>
                  <span className="text-gray-400 text-xs">Ticker</span>
                  <p className="font-bold text-lg text-blue-300">{t.ticker}</p>
                </div>
                <div>
                  <span className="text-gray-400 text-xs">Quantity</span>
                  <p className="font-semibold text-gray-100">{t.quantity.toLocaleString()} shares</p>
                </div>
                <div>
                  <span className="text-gray-400 text-xs">Order Type</span>
                  <p className="font-semibold text-gray-100">{t.order_type}</p>
                </div>
                {t.price && (
                  <div>
                    <span className="text-gray-400 text-xs">Price</span>
                    <p className="font-semibold flex items-center gap-1 text-gray-100">
                      <Currency size={16} className="text-blue-400" />
                      {t.price.toFixed(2)}
                    </p>
                  </div>
                )}
                
                {/* Client Info */}
                {t.client_name && (
                  <div>
                    <span className="text-gray-400 text-xs">Client</span>
                    <p className="font-semibold text-gray-100">{t.client_name}</p>
                  </div>
                )}
                {t.account_number && (
                  <div>
                    <span className="text-gray-400 text-xs">Account #</span>
                    <p className="font-semibold text-gray-100">{t.account_number}</p>
                  </div>
                )}
                
                {/* Compliance Info */}
                {t.solicited && (
                  <div>
                    <span className="text-gray-400 text-xs">Type</span>
                    <Tag type={t.solicited === 'Solicited' ? 'blue' : 'gray'}>
                      {t.solicited}
                    </Tag>
                  </div>
                )}
                {t.ticket_id && (
                  <div>
                    <span className="text-gray-400 text-xs">Ticket ID</span>
                    <p className="font-semibold text-gray-100">{t.ticket_id}</p>
                  </div>
                )}
                
                {/* Timestamp & Stage */}
                {t.timestamp && (
                  <div>
                    <span className="text-gray-400 text-xs">Timestamp</span>
                    <p className="font-semibold text-gray-100 text-xs">{t.timestamp}</p>
                  </div>
                )}
                {t.stage && (
                  <div>
                    <span className="text-gray-400 text-xs">Stage</span>
                    <Tag type={t.stage === 'Compliance Review' ? 'red' : 'green'}>
                      {t.stage}
                    </Tag>
                  </div>
                )}
                
                {/* Follow-up Info */}
                {t.email && (
                  <div className="col-span-2">
                    <span className="text-gray-400 text-xs">Email</span>
                    <p className="font-semibold text-gray-100 text-xs truncate">{t.email}</p>
                  </div>
                )}
                {t.follow_up_date && (
                  <div>
                    <span className="text-gray-400 text-xs">Follow-up Date</span>
                    <p className="font-semibold text-gray-100">{t.follow_up_date}</p>
                  </div>
                )}
                {t.meeting_needed && (
                  <div>
                    <span className="text-gray-400 text-xs">Meeting Needed</span>
                    <Tag type={t.meeting_needed === 'Yes' ? 'red' : 'gray'}>
                      {t.meeting_needed}
                    </Tag>
                  </div>
                )}
                
                {/* Notes */}
                {t.notes && (
                  <div className="col-span-2">
                    <span className="text-gray-400 text-xs">Notes</span>
                    <p className="font-semibold text-gray-100 text-xs">{t.notes}</p>
                  </div>
                )}
                
                {/* Confidence */}
                <div className="col-span-2">
                  <span className="text-gray-400 text-xs">Confidence</span>
                  <ProgressBar 
                    label=""
                    value={t.confidence * 100}
                    max={100}
                    size="sm"
                    className="mt-2"
                  />
                  <span className="text-xs font-semibold mt-1 block">{(t.confidence * 100).toFixed(0)}%</span>
                </div>
              </div>
            </Tile>
          ))}
          <Button
            kind="primary"
            size="md"
            onClick={() => handleSaveTrades(trade.trades)}
            disabled={savingTrades}
            className="w-full mt-2"
          >
            {savingTrades ? 'Saving...' : `Confirm & Save ${trade.trades.length} Trade(s) to CSV`}
          </Button>
        </div>
      );
    }

    // Single trade
    const isBuy = trade.action === 'BUY';

    return (
      <>
        <Tile className="mt-3 bg-gray-800/50 backdrop-blur-sm border border-blue-600/40 shadow-[inset_0_-30px_50px_-15px_rgba(59,130,246,0.12)]">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <ArrowUp size={16} className="text-blue-400" />
              <h4 className="text-sm font-semibold text-blue-400">Trade Details</h4>
            </div>
            <Tag type={isBuy ? 'green' : 'red'}>
              {trade.action}
            </Tag>
          </div>
          
          <div className="grid grid-cols-2 gap-3 text-sm">
            {/* Core Trade Info */}
            <div>
              <span className="text-gray-400 text-xs">Ticker</span>
              <p className="font-bold text-lg text-blue-300">{trade.ticker}</p>
            </div>
            <div>
              <span className="text-gray-400 text-xs">Quantity</span>
              <p className="font-semibold text-gray-100">{trade.quantity.toLocaleString()} shares</p>
            </div>
            <div>
              <span className="text-gray-400 text-xs">Order Type</span>
              <p className="font-semibold text-gray-100">{trade.order_type}</p>
            </div>
            {trade.price && (
              <div>
                <span className="text-gray-400 text-xs">Price</span>
                <p className="font-semibold flex items-center gap-1 text-gray-100">
                  <Currency size={16} className="text-blue-400" />
                  {trade.price.toFixed(2)}
                </p>
              </div>
            )}
            
            {/* Client Info */}
            {trade.client_name && (
              <div>
                <span className="text-gray-400 text-xs">Client</span>
                <p className="font-semibold text-gray-100">{trade.client_name}</p>
              </div>
            )}
            {trade.account_number && (
              <div>
                <span className="text-gray-400 text-xs">Account #</span>
                <p className="font-semibold text-gray-100">{trade.account_number}</p>
              </div>
            )}
            
            {/* Compliance Info */}
            {trade.solicited && (
              <div>
                <span className="text-gray-400 text-xs">Type</span>
                <Tag type={trade.solicited === 'Solicited' ? 'blue' : 'gray'}>
                  {trade.solicited}
                </Tag>
              </div>
            )}
            {trade.ticket_id && (
              <div>
                <span className="text-gray-400 text-xs">Ticket ID</span>
                <p className="font-semibold text-gray-100">{trade.ticket_id}</p>
              </div>
            )}
            
            {/* Timestamp & Stage */}
            {trade.timestamp && (
              <div>
                <span className="text-gray-400 text-xs">Timestamp</span>
                <p className="font-semibold text-gray-100 text-xs">{trade.timestamp}</p>
              </div>
            )}
            {trade.stage && (
              <div>
                <span className="text-gray-400 text-xs">Stage</span>
                <Tag type={trade.stage === 'Compliance Review' ? 'red' : 'green'}>
                  {trade.stage}
                </Tag>
              </div>
            )}
            
            {/* Follow-up Info */}
            {trade.email && (
              <div className="col-span-2">
                <span className="text-gray-400 text-xs">Email</span>
                <p className="font-semibold text-gray-100 text-xs truncate">{trade.email}</p>
              </div>
            )}
            {trade.follow_up_date && (
              <div>
                <span className="text-gray-400 text-xs">Follow-up Date</span>
                <p className="font-semibold text-gray-100">{trade.follow_up_date}</p>
              </div>
            )}
            {trade.meeting_needed && (
              <div>
                <span className="text-gray-400 text-xs">Meeting Needed</span>
                <Tag type={trade.meeting_needed === 'Yes' ? 'red' : 'gray'}>
                  {trade.meeting_needed}
                </Tag>
              </div>
            )}
            
            {/* Notes */}
            {trade.notes && (
              <div className="col-span-2">
                <span className="text-gray-400 text-xs">Notes</span>
                <p className="font-semibold text-gray-100 text-xs">{trade.notes}</p>
              </div>
            )}
            
            {/* Confidence */}
            <div className="col-span-2">
              <span className="text-gray-400 text-xs">Confidence</span>
              <ProgressBar 
                label=""
                value={trade.confidence * 100}
                max={100}
                size="sm"
                className="mt-2"
              />
              <span className="text-xs font-semibold mt-1 block">{(trade.confidence * 100).toFixed(0)}%</span>
            </div>
          </div>
        </Tile>
        <Button
          kind="primary"
          size="md"
          onClick={() => handleSaveTrades([trade])}
          disabled={savingTrades}
          className="w-full mt-2"
        >
          {savingTrades ? 'Saving...' : 'Confirm & Save Trade to CSV'}
        </Button>
      </>
    );
  };

  return (
    <Tile className="flex flex-col border border-blue-600/40 bg-gray-900/90 backdrop-blur-sm h-full">
      {/* Header */}
      <div className="px-6 py-4 border-b border-blue-600/30 flex-shrink-0 bg-gray-800/70 backdrop-blur-sm">
        <h2 className="text-3xl text-blue-400" style={{ fontFamily: 'IBM Plex Sans', fontWeight: 300, letterSpacing: '-0.015em' }}>Trade Parser</h2>
        <p className="text-sm text-gray-400" style={{ fontFamily: 'IBM Plex Sans', fontWeight: 400 }}>Natural language trade execution</p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4" style={{ minHeight: 0 }}>
        {messages.length === 0 && (
          <div className="text-center py-12">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gray-800/70 backdrop-blur-sm border border-blue-600/40 mb-4 shadow-[inset_0_0_30px_rgba(59,130,246,0.15)]">
              <ArrowUp size={32} className="text-blue-400" />
            </div>
            <h3 className="text-lg font-semibold mb-2 text-blue-400">Start Trading</h3>
            <p className="text-gray-400 text-sm max-w-md mx-auto">
              Enter trade commands like: "Buy 100 shares of Apple at market" or "Sell 50 TSLA at $250 limit"
            </p>
          </div>
        )}

        {messages.map((msg, idx) => (
          <div key={idx} className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}>
            <Tile 
              className={`${msg.text && (msg.text.includes('<table') || msg.text.includes('{{TABLE_START}}')) ? 'w-full max-w-full' : 'max-w-[80%]'} ${
                msg.type === 'user' 
                  ? 'bg-blue-600/90 backdrop-blur-sm text-white shadow-[inset_0_0_20px_rgba(59,130,246,0.2)] border border-blue-500/50' 
                  : msg.type === 'error'
                  ? 'bg-red-900/80 backdrop-blur-sm text-red-100 border border-red-600/40 shadow-[inset_0_0_20px_rgba(239,68,68,0.15)]'
                  : 'bg-gray-800/80 backdrop-blur-sm text-gray-100 border border-blue-600/30 shadow-[inset_0_0_20px_rgba(59,130,246,0.1)]'
              }`}
            >
              {/* Render table if message contains TABLE markers */}
              {(() => {
                if (msg.text && msg.type === 'assistant') {
                  console.log('Message text sample:', msg.text.substring(0, 100));
                  console.log('Contains TABLE_START?', msg.text.includes('{{TABLE_START}}'));
                  console.log('Contains escaped?', msg.text.includes('{TABLE_START}'));
                }
                return null;
              })()}
              {msg.text && msg.text.includes('{{TABLE_START}}') ? (
                (() => {
                  try {
                    const parts = msg.text.split('{{TABLE_START}}');
                    const headerText = parts[0];
                    const tableJsonMatch = parts[1]?.match(/(.+?){{TABLE_END}}/s);
                    
                    if (!tableJsonMatch) {
                      console.error('No TABLE_END marker found');
                      return <div>{msg.text}</div>;
                    }
                    
                    const jsonStr = tableJsonMatch[1].trim();
                    console.log('Parsing table JSON:', jsonStr.substring(0, 200) + '...');
                    
                    const tableData = JSON.parse(jsonStr);
                    const footerText = parts[1]?.split('{{TABLE_END}}')[1] || '';
                    
                    return (
                      <div className="w-full">
                        {headerText && (
                          <div className="mb-3">
                            {headerText.split('**').map((part, j) => 
                              j % 2 === 0 ? (
                                <span key={j}>{part}</span>
                              ) : (
                                <strong key={j} className="font-bold text-white">{part}</strong>
                              )
                            )}
                          </div>
                        )}
                      
                      
                      {tableData && (
                        <div className="overflow-x-auto" style={{ maxHeight: '600px', overflowY: 'auto' }}>
                          <table className="w-full text-sm" style={{ 
                            borderCollapse: 'collapse',
                            fontFamily: 'IBM Plex Mono, monospace'
                          }}>
                            <thead style={{ position: 'sticky', top: 0, zIndex: 10 }}>
                              <tr style={{ backgroundColor: '#262626', borderBottom: '1px solid #393939' }}>
                                {tableData.headers.map((header, i) => (
                                  <th key={i} style={{ 
                                    padding: '12px 8px',
                                    textAlign: 'left',
                                    fontWeight: 600,
                                    color: '#f4f4f4',
                                    whiteSpace: 'nowrap'
                                  }}>
                                    {header}
                                  </th>
                                ))}
                              </tr>
                            </thead>
                            <tbody>
                              {tableData.rows.map((row, i) => (
                                <tr key={i} style={{ 
                                  backgroundColor: i % 2 === 0 ? '#1a1a1a' : '#161616',
                                  borderBottom: '1px solid #393939'
                                }}>
                                  {row.map((cell, j) => {
                                    const isSideCol = j === 3;
                                    const isTickerCol = j === 4;
                                    const isBuy = cell === 'Buy';
                                    const isSell = cell === 'Sell';
                                    
                                    return (
                                      <td key={j} style={{ 
                                        padding: '12px 8px',
                                        color: isSideCol ? (isBuy ? '#42be65' : isSell ? '#fa4d56' : '#c6c6c6') 
                                             : isTickerCol ? '#78a9ff'
                                             : '#c6c6c6',
                                        fontWeight: isSideCol ? 600 : 'normal',
                                        whiteSpace: 'nowrap'
                                      }}>
                                        {cell}
                                      </td>
                                    );
                                  })}
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      )}
                      
                      {footerText && (
                        <div className="mt-3 text-xs opacity-80">
                          {footerText}
                        </div>
                      )}
                    </div>
                  );
                  } catch (error) {
                    console.error('Error parsing table data:', error);
                    return (
                      <div>
                        <div className="text-red-400 mb-2">Error rendering table</div>
                        <div className="text-xs opacity-70">{msg.text}</div>
                      </div>
                    );
                  }
                })()
              ) : msg.text && msg.text.includes('**') ? (
                // Render markdown-style bold text
                <div className="text-sm leading-relaxed whitespace-pre-wrap" style={{ fontSize: '14px', fontFamily: 'IBM Plex Sans' }}>
                  {msg.text.split('\n').map((line, i) => {
                    const parts = line.split('**');
                    return (
                      <p key={i} className="mb-1" style={{ fontSize: '14px' }}>
                        {parts.map((part, j) => 
                          j % 2 === 0 ? (
                            <span key={j}>{part}</span>
                          ) : (
                            <strong key={j} className="font-bold text-white">{part}</strong>
                          )
                        )}
                      </p>
                    );
                  })}
                </div>
              ) : msg.tableData && msg.tableData.headers && msg.tableData.rows ? (
                <div className="w-full my-4">
                  <h3 className="text-xl font-semibold mb-4 text-blue-400" style={{ fontFamily: 'IBM Plex Sans, sans-serif', letterSpacing: '-0.02em' }}>
                    {msg.tableData.title || '📊 Data Table'}
                  </h3>
                  <div className="overflow-x-auto bg-gray-800 rounded-lg border-2 border-blue-600/30 shadow-lg">
                    <table className="w-full" style={{ 
                      fontFamily: 'IBM Plex Sans, sans-serif',
                      borderCollapse: 'separate',
                      borderSpacing: 0,
                      minWidth: '100%'
                    }}>
                      <thead>
                        <tr className="border-b-2 border-blue-600/50" style={{ backgroundColor: '#262626' }}>
                          {msg.tableData.headers.map((h, i) => (
                            <th key={i} className="px-4 py-4 text-left text-blue-400 font-semibold uppercase tracking-wider whitespace-nowrap border-r border-gray-700/50 last:border-r-0" style={{ 
                              fontFamily: 'IBM Plex Sans, sans-serif',
                              fontSize: '12px',
                              letterSpacing: '0.05em'
                            }}>
                              {h}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {msg.tableData.rows.map((row, i) => (
                          <tr key={i} className="border-b border-gray-700/50 hover:bg-gray-700/50 transition-colors" style={{ backgroundColor: i % 2 === 0 ? '#1a1a1a' : '#161616' }}>
                            {row.map((cell, j) => {
                              const header = msg.tableData.headers[j];
                              const isSide = header === 'Side';
                              const isTicker = header === 'Ticker';
                              const isPrice = header === 'Price';
                              return (
                                <td key={j} className="px-4 py-3 border-r border-gray-700/30 last:border-r-0 whitespace-nowrap" style={{
                                  fontFamily: isPrice ? 'IBM Plex Mono, monospace' : 'IBM Plex Sans, sans-serif',
                                  color: isSide ? (cell === 'Buy' ? '#42be65' : cell === 'Sell' ? '#ff8389' : '#f4f4f4') : 
                                         isTicker ? '#78a9ff' : '#f4f4f4',
                                  fontWeight: (isSide || isTicker) ? '600' : '400',
                                  fontSize: '14px'
                                }}>
                                  {cell}
                                </td>
                              );
                            })}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  {msg.tableData.footer && (
                    <p className="text-sm text-gray-500 mt-3" style={{ fontFamily: 'IBM Plex Sans, sans-serif' }}>{msg.tableData.footer}</p>
                  )}
                </div>
              ) : msg.oldTableDataAttempt ? (
                (() => {
                  console.log('Rendering table with data:', msg.oldTableDataAttempt);
                  try {
                    const headers = msg.tableData.headers.map((h, i) => ({ key: `col${i}`, header: h }));
                    const rows = msg.tableData.rows.map((row, i) => {
                      const rowObj = { id: i };
                      row.forEach((cell, j) => {
                        rowObj[`col${j}`] = cell;
                      });
                      return rowObj;
                    });
                    
                    return (
                      <div className="w-full my-4">
                        {msg.tableData.title && (
                          <h3 className="text-lg font-semibold mb-3 text-blue-400" style={{ fontFamily: 'IBM Plex Sans' }}>
                            {msg.tableData.title}
                          </h3>
                        )}
                      <DataTable rows={rows} headers={headers}>
                        {({ rows, headers, getTableProps, getHeaderProps, getRowProps }) => (
                          <TableContainer className="bg-gray-900/80">
                            <Table {...getTableProps()} size="md">
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
                                  const rowData = msg.tableData.rows[row.id];
                                  return (
                                    <TableRow key={row.id} {...getRowProps({ row })}>
                                      {headers.map((header, colIdx) => {
                                        const cellValue = rowData[colIdx];
                                        const isSide = header.header === 'Side';
                                        const isTicker = header.header === 'Ticker';
                                        
                                        return (
                                          <TableCell key={header.key}>
                                            <span style={{
                                              color: isSide ? (cellValue === 'Buy' ? '#42be65' : cellValue === 'Sell' ? '#ff8389' : '#f4f4f4') : 
                                                     isTicker ? '#78a9ff' : '#f4f4f4',
                                              fontWeight: (isSide || isTicker) ? '600' : '400',
                                              fontFamily: header.header === 'Price' ? 'IBM Plex Mono' : 'IBM Plex Sans'
                                            }}>
                                              {cellValue}
                                            </span>
                                          </TableCell>
                                        );
                                      })}
                                    </TableRow>
                                  );
                                })}
                              </TableBody>
                            </Table>
                          </TableContainer>
                        )}
                      </DataTable>
                        {msg.tableData.footer && (
                          <p className="text-xs text-gray-500 mt-2" style={{ fontFamily: 'IBM Plex Sans' }}>
                            {msg.tableData.footer}
                          </p>
                        )}
                      </div>
                    );
                  } catch (error) {
                    console.error('Error rendering table:', error);
                    return <div className="text-red-400">Error rendering table: {error.message}</div>;
                  }
                })()
              ) : (
                <p className="text-sm leading-relaxed whitespace-pre-wrap" style={{ fontSize: '14px', fontFamily: 'IBM Plex Sans' }}>{msg.text}</p>
              )}
              {(msg.trade || msg.parsed_trade) && renderTradeCard(msg.trade || msg.parsed_trade)}
              <p className="text-xs mt-2 opacity-60" style={{ fontSize: '11px' }}>
                {new Date(msg.timestamp).toLocaleTimeString()}
              </p>
            </Tile>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <Tile className="bg-gray-800/60 backdrop-blur-sm border border-blue-600/30">
              <div className="flex space-x-2">
                <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </Tile>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area - Fixed at bottom */}
      <div className="border-t border-blue-600/30 bg-gray-800/70 backdrop-blur-sm p-4 flex-shrink-0">
        {/* File Upload Drop Zone */}
        <div {...getRootProps()} className={`mb-3 p-3 border border-dashed rounded-lg transition-all duration-300 cursor-pointer ${
          isDragActive ? 'border-blue-400/60 bg-gray-800/60 backdrop-blur-sm shadow-[inset_0_0_25px_rgba(59,130,246,0.2)]' : 'border-blue-600/40 bg-gray-800/30 hover:bg-gray-800/50 hover:border-blue-500/50 hover:shadow-[inset_0_0_20px_rgba(59,130,246,0.12)]'
        }`}>
          <input {...getInputProps()} />
          <div className="flex flex-col items-center justify-center gap-1 text-sm text-gray-400">
            <div className="flex items-center gap-2">
              <Upload size={16} className="text-blue-400" />
              <span>
                {isDragActive ? 'Drop file here' : 'Drag & drop or click to upload document'}
              </span>
            </div>
            <span className="text-xs text-gray-500">
              PDF, DOCX, DOC, TXT, JPG, PNG (Max 10MB)
            </span>
          </div>
        </div>

        {/* Input Form */}
        <form onSubmit={handleSubmit} className="flex gap-2 w-full">
          <div className="flex-1">
            <TextInput
              id="trade-input"
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type trade command (e.g., Buy 100 AAPL at market)..."
              disabled={loading || isRecording}
              labelText=""
              style={{
                backgroundColor: 'rgba(31, 41, 55, 0.9)',
                color: '#f3f4f6',
                border: '1px solid rgba(37, 99, 235, 0.4)'
              }}
            />
          </div>
          
          <Button
            kind="secondary"
            size="md"
            onClick={toggleRecording}
            hasIconOnly
            renderIcon={isRecording ? MicrophoneOff : Microphone}
            iconDescription={isRecording ? "Stop recording" : "Start recording"}
          />
          
          <Button
            kind="primary"
            size="md"
            type="submit"
            disabled={loading || !input.trim() || !token}
            renderIcon={Send}
            iconDescription="Send message"
          >
            Send
          </Button>
        </form>
      </div>
    </Tile>
  );
}



