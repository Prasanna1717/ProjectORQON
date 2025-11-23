import { useEffect, useState, useRef } from 'react';
import axios from 'axios';
const API_BASE = 'http:
export default function ChatWidget() {
  const [token, setToken] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const chatInitialized = useRef(false);
  useEffect(() => {
    const fetchToken = async () => {
      try {
        setIsLoading(true);
        const response = await axios.post(`${API_BASE}/auth/token`, {
          user_email: 'trader@orqon.com',
          user_id: 'trader_001',
          metadata: {
            role: 'trader',
            department: 'trading_desk'
          }
        });
        const { access_token } = response.data;
        setToken(access_token);
        setError(null);
      } catch (err) {
        console.error('Token fetch error:', err);
        setError('Failed to authenticate with backend');
        setIsLoading(false);
      }
    };
    fetchToken();
  }, []);
  useEffect(() => {
    if (token && !chatInitialized.current) {
      const script = document.createElement('script');
      script.src = 'https:
      script.async = true;
      script.onload = () => {
        window.watsonAssistantChatOptions = {
          integrationID: process.env.REACT_APP_IBM_INTEGRATION_ID || 'YOUR_INTEGRATION_ID',
          region: process.env.REACT_APP_IBM_REGION || 'us-south',
          serviceInstanceID: process.env.REACT_APP_IBM_SERVICE_INSTANCE_ID || 'YOUR_SERVICE_INSTANCE_ID',
          identityToken: token,
          subscriptionID: process.env.REACT_APP_IBM_SUBSCRIPTION_ID || 'YOUR_SUBSCRIPTION_ID',
          onLoad: function(instance) {
            console.log('IBM watsonx Assistant Web Chat loaded successfully');
            instance.render();
            setIsLoading(false);
            chatInitialized.current = true;
          },
          onError: function(error) {
            console.error('IBM Web Chat error:', error);
            setError('Web Chat failed to load');
            setIsLoading(false);
          },
          carbonTheme: 'g90', 
          hideCloseButton: false,
          openChatByDefault: false,
          showLauncher: true,
          launcherPosition: 'bottom right',
          defaultView: 'narrow', 
          locale: 'en-us',
          messagePlaceholder: 'Type a trade command...',
          onBeforeRender: function(instance) {
            return true;
          },
          enableSessionPersistence: true,
          layout: {
            hasContentMaxWidth: true,
            showFrame: true,
          },
          themeConfig: {
            corners: 'square',
            userBubbleColor: '#f97316', 
            agentBubbleColor: '#2d2d2d', 
            headerBackgroundColor: '#1a1a1a',
            headerTextColor: '#ffffff',
            launcherBackgroundColor: '#f97316',
          }
        };
        if (window.loadWatsonAssistantChat) {
          window.loadWatsonAssistantChat(window.watsonAssistantChatOptions);
        }
      };
      script.onerror = () => {
        console.error('Failed to load IBM Web Chat script');
        setError('Failed to load chat widget');
        setIsLoading(false);
      };
      document.head.appendChild(script);
      return () => {
        if (document.head.contains(script)) {
          document.head.removeChild(script);
        }
      };
    }
  }, [token]);
  if (isLoading) {
    return (
      <div className="fixed bottom-4 right-4 bg-gray-800 text-white p-4 rounded-lg shadow-lg">
        <div className="flex items-center space-x-2">
          <div className="animate-spin h-5 w-5 border-2 border-orange-500 border-t-transparent rounded-full"></div>
          <span>Loading chat...</span>
        </div>
      </div>
    );
  }
  if (error) {
    return (
      <div className="fixed bottom-4 right-4 bg-red-900 text-white p-4 rounded-lg shadow-lg max-w-sm">
        <div className="flex items-center space-x-2">
          <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
          </svg>
          <span>{error}</span>
        </div>
      </div>
    );
  }
  return (
    <div id="watson-assistant-chat-container">
      {}
    </div>
  );
}
