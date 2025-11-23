/**
 * IBM watsonx Assistant Web Chat Widget with JWT Authentication
 * Professional financial dashboard integration
 */
import { useEffect, useState, useRef } from 'react';
import axios from 'axios';

const API_BASE = 'http://localhost:8000';

/**
 * ChatWidget Component
 * Embeds IBM watsonx Assistant Web Chat with JWT authentication
 */
export default function ChatWidget() {
  const [token, setToken] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const chatInitialized = useRef(false);

  useEffect(() => {
    // Step 1: Fetch JWT token from backend
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
    // Step 2: Load IBM Web Chat script and initialize
    if (token && !chatInitialized.current) {
      // Load the IBM watsonx Assistant Web Chat script
      const script = document.createElement('script');
      script.src = 'https://web-chat.global.assistant.watson.appdomain.cloud/versions/latest/WatsonAssistantChatEntry.js';
      script.async = true;

      script.onload = () => {
        // Initialize IBM Web Chat
        window.watsonAssistantChatOptions = {
          // IMPORTANT: Replace these placeholders with your actual IBM credentials
          integrationID: process.env.REACT_APP_IBM_INTEGRATION_ID || 'YOUR_INTEGRATION_ID',
          region: process.env.REACT_APP_IBM_REGION || 'us-south',
          serviceInstanceID: process.env.REACT_APP_IBM_SERVICE_INSTANCE_ID || 'YOUR_SERVICE_INSTANCE_ID',
          
          // JWT Identity Token for authentication
          identityToken: token,
          
          // Subscription ID (required for some features)
          subscriptionID: process.env.REACT_APP_IBM_SUBSCRIPTION_ID || 'YOUR_SUBSCRIPTION_ID',
          
          // Configuration options
          onLoad: function(instance) {
            console.log('IBM watsonx Assistant Web Chat loaded successfully');
            instance.render();
            setIsLoading(false);
            chatInitialized.current = true;
          },
          
          // Error handler
          onError: function(error) {
            console.error('IBM Web Chat error:', error);
            setError('Web Chat failed to load');
            setIsLoading(false);
          },
          
          // Styling configuration
          carbonTheme: 'g90', // Dark theme for professional look
          hideCloseButton: false,
          
          // Open on page load (optional)
          openChatByDefault: false,
          
          // Position
          showLauncher: true,
          launcherPosition: 'bottom right',
          
          // Size
          defaultView: 'narrow', // 'narrow' or 'wide'
          
          // Language
          locale: 'en-us',
          
          // Custom launcher button text
          messagePlaceholder: 'Type a trade command...',
          
          // Event handlers
          onBeforeRender: function(instance) {
            // Customize before rendering
            return true;
          },
          
          // Session history
          enableSessionPersistence: true,
          
          // Layout customization
          layout: {
            hasContentMaxWidth: true,
            showFrame: true,
          },
          
          // Theming for professional financial dashboard
          themeConfig: {
            corners: 'square',
            userBubbleColor: '#f97316', // Orange accent
            agentBubbleColor: '#2d2d2d', // Dark gray
            headerBackgroundColor: '#1a1a1a',
            headerTextColor: '#ffffff',
            launcherBackgroundColor: '#f97316',
          }
        };

        // Initialize the chat
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

      // Cleanup
      return () => {
        if (document.head.contains(script)) {
          document.head.removeChild(script);
        }
      };
    }
  }, [token]);

  // Render loading/error states
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

  // The IBM Web Chat will render itself via the script
  return (
    <div id="watson-assistant-chat-container">
      {/* IBM Web Chat renders here automatically */}
    </div>
  );
}

/**
 * SETUP INSTRUCTIONS:
 * 
 * 1. Create IBM watsonx Assistant instance in IBM Cloud
 * 2. Get your credentials:
 *    - Integration ID
 *    - Region (e.g., us-south, us-east, eu-gb)
 *    - Service Instance ID
 *    - Subscription ID (optional)
 * 
 * 3. Set environment variables in .env:
 *    REACT_APP_IBM_INTEGRATION_ID=your_integration_id
 *    REACT_APP_IBM_REGION=us-south
 *    REACT_APP_IBM_SERVICE_INSTANCE_ID=your_service_instance_id
 *    REACT_APP_IBM_SUBSCRIPTION_ID=your_subscription_id
 * 
 * 4. Configure your assistant in IBM Cloud:
 *    - Add skills (trade parsing, etc.)
 *    - Configure dialog flows
 *    - Set up webhooks to your FastAPI backend
 * 
 * 5. Backend webhook configuration:
 *    - Point IBM Assistant webhooks to http://your-domain:8000/skills/parse_trade
 *    - Ensure JWT authentication is configured
 * 
 * ALTERNATIVE: Direct Backend Integration (No IBM Cloud)
 * If you prefer to use only your backend without IBM Cloud:
 * - Remove this component
 * - Use the custom ChatInterface component instead
 * - Directly call POST /chat endpoint for trade parsing
 */
