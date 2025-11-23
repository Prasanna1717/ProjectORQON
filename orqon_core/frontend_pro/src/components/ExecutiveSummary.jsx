import { useState, useEffect } from 'react';
import { Tile, Button } from '@carbon/react';
import { Document, Email, WarningAlt, CheckmarkFilled, ErrorFilled } from '@carbon/icons-react';
import axios from 'axios';
import { toast } from 'sonner';
const API_BASE = 'http:
export default function ExecutiveSummary({ complianceData }) {
  const [executiveSummary, setExecutiveSummary] = useState('No analysis performed yet.');
  const [auditLogs, setAuditLogs] = useState([]);
  const {
    compliance_score = 100,
    violations = [],
    summary = executiveSummary,
    recommendations = []
  } = complianceData || {};
  useEffect(() => {
    fetchExecutiveSummary();
    fetchAuditLogs();
  }, [complianceData]);
  const fetchExecutiveSummary = async () => {
    try {
      const response = await axios.get(`${API_BASE}/executive-summary`);
      if (response.data.success) {
        setExecutiveSummary(response.data.summary);
      }
    } catch (error) {
      console.error('Failed to fetch executive summary:', error);
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
  const handleGenerateReport = async () => {
    const loadingToast = toast.loading('Generating Client Portfolio Report with RAG analysis...');
    try {
      const response = await axios.post(`${API_BASE}/generate-portfolio-report`, {
        trigger_rag: true
      });
      toast.dismiss(loadingToast);
      if (response.data.success) {
        toast.success('📄 Client Portfolio Report generated successfully');
        await axios.get(`${API_BASE}/download-portfolio-report`);
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
  const getScoreColor = (score) => {
    if (score >= 90) return 'text-green-600';
    if (score >= 70) return 'text-yellow-600';
    return 'text-red-600';
  };
  const getScoreBg = (score) => {
    if (score >= 90) return 'bg-green-50 border-green-400';
    if (score >= 70) return 'bg-yellow-50 border-yellow-400';
    return 'bg-red-50 border-red-400';
  };
  return (
    <Tile className="border border-blue-600/40 bg-gray-900/90 backdrop-blur-sm shadow-[inset_0_0_30px_rgba(59,130,246,0.08)]">
      <div className="mb-4">
        <h2 className="text-xl font-bold mb-2 text-blue-300">Compliance Officer Review: Q4-2025</h2>
        {}
        <div className="mb-4 border border-blue-600/40 rounded-lg p-4 bg-blue-950/30">
          <p className="text-xs text-blue-300 mb-2 font-semibold">Compliance Score</p>
          <div className="flex items-center justify-between">
            <p className="text-4xl font-bold text-blue-400">
              {compliance_score.toFixed(0)}%
            </p>
            <div className="flex items-center gap-2">
              {compliance_score >= 90 ? (
                <>
                  <CheckmarkFilled size={24} className="text-green-400" />
                  <span className="text-sm text-green-400 font-semibold">Perfect</span>
                </>
              ) : compliance_score >= 50 ? (
                <>
                  <WarningAlt size={24} className="text-yellow-400" />
                  <span className="text-sm text-yellow-400 font-semibold">Warnings</span>
                </>
              ) : (
                <>
                  <ErrorFilled size={24} className="text-red-400" />
                  <span className="text-sm text-red-400 font-semibold">Violations</span>
                </>
              )}
            </div>
          </div>
        </div>
      </div>
      <div className="mb-4 p-4 bg-gray-800/70 backdrop-blur-sm border border-blue-600/30 rounded-lg">
        <h3 className="text-sm font-semibold mb-2 text-blue-300">Executive Summary:</h3>
        <p className="text-sm text-gray-300">{executiveSummary}</p>
      </div>
      {violations.length > 0 && (
        <div className="mb-4 space-y-2 p-4 bg-gray-800/70 backdrop-blur-sm border border-blue-600/30 rounded-lg shadow-[inset_0_0_20px_rgba(59,130,246,0.1)]">
          <h3 className="text-sm font-semibold text-blue-300">Critical Violations:</h3>
          {violations.map((violation, idx) => (
            <div key={idx} className={`p-3 rounded-lg border-2 ${
              violation.severity === 'CRITICAL' ? 'bg-red-50 border-red-400' : 'bg-yellow-50 border-yellow-400'
            }`}>
              <div className="flex justify-between items-start mb-1">
                <p className="text-xs font-bold text-gray-700">{violation.violation_type.replace(/_/g, ' ')}</p>
                <span className={`px-2 py-1 rounded text-xs font-bold ${
                  violation.severity === 'CRITICAL' ? 'bg-red-600 text-white' : 'bg-yellow-600 text-white'
                }`}>
                  {violation.severity}
                </span>
              </div>
              <p className="text-sm text-gray-700">{violation.description}</p>
            </div>
          ))}
        </div>
      )}
      {recommendations.length > 0 && (
        <div className="mb-4 p-4 bg-gray-800/70 backdrop-blur-sm border border-blue-600/30 rounded-lg shadow-[inset_0_0_20px_rgba(59,130,246,0.1)]">
          <h3 className="text-sm font-semibold mb-2 text-blue-300">Action Items:</h3>
          <div className="space-y-2">
            {recommendations.map((rec, idx) => (
              <p key={idx} className="text-sm text-gray-100 pl-4 border-l-2 border-blue-400">
                • {rec}
              </p>
            ))}
          </div>
        </div>
      )}
      <div className="flex gap-2 mb-4">
        <Button 
          kind="primary" 
          size="sm"
          renderIcon={Document}
          onClick={handleGenerateReport}
        >
          📄 Client Portfolio Report
        </Button>
        <Button 
          kind="secondary" 
          size="sm"
          renderIcon={Email}
          onClick={handleEmailSupervisor}
        >
          📧 Email Supervisor
        </Button>
      </div>
      {}
      <div className="border-t border-blue-600/30 pt-4">
        <h3 className="text-sm font-semibold mb-3 text-cyan-300 flex items-center gap-2">
          <Document size={16} className="text-cyan-400" />
          Compliance Audit Log
        </h3>
        <div className="max-h-64 overflow-y-auto">
          {auditLogs.length > 0 ? (
            <div className="space-y-2">
              {auditLogs.map((log, index) => (
                <div key={index} className="p-3 bg-gray-800/50 border border-cyan-600/30 rounded-lg hover:bg-gray-800/70 transition-colors">
                  <div className="flex justify-between items-start mb-1">
                    <span className="text-xs text-gray-400">{log.timestamp}</span>
                    <span className="px-2 py-0.5 rounded bg-cyan-900/30 text-cyan-400 text-xs font-semibold">
                      v{log.version}
                    </span>
                  </div>
                  <p className="text-xs text-gray-300">{log.preview}</p>
                  <span className="inline-block mt-1 px-2 py-0.5 rounded bg-green-900/30 text-green-400 text-xs">
                    {log.status}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-6 text-gray-500">
              <Document size={32} className="mx-auto mb-2 text-gray-600" />
              <p className="text-xs">No audit logs yet</p>
            </div>
          )}
        </div>
      </div>
    </Tile>
  );
}
