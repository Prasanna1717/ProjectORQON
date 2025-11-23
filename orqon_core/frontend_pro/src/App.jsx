/**
 * ORQON Trade Intelligence Platform
 * Built with IBM Carbon Design System
 */
import { useState, useEffect } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { 
  Theme,
  Header,
  HeaderName,
  HeaderNavigation,
  HeaderMenuItem,
  HeaderGlobalBar,
  HeaderGlobalAction,
  Content,
  Grid,
  Column
} from '@carbon/react';
import { Notification, UserAvatar, Ai } from '@carbon/icons-react';
import { Toaster } from 'sonner';

// Components
import ChatInterface from './components/ChatInterface.jsx';
import TradeHistory from './components/TradeHistory.jsx';
import MarketOverview from './components/MarketOverview.jsx';
import PerformanceCharts from './components/PerformanceCharts.jsx';
import PortfolioSummary from './components/PortfolioSummary.jsx';
import ComplianceInputPanel from './components/ComplianceInputPanel.jsx';
import ExecutiveSummary from './components/ExecutiveSummary.jsx';
import AuditLog from './components/AuditLog.jsx';
import ComplianceCharts from './components/ComplianceCharts.jsx';

const queryClient = new QueryClient();

function App() {
  const [trades, setTrades] = useState([]);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [complianceData, setComplianceData] = useState(null);
  const [token, setToken] = useState(null);
  const [showAiDropdown, setShowAiDropdown] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);
  const [showProfile, setShowProfile] = useState(false);
  const [notifications, setNotifications] = useState([]);

  // Authenticate on mount
  useEffect(() => {
    const authenticateUser = async () => {
      try {
        const response = await fetch('http://localhost:8000/auth/token', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            user_email: 'compliance@orqon.com',
            user_id: 'compliance_001'
          })
        });
        const data = await response.json();
        setToken(data.access_token);
        console.log('✅ Authentication successful');
      } catch (error) {
        console.error('❌ Auth failed:', error);
      }
    };
    authenticateUser();
  }, []);

  // Fetch notifications (reminders/meetings) from Google Calendar
  useEffect(() => {
    const fetchNotifications = async () => {
      try {
        const response = await fetch('http://localhost:8003/api/calendar/upcoming', {
          method: 'GET',
          headers: { 'Content-Type': 'application/json' }
        });
        
        if (response.ok) {
          const data = await response.json();
          if (data.success && data.events) {
            setNotifications(data.events);
          }
        }
      } catch (error) {
        console.error('❌ Failed to fetch notifications:', error);
      }
    };
    
    fetchNotifications();
    // Refresh every 5 minutes
    const interval = setInterval(fetchNotifications, 300000);
    return () => clearInterval(interval);
  }, []);

  const handleTradeCreated = (trade) => {
    setTrades(prev => [trade, ...prev]);
  };

  const handleComplianceAnalysis = (analysisData) => {
    setComplianceData(analysisData);
    
    // Add compliance data to the last trade
    if (trades.length > 0) {
      const updatedTrades = [...trades];
      updatedTrades[0] = {
        ...updatedTrades[0],
        compliance_status: analysisData.violations.length > 0 ? 'VIOLATION' : 'COMPLIANT',
        risk_score: analysisData.violations[0]?.risk_score || 10,
        slippage_percent: analysisData.slippage_percent
      };
      setTrades(updatedTrades);
    }
  };

  console.log('✅ App loaded - Tab:', activeTab, 'Trades:', trades.length, 'Token:', token ? 'Ready' : 'Loading');

  // Wrap in try-catch
  try {
    return (
      <QueryClientProvider client={queryClient}>
        <Theme theme="g100">
          {/* IBM Carbon Header */}
          <Header aria-label="ORQON Platform">
          <div className="flex items-center gap-2 pl-4" style={{ marginRight: '-1rem' }}>
            <div className="w-8 h-8 flex items-center justify-center">
              <img 
                src="/logo.png" 
                alt="ORQON Logo" 
                className="h-8 w-8 object-contain"
                style={{ filter: 'brightness(1.1)' }}
              />
            </div>
          </div>
          <HeaderName href="#" prefix="Project">
            ORQON
          </HeaderName>
          <HeaderNavigation aria-label="ORQON">
            <HeaderMenuItem 
              onClick={() => setActiveTab('dashboard')}
              isActive={activeTab === 'dashboard'}
            >
              Dashboard
            </HeaderMenuItem>
            <HeaderMenuItem 
              onClick={() => setActiveTab('compliance')}
              isActive={activeTab === 'compliance'}
            >
              Compliance Analysis
            </HeaderMenuItem>
            <HeaderMenuItem 
              onClick={() => setActiveTab('analytics')}
              isActive={activeTab === 'analytics'}
            >
              Analytics
            </HeaderMenuItem>
            <HeaderMenuItem 
              onClick={() => setActiveTab('history')}
              isActive={activeTab === 'history'}
            >
              Trade History
            </HeaderMenuItem>
          </HeaderNavigation>
          <HeaderGlobalBar>
            <HeaderGlobalAction 
              aria-label="AI Assistant" 
              tooltipAlignment="end"
              onClick={() => setShowAiDropdown(!showAiDropdown)}
            >
              <div className="p-1 border border-blue-400/60 rounded">
                <Ai size={20} className="text-blue-400" />
              </div>
            </HeaderGlobalAction>
            {showAiDropdown && (
              <div className="absolute right-16 top-12 w-96 border border-blue-600/40 bg-gray-900/95 backdrop-blur-lg rounded-lg p-6 shadow-[inset_0_-20px_40px_-10px_rgba(59,130,246,0.15)] z-50">
                <div className="flex items-center gap-2 mb-4 pb-3 border-b border-blue-600/30">
                  <Ai size={24} className="text-blue-400" />
                  <h3 className="text-lg font-semibold text-blue-400">ORQON AI Assistant</h3>
                </div>
                <div className="space-y-3 text-sm">
                  <div>
                    <h4 className="font-semibold text-blue-300 mb-1">Project Overview</h4>
                    <p className="text-gray-300">SEC Compliance Analysis Platform powered by IBM watsonx Orchestrate</p>
                  </div>
                  <div>
                    <h4 className="font-semibold text-blue-300 mb-1">Key Features</h4>
                    <ul className="text-gray-300 space-y-1 list-disc list-inside">
                      <li>Real-time trade compliance monitoring</li>
                      <li>AI-powered risk assessment</li>
                      <li>Slippage detection & analysis</li>
                      <li>Natural language trade parsing</li>
                      <li>Automated audit trail generation</li>
                    </ul>
                  </div>
                  <div>
                    <h4 className="font-semibold text-blue-300 mb-1">Technology Stack</h4>
                    <p className="text-gray-300">React + IBM Carbon + watsonx + FastAPI</p>
                  </div>
                  <div className="pt-3 border-t border-blue-600/30">
                    <p className="text-xs text-gray-400">Built with IBM Plex Sans & Carbon Design System</p>
                  </div>
                </div>
              </div>
            )}
            <HeaderGlobalAction 
              aria-label="Notifications" 
              tooltipAlignment="end"
              onClick={() => {
                setShowNotifications(!showNotifications);
                setShowProfile(false);
                setShowAiDropdown(false);
              }}
            >
              <div className="relative">
                <Notification size={20} />
                {notifications.length > 0 && (
                  <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center font-semibold">
                    {notifications.length > 9 ? '9+' : notifications.length}
                  </span>
                )}
              </div>
            </HeaderGlobalAction>
            {showNotifications && (
              <div className="absolute right-16 top-12 w-96 border border-blue-600/40 bg-gray-900/95 backdrop-blur-lg rounded-lg shadow-[inset_0_-20px_40px_-10px_rgba(59,130,246,0.15)] z-50 max-h-96 overflow-y-auto">
                <div className="flex items-center justify-between gap-2 p-4 pb-3 border-b border-blue-600/30 sticky top-0 bg-gray-900/95">
                  <div className="flex items-center gap-2">
                    <Notification size={24} className="text-blue-400" />
                    <h3 className="text-lg font-semibold text-blue-400">Notifications</h3>
                  </div>
                  {notifications.length > 0 && (
                    <span className="text-xs text-gray-400">{notifications.length} upcoming</span>
                  )}
                </div>
                <div className="p-4">
                  {notifications.length === 0 ? (
                    <p className="text-gray-400 text-sm text-center py-8">No upcoming reminders or meetings</p>
                  ) : (
                    <div className="space-y-3">
                      {notifications.map((event, index) => (
                        <div key={index} className="p-3 border border-blue-600/20 rounded-lg bg-gray-800/50 hover:bg-gray-800/80 transition-colors">
                          <h4 className="font-semibold text-blue-300 text-sm mb-1">{event.summary || 'Untitled Event'}</h4>
                          <div className="text-xs text-gray-400 space-y-1">
                            <div className="flex items-center gap-1">
                              <span>📅</span>
                              <span>{new Date(event.start?.dateTime || event.start?.date).toLocaleDateString('en-US', {
                                month: 'short',
                                day: 'numeric',
                                year: 'numeric'
                              })}</span>
                            </div>
                            <div className="flex items-center gap-1">
                              <span>🕐</span>
                              <span>{event.start?.dateTime ? new Date(event.start.dateTime).toLocaleTimeString('en-US', {
                                hour: '2-digit',
                                minute: '2-digit'
                              }) : 'All day'}</span>
                            </div>
                            {event.hangoutLink && (
                              <div className="flex items-center gap-1">
                                <span>📹</span>
                                <a href={event.hangoutLink} target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:text-blue-300">
                                  Join Google Meet
                                </a>
                              </div>
                            )}
                            {event.attendees && event.attendees.length > 0 && (
                              <div className="flex items-center gap-1">
                                <span>👥</span>
                                <span>{event.attendees.length} attendee{event.attendees.length !== 1 ? 's' : ''}</span>
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}
            <HeaderGlobalAction 
              aria-label="User Profile" 
              tooltipAlignment="end"
              onClick={() => {
                setShowProfile(!showProfile);
                setShowNotifications(false);
                setShowAiDropdown(false);
              }}
            >
              <UserAvatar size={20} />
            </HeaderGlobalAction>
            {showProfile && (
              <div className="absolute right-4 top-12 w-80 border border-blue-600/40 bg-gray-900/95 backdrop-blur-lg rounded-lg shadow-[inset_0_-20px_40px_-10px_rgba(59,130,246,0.15)] z-50">
                <div className="flex items-center gap-3 p-6 pb-4 border-b border-blue-600/30">
                  <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-blue-700 rounded-full flex items-center justify-center text-2xl font-bold text-white">
                    PV
                  </div>
                  <div>
                    <h3 className="text-xl font-semibold text-blue-400">Prasanna Vijay</h3>
                    <p className="text-sm text-gray-400">Trade Compliance Officer</p>
                  </div>
                </div>
                <div className="p-6 space-y-4">
                  <div>
                    <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">Contact Information</h4>
                    <div className="space-y-2 text-sm text-gray-300">
                      <div className="flex items-center gap-2">
                        <span className="text-blue-400">📧</span>
                        <span>prasannathefreelancer@gmail.com</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-blue-400">🏢</span>
                        <span>ORQON Trade Intelligence</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-blue-400">📍</span>
                        <span>Remote Workspace</span>
                      </div>
                    </div>
                  </div>
                  <div className="pt-4 border-t border-blue-600/30">
                    <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">Role & Permissions</h4>
                    <div className="flex flex-wrap gap-2">
                      <span className="px-3 py-1 bg-blue-600/20 text-blue-300 text-xs rounded-full border border-blue-600/30">
                        Admin Access
                      </span>
                      <span className="px-3 py-1 bg-green-600/20 text-green-300 text-xs rounded-full border border-green-600/30">
                        Compliance Officer
                      </span>
                      <span className="px-3 py-1 bg-purple-600/20 text-purple-300 text-xs rounded-full border border-purple-600/30">
                        AI Assistant Enabled
                      </span>
                    </div>
                  </div>
                  <div className="pt-4 border-t border-blue-600/30">
                    <button className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold rounded transition-colors">
                      Edit Profile
                    </button>
                    <button className="w-full px-4 py-2 mt-2 border border-gray-600 hover:border-gray-500 text-gray-300 hover:text-white text-sm font-semibold rounded transition-colors">
                      Sign Out
                    </button>
                  </div>
                </div>
              </div>
            )}
          </HeaderGlobalBar>
        </Header>

        {/* Main Content */}
        <Content style={{ height: 'calc(100vh - 48px)', overflow: 'hidden' }}>
          <div style={{ display: activeTab === 'dashboard' ? 'block' : 'none', height: '100%' }}>
            <Grid fullWidth className="h-full" style={{ overflow: 'hidden' }}>
              <Column lg={5} md={4} sm={4} className="h-full" style={{ overflow: 'hidden' }}>
                <div className="space-y-4 p-4 h-full overflow-y-auto">
                  <MarketOverview />
                  <PortfolioSummary trades={trades} />
                </div>
              </Column>
              <Column lg={11} md={4} sm={4} className="h-full" style={{ overflow: 'hidden' }}>
                <div className="h-full p-4">
                  <ChatInterface onTradeCreated={handleTradeCreated} />
                </div>
              </Column>
            </Grid>
          </div>

          <div style={{ display: activeTab === 'compliance' ? 'block' : 'none', height: '100%' }}>
            <Grid fullWidth className="overflow-hidden h-full">
              <Column lg={6} md={4} sm={4} className="h-full overflow-y-auto">
                <div className="p-4 h-full">
                  <ComplianceInputPanel 
                    onAnalysisComplete={handleComplianceAnalysis}
                    token={token}
                  />
                </div>
              </Column>
              <Column lg={10} md={4} sm={4} className="h-full overflow-y-auto">
                <div className="space-y-4 p-4">
                  <ExecutiveSummary complianceData={complianceData} />
                  <ComplianceCharts />
                  <AuditLog trades={trades} auditTrail={complianceData?.audit_trail || []} />
                </div>
              </Column>
            </Grid>
          </div>

          <div style={{ display: activeTab === 'analytics' ? 'block' : 'none', height: '100%' }}>
            <Grid fullWidth className="overflow-hidden h-full">
              <Column lg={16} md={8} sm={4} className="h-full overflow-y-auto">
                <div className="p-4">
                  <ComplianceCharts />
                </div>
              </Column>
            </Grid>
          </div>

          <div style={{ display: activeTab === 'history' ? 'block' : 'none', height: '100%' }}>
            <Grid fullWidth className="overflow-hidden h-full">
              <Column lg={16} md={8} sm={4} className="h-full overflow-y-auto">
                <div className="p-4">
                  <TradeHistory trades={trades} expanded />
                </div>
              </Column>
            </Grid>
          </div>
        </Content>

        <Toaster position="top-right" theme="light" />
      </Theme>
    </QueryClientProvider>
    );
  } catch (error) {
    console.error('❌ App render error:', error);
    return (
      <div style={{ padding: '40px', background: '#da1e28', color: 'white' }}>
        <h1>Application Error</h1>
        <p>{error.message}</p>
        <pre style={{ background: 'rgba(0,0,0,0.2)', padding: '10px', overflow: 'auto' }}>
          {error.stack}
        </pre>
      </div>
    );
  }
}

export default App;
