import { useState, useRef, useEffect } from 'react'
import axios from 'axios'
import './TradeParser.css'

const API_BASE = 'http://localhost:8003'

function TradeParser() {
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)
  const [conversationId, setConversationId] = useState(null)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!input.trim()) return

    // Add user message
    const userMessage = {
      type: 'user',
      text: input,
      timestamp: new Date().toLocaleTimeString()
    }
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      // Call backend chat API
      const response = await axios.post(`${API_BASE}/chat`, {
        message: input,
        conversation_id: conversationId
      })

      const data = response.data

      // Add assistant response
      const assistantMessage = {
        type: 'assistant',
        text: data.response,
        parsedTrade: data.parsed_trade,
        timestamp: new Date().toLocaleTimeString()
      }

      setMessages(prev => [...prev, assistantMessage])
      setConversationId(data.conversation_id)

    } catch (error) {
      console.error('Error:', error)
      const errorMessage = {
        type: 'error',
        text: 'Failed to process trade. Please try again.',
        timestamp: new Date().toLocaleTimeString()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  const quickCommands = [
    "Buy 100 shares of Apple at market",
    "Sell 50 Tesla at $250 limit",
    "Buy 200 Microsoft at market for John Smith",
    "Sell 75 NVDA at $500 limit"
  ]

  return (
    <div className="trade-parser-container">
      <div className="chat-window">
        <div className="messages-container">
          {messages.length === 0 && (
            <div className="welcome-message">
              <h2>👋 Welcome to Orqon Trade Parser</h2>
              <p>Try commands like:</p>
              <div className="quick-commands">
                {quickCommands.map((cmd, idx) => (
                  <button
                    key={idx}
                    className="quick-command-btn"
                    onClick={() => setInput(cmd)}
                  >
                    {cmd}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg, idx) => (
            <div key={idx} className={`message ${msg.type}`}>
              <div className="message-header">
                <span className="message-sender">
                  {msg.type === 'user' ? '👤 You' : '🤖 Assistant'}
                </span>
                <span className="message-time">{msg.timestamp}</span>
              </div>
              <div className="message-content">
                <div className="message-text">{msg.text}</div>
                {msg.parsedTrade && (
                  <div className="parsed-trade-card">
                    <h4>📊 Parsed Trade Data</h4>
                    <div className="trade-details">
                      <div className="trade-field">
                        <span className="field-label">Action:</span>
                        <span className={`field-value ${msg.parsedTrade.action.toLowerCase()}`}>
                          {msg.parsedTrade.action}
                        </span>
                      </div>
                      <div className="trade-field">
                        <span className="field-label">Quantity:</span>
                        <span className="field-value">{msg.parsedTrade.quantity} shares</span>
                      </div>
                      <div className="trade-field">
                        <span className="field-label">Ticker:</span>
                        <span className="field-value ticker">{msg.parsedTrade.ticker}</span>
                      </div>
                      <div className="trade-field">
                        <span className="field-label">Order Type:</span>
                        <span className="field-value">{msg.parsedTrade.order_type}</span>
                      </div>
                      {msg.parsedTrade.price && (
                        <div className="trade-field">
                          <span className="field-label">Price:</span>
                          <span className="field-value">${msg.parsedTrade.price}</span>
                        </div>
                      )}
                      {msg.parsedTrade.client_name && (
                        <div className="trade-field">
                          <span className="field-label">Client:</span>
                          <span className="field-value">{msg.parsedTrade.client_name}</span>
                        </div>
                      )}
                      <div className="trade-field">
                        <span className="field-label">Confidence:</span>
                        <span className="field-value">
                          {(msg.parsedTrade.confidence * 100).toFixed(0)}%
                        </span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="message assistant loading">
              <div className="message-header">
                <span className="message-sender">🤖 Assistant</span>
              </div>
              <div className="message-content">
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        <form className="input-form" onSubmit={handleSubmit}>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type a trade command (e.g., Buy 50 Apple at market)..."
            className="trade-input"
            disabled={loading}
          />
          <button 
            type="submit" 
            className="send-button"
            disabled={loading || !input.trim()}
          >
            {loading ? '⏳' : '📤'} Send
          </button>
        </form>
      </div>
    </div>
  )
}

export default TradeParser
