import { useState, useEffect } from 'react';
import { Tile, Button, TextArea, TextInput, Select, SelectItem, ProgressBar } from '@carbon/react';
import { Upload, CheckmarkFilled, WarningAlt, ErrorFilled, Document } from '@carbon/icons-react';
import axios from 'axios';
import { toast } from 'sonner';
const API_BASE = 'http:
export default function ComplianceInputPanel({ onAnalysisComplete, token }) {
  const [transcript, setTranscript] = useState('');
  const [audioFile, setAudioFile] = useState(null);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [tradeTicket, setTradeTicket] = useState({
    ticker: '',
    quantity: '',
    intended_price: '',
    executed_price: '',
    order_type: 'MARKET'
  });
  const [clientProfile, setClientProfile] = useState({
    risk_tolerance: 'Conservative',
    age_category: 'Elderly',
    net_worth: 'Medium'
  });
  const [analyzing, setAnalyzing] = useState(false);
  const [complianceScore, setComplianceScore] = useState(null);
  const [executiveSummary, setExecutiveSummary] = useState('No analysis performed yet.');
  const [auditLogs, setAuditLogs] = useState([]);
  useEffect(() => {
    fetchAuditLogs();
    fetchExecutiveSummary();
  }, []);
  const handleAuditIt = async () => {
    if (!transcript.trim()) {
      toast.error('No transcript to audit. Please upload audio or enter transcript first.');
      return;
    }
    const loadingToast = toast.loading('Saving transcript to audit document...');
    try {
      const response = await axios.post(`${API_BASE}/audit-transcript`, {
        transcript: transcript,
        timestamp: new Date().toISOString()
      });
      toast.dismiss(loadingToast);
      if (response.data.success) {
        toast.success('✅ Transcript audited and saved to Word document');
        fetchAuditLogs();
        fetchExecutiveSummary();
      } else {
        toast.error(response.data.error || 'Failed to audit transcript');
      }
    } catch (error) {
      toast.dismiss(loadingToast);
      console.error('Audit error:', error);
      toast.error(error.response?.data?.detail || 'Failed to audit transcript');
    }
  };
  const fetchAuditLogs = async () => {
    try {
      const response = await axios.get(`${API_BASE}/audit-logs`);
      if (response.data.success) {
        setAuditLogs(response.data.logs || []);
      }
    } catch (error) {
      console.error('Failed to fetch audit logs:', error);
    }
  };
  const fetchExecutiveSummary = async () => {
    try {
      const response = await axios.get(`${API_BASE}/executive-summary`);
      if (response.data.success) {
        setExecutiveSummary(response.data.summary || 'No analysis performed yet.');
      }
    } catch (error) {
      console.error('Failed to fetch executive summary:', error);
    }
  };
  const handleGenerateReport = async () => {
    const loadingToast = toast.loading('Generating Client Portfolio Report with RAG analysis...');
    try {
      const response = await axios.post(`${API_BASE}/generate-portfolio-report`, {
        trigger_rag: true
      });
      toast.dismiss(loadingToast);
      if (response.data.success) {
        toast.success('📄 Client Portfolio Report generated successfully');
        window.open(`${API_BASE}/download-portfolio-report`, '_blank');
        fetchExecutiveSummary();
      } else {
        toast.error(response.data.error || 'Failed to generate report');
      }
    } catch (error) {
      toast.dismiss(loadingToast);
      console.error('Report generation error:', error);
      toast.error(error.response?.data?.detail || 'Failed to generate report');
    }
  };
  const handleEmailSupervisor = async () => {
    const loadingToast = toast.loading('Sending email to supervisor...');
    try {
      const response = await axios.post(`${API_BASE}/email-supervisor`, {
        timestamp: new Date().toISOString()
      });
      toast.dismiss(loadingToast);
      if (response.data.success) {
        toast.success('📧 Email sent to supervisor with attachments');
      } else {
        toast.error(response.data.error || 'Failed to send email');
      }
    } catch (error) {
      toast.dismiss(loadingToast);
      console.error('Email error:', error);
      toast.error(error.response?.data?.detail || 'Failed to send email');
    }
  };
  const handleAudioUpload = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    const validTypes = ['audio/mpeg', 'audio/wav', 'audio/mp4', 'audio/x-m4a', 'audio/webm', 'audio/flac', 'audio/ogg'];
    if (!validTypes.includes(file.type)) {
      toast.error('Invalid file type. Please upload MP3, WAV, M4A, WEBM, FLAC, or OGG files.');
      return;
    }
    const maxSize = 100 * 1024 * 1024;
    if (file.size > maxSize) {
      toast.error('File too large. Maximum size is 100MB.');
      return;
    }
    setAudioFile(file);
    setIsTranscribing(true);
    const loadingToast = toast.loading('Transcribing audio with IBM Watson STT...');
    try {
      const formData = new FormData();
      formData.append('file', file);
      const response = await axios.post(`${API_BASE}/transcribe-audio`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      toast.dismiss(loadingToast);
      if (response.data.success) {
        const { transcript: transcribedText, confidence } = response.data;
        setTranscript(transcribedText);
        if (confidence < 0.7) {
          toast.warning(`Transcribed with ${Math.round(confidence * 100)}% confidence - Please review`);
        } else {
          toast.success(`Transcribed (${Math.round(confidence * 100)}% confidence)`);
        }
      } else {
        toast.error(response.data.error || 'Failed to transcribe audio');
      }
    } catch (error) {
      toast.dismiss(loadingToast);
      console.error('Audio transcription error:', error);
      toast.error(error.response?.data?.detail || 'Failed to transcribe audio');
    } finally {
      setIsTranscribing(false);
    }
  };
  const handleAnalyze = async () => {
    if (!transcript.trim()) {
      toast.error('Please enter a transcript or upload audio file');
      return;
    }
    if (!tradeTicket.ticker || !tradeTicket.executed_price) {
      toast.error('Please fill in required trade ticket fields (Ticker, Executed Price)');
      return;
    }
    if (!token) {
      toast.error('Authentication token not available. Please refresh the page.');
      return;
    }
    if (isNaN(parseFloat(tradeTicket.executed_price))) {
      toast.error('Executed price must be a valid number');
      return;
    }
    if (tradeTicket.quantity && isNaN(parseInt(tradeTicket.quantity))) {
      toast.error('Quantity must be a valid number');
      return;
    }
    setAnalyzing(true);
    try {
      const response = await axios.post(
        `${API_BASE}/analyze_compliance`,
        {
          transcript: transcript,
          execution_log: {
            ticker: tradeTicket.ticker,
            quantity: parseInt(tradeTicket.quantity),
            intended_price: tradeTicket.intended_price ? parseFloat(tradeTicket.intended_price) : null,
            executed_price: parseFloat(tradeTicket.executed_price),
            order_type: tradeTicket.order_type,
            timestamp: new Date().toISOString()
          },
          client_profile: clientProfile,
          trader_id: 'Trader_555'
        },
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );
      onAnalysisComplete(response.data);
      const score = response.data.compliance_score || 0;
      setComplianceScore(score);
      fetchExecutiveSummary();
      const violations = response.data.violations?.length || 0;
      if (violations === 0) {
        toast.success(`✅ Analysis Complete - Compliance Score: ${score.toFixed(0)}% - No violations detected`);
      } else {
        toast.warning(`⚠️ Analysis Complete - ${violations} violation(s) found - Score: ${score.toFixed(0)}%`);
      }
    } catch (error) {
      console.error('Analysis error:', error);
      if (error.response) {
        if (error.response.status === 401) {
          toast.error('Authentication failed. Please refresh the page.');
        } else if (error.response.status === 422) {
          toast.error('Invalid data format. Please check your inputs.');
        } else {
          toast.error(`Server error: ${error.response.data?.detail || 'Failed to analyze compliance'}`);
        }
      } else if (error.request) {
        toast.error('Cannot connect to server. Please ensure backend is running on port 8000.');
      } else {
        toast.error('Failed to analyze compliance. Please try again.');
      }
    } finally {
      setAnalyzing(false);
    }
  };
  const loadSampleData = () => {
    setTranscript(
      `Broker: Good morning, Mr. Peterson. I have an exciting opportunity for you.
Client: Oh? What is it?
Broker: High-yield cryptocurrency fund. We're seeing 40% returns this quarter.
Client: That sounds risky. I'm retired and need stable income.
Broker: Don't worry, everyone's doing it. I'll put you down for $100,000.
Client: Well... if you think it's okay...
Broker: Trust me, you'll thank me later. Executing now at market price.`
    );
    setTradeTicket({
      ticker: 'CRYPTO-X',
      quantity: '1000',
      intended_price: '95.00',
      executed_price: '101.50',
      order_type: 'MARKET'
    });
    setClientProfile({
      risk_tolerance: 'Conservative',
      age_category: 'Elderly',
      net_worth: 'Medium'
    });
    setComplianceScore(35);
    toast.success('⚠️ Sample data loaded - High risk scenario');
  };
  return (
    <div className="h-full overflow-y-auto p-6 bg-gray-950">
      <div className="max-w-7xl mx-auto">
        <div className="mb-6">
          <h2 className="text-3xl mb-2 text-blue-400" style={{ fontFamily: 'IBM Plex Sans', fontWeight: 300, letterSpacing: '-0.015em' }}>
            SEC Compliance Analysis
          </h2>
          <p className="text-sm text-gray-400" style={{ fontFamily: 'IBM Plex Sans', fontWeight: 400 }}>
            End-to-end workflow for investigating broker-client communications
          </p>
        </div>
        <div className="space-y-4">
          {}
          <Tile className="border border-blue-600/40 bg-gray-900/90 backdrop-blur-sm">
            <div className="mb-4 flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-blue-600/20 flex items-center justify-center text-blue-400 font-bold text-sm">1</div>
              <div>
                <h3 className="text-lg font-semibold text-blue-300" style={{ fontFamily: 'IBM Plex Sans' }}>
                  Evidence - Broker Communication
                </h3>
                <p className="text-xs text-gray-400">The "Ground Truth" - what the client actually said</p>
              </div>
            </div>
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-semibold mb-2 text-gray-300">
                  Client-Broker Transcript
                </label>
                <TextArea
                  id="transcript"
                  value={transcript}
                  onChange={(e) => setTranscript(e.target.value)}
                  placeholder="Paste conversation transcript or upload audio below for auto-transcription..."
                  rows={6}
                  className="w-full"
                />
              </div>
              <div className="border border-dashed border-blue-600/40 rounded-lg p-4 bg-gray-800/50">
                <div className="flex items-center gap-2 mb-2">
                  <Upload size={20} className="text-blue-400" />
                  <p className="text-sm font-semibold text-blue-300">Upload Call (IBM Watson STT)</p>
                </div>
                <input
                  type="file"
                  accept=".mp3,.wav,.m4a,.webm,.flac,.ogg"
                  onChange={handleAudioUpload}
                  disabled={isTranscribing}
                  className="w-full text-sm text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-semibold file:bg-blue-600 file:text-white hover:file:bg-blue-700 file:cursor-pointer"
                />
                <p className="text-xs text-gray-500 mt-2">MP3, WAV, M4A, WEBM, FLAC, OGG (Max 100MB) - Auto-transcription via IBM Watson</p>
                {audioFile && (
                  <p className="text-xs text-green-400 mt-2">
                    ✓ {audioFile.name} ({(audioFile.size / 1024 / 1024).toFixed(2)} MB)
                  </p>
                )}
                {isTranscribing && (
                  <p className="text-xs text-blue-400 mt-2 animate-pulse">⏳ Transcribing with Watson STT...</p>
                )}
              </div>
              {transcript.trim() && (
                <Button
                  kind="primary"
                  size="md"
                  className="w-full"
                  renderIcon={Document}
                  onClick={handleAuditIt}
                >
                  📋 Audit It - Save to Word Document
                </Button>
              )}
            </div>
          </Tile>
          {}
          <Tile className="border border-green-600/40 bg-gray-900/90 backdrop-blur-sm">
            <div className="mb-4 flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-green-600/20 flex items-center justify-center text-green-400 font-bold text-sm">2</div>
              <div>
                <h3 className="text-lg font-semibold text-green-300" style={{ fontFamily: 'IBM Plex Sans' }}>
                  Trade Execution Log
                </h3>
                <p className="text-xs text-gray-400">Used for Slippage Check - flags Best Execution Violations</p>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <TextInput
                id="ticker"
                labelText="Ticker Symbol"
                value={tradeTicket.ticker}
                onChange={(e) => setTradeTicket({...tradeTicket, ticker: e.target.value})}
                placeholder="AAPL"
              />
              <TextInput
                id="quantity"
                labelText="Quantity"
                type="number"
                value={tradeTicket.quantity}
                onChange={(e) => setTradeTicket({...tradeTicket, quantity: e.target.value})}
                placeholder="100"
              />
              <TextInput
                id="intended_price"
                labelText="Intended Price"
                type="number"
                step="0.01"
                value={tradeTicket.intended_price}
                onChange={(e) => setTradeTicket({...tradeTicket, intended_price: e.target.value})}
                placeholder="150.00"
              />
              <TextInput
                id="executed_price"
                labelText="Executed Price *"
                type="number"
                step="0.01"
                value={tradeTicket.executed_price}
                onChange={(e) => setTradeTicket({...tradeTicket, executed_price: e.target.value})}
                placeholder="152.50"
              />
              <Select
                id="order_type"
                labelText="Order Type"
                value={tradeTicket.order_type}
                onChange={(e) => setTradeTicket({...tradeTicket, order_type: e.target.value})}
                className="col-span-2"
              >
                <SelectItem value="MARKET" text="Market Order" />
                <SelectItem value="LIMIT" text="Limit Order" />
              </Select>
            </div>
            {tradeTicket.intended_price && tradeTicket.executed_price && (
              <div className="mt-3 p-2 bg-gray-800/70 rounded border border-yellow-600/30">
                <p className="text-xs text-yellow-300">
                  💡 Slippage: ${Math.abs(parseFloat(tradeTicket.executed_price) - parseFloat(tradeTicket.intended_price)).toFixed(2)}
                  {Math.abs(parseFloat(tradeTicket.executed_price) - parseFloat(tradeTicket.intended_price)) > 3 && 
                    <span className="text-red-400 font-semibold"> ⚠️ Exceeds 3% threshold</span>
                  }
                </p>
              </div>
            )}
          </Tile>
          {}
          <Tile className="border border-purple-600/40 bg-gray-900/90 backdrop-blur-sm">
            <div className="mb-4 flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-purple-600/20 flex items-center justify-center text-purple-400 font-bold text-sm">3</div>
              <div>
                <h3 className="text-lg font-semibold text-purple-300" style={{ fontFamily: 'IBM Plex Sans' }}>
                  Client Suitability Profile (KYC)
                </h3>
                <p className="text-xs text-gray-400">Elderly+Conservative with High Risk = Abuse Alert</p>
              </div>
            </div>
            <div className="space-y-3">
              <Select
                id="risk_tolerance"
                labelText="Risk Tolerance"
                value={clientProfile.risk_tolerance}
                onChange={(e) => setClientProfile({...clientProfile, risk_tolerance: e.target.value})}
              >
                <SelectItem value="Conservative" text="Conservative" />
                <SelectItem value="Moderate" text="Moderate" />
                <SelectItem value="Aggressive" text="Aggressive" />
              </Select>
              <Select
                id="age_category"
                labelText="Age Category"
                value={clientProfile.age_category}
                onChange={(e) => setClientProfile({...clientProfile, age_category: e.target.value})}
              >
                <SelectItem value="Young" text="Young (< 35)" />
                <SelectItem value="Middle-Age" text="Middle-Age (35-60)" />
                <SelectItem value="Elderly" text="Elderly (60+)" />
              </Select>
              <Select
                id="net_worth"
                labelText="Net Worth"
                value={clientProfile.net_worth}
                onChange={(e) => setClientProfile({...clientProfile, net_worth: e.target.value})}
              >
                <SelectItem value="Low" text="Low (< $500K)" />
                <SelectItem value="Medium" text="Medium ($500K - $5M)" />
                <SelectItem value="High" text="High (> $5M)" />
              </Select>
            </div>
            {clientProfile.risk_tolerance === 'Conservative' && clientProfile.age_category === 'Elderly' && (
              <div className="mt-3 p-2 bg-red-900/30 rounded border border-red-600/40">
                <p className="text-xs text-red-300">
                  ⚠️ High Risk Alert: Elderly Conservative investor - monitor for unsuitable recommendations
                </p>
              </div>
            )}
          </Tile>
        </div>
        <div className="mt-4 flex justify-end">
          <Button kind="secondary" size="sm" onClick={loadSampleData}>
            Load Sample Data
          </Button>
        </div>
      </div>
    </div>
  );
}
