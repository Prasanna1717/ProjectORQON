# ORQON SEC Compliance Analysis Platform

## Overview
Enterprise-grade SEC compliance analysis platform for trade reconstruction and regulatory compliance. Built with IBM Carbon Design System and powered by AI-driven compliance checks.

## 🎯 Key Features

### 1. **Slippage Detection (Best Execution)**
- Monitors price deviation between intended and executed prices
- Flags violations: WARNING (>2%), CRITICAL (>5%)
- Supports LIMIT and MARKET order analysis
- Real-time slippage percentage calculation

### 2. **Suitability Checks (KYC Compliance)**
- Validates trades against client risk profiles
- Detects high-risk assets (crypto, volatile stocks, large quantities)
- Flags unsuitable trades for conservative/elderly clients
- Profile categories: Conservative, Moderate, Aggressive

### 3. **Solicitation Classification**
- Analyzes broker-client communication transcripts
- Determines if trade was broker-initiated (Solicited) or client-initiated (Unsolicited)
- Keyword-based analysis with confidence scoring
- Churning detection for high solicited ratios

### 4. **Executive Summary Dashboard**
- Real-time compliance score (0-100)
- Color-coded violation alerts
- Critical violation highlights
- Action buttons: Generate FINRA Report, Email Supervisor

### 5. **Audit Log**
- Comprehensive trade reconstruction evidence
- Timestamped audit trail
- Risk score visualization
- Export capabilities

### 6. **Compliance Charts**
- Trade solicitation distribution
- Risk score breakdown
- Violation analytics
- Interactive visualizations

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- npm or yarn

### Backend Setup
```bash
cd orqon_core
pip install -r requirements.txt
python main.py
```
Backend runs on: `http://localhost:8000`

### Frontend Setup
```bash
cd frontend_pro
npm install
npm run dev
```
Frontend runs on: `http://localhost:3001`

## 📊 Usage

### 1. Navigate to Compliance Tab
Open `http://localhost:3001` and click **"Compliance Analysis"**

### 2. Input Trade Data
- **Transcript**: Paste broker-client conversation
- **Audio Upload**: (Optional) Upload MP3/WAV/M4A files
- **Trade Ticket**: Enter execution details
  - Ticker (e.g., AAPL)
  - Quantity
  - Intended Price (for LIMIT orders)
  - Executed Price
  - Order Type (LIMIT/MARKET)
- **Client Profile**:
  - Risk Tolerance (Conservative/Moderate/Aggressive)
  - Age Category (Young/Middle-Age/Elderly)
  - Net Worth (Low/Medium/High)

### 3. Run Analysis
Click **"Analyze Compliance"** or use **"Load Sample Data"** for demo

### 4. Review Results
- **Executive Summary**: Compliance score and violations
- **Compliance Charts**: Visual analytics
- **Audit Log**: Detailed evidence trail

## 🔧 API Endpoints

### Authentication
```http
POST /auth/token
Content-Type: application/json

{
  "user_email": "compliance@orqon.com",
  "user_id": "compliance_001"
}
```

### Compliance Analysis
```http
POST /analyze_compliance
Authorization: Bearer <token>
Content-Type: application/json

{
  "transcript": "Client: I'd like to buy 500 AAPL...",
  "execution_log": {
    "ticker": "AAPL",
    "quantity": 500,
    "intended_price": 150.00,
    "executed_price": 152.50,
    "order_type": "LIMIT",
    "timestamp": "2024-11-22T10:30:00Z"
  },
  "client_profile": {
    "risk_tolerance": "Moderate",
    "age_category": "Middle-Age",
    "net_worth": "High"
  },
  "trader_id": "Trader_555"
}
```

### Response Format
```json
{
  "compliance_score": 85.0,
  "violations": [
    {
      "violation_type": "SLIPPAGE_WARNING",
      "severity": "WARNING",
      "description": "Price slippage of 1.67% detected",
      "evidence": "Intended: $150.00, Executed: $152.50",
      "timestamp": "2024-11-22T10:30:00Z",
      "risk_score": 45.0
    }
  ],
  "trade_classification": "Unsolicited",
  "classification_reason": "Client-initiated trade",
  "audit_trail": [
    "2024-11-22T10:30:00Z - Client requested BUY 500 AAPL",
    "2024-11-22T10:30:05Z - LIMIT order placed at $150.00"
  ],
  "recommendations": [
    "Review execution quality with broker"
  ]
}
```

## 🧪 Testing

### Run Compliance Tests
```bash
cd orqon_core
python test_compliance.py
```

### Test Scenarios
1. **Slippage Detection**: AAPL limit order with 1.67% slippage
2. **Suitability Violation**: Elderly conservative client buying volatile stock
3. **Solicitation**: Broker-recommended trade classification

## 📁 Project Structure

```
orqon_core/
├── main.py                 # FastAPI backend with compliance logic
├── test_compliance.py      # Automated test suite
└── requirements.txt        # Python dependencies

frontend_pro/
├── src/
│   ├── App.jsx            # Main application
│   └── components/
│       ├── ComplianceInputPanel.jsx    # Left panel input form
│       ├── ExecutiveSummary.jsx        # Top right summary
│       ├── ComplianceCharts.jsx        # Analytics visualizations
│       └── AuditLog.jsx                # Bottom right audit table
├── package.json
└── vite.config.js
```

## 🎨 Technology Stack

### Backend
- **FastAPI** 0.115.0+ - High-performance API framework
- **Pydantic** - Data validation
- **JWT** - Authentication
- **Uvicorn** - ASGI server

### Frontend
- **React** 18.3.1 - UI framework
- **IBM Carbon Design System** - Enterprise UI components
- **Vite** - Build tool
- **Axios** - HTTP client
- **Sonner** - Toast notifications

## 🔒 Security

### Authentication
- JWT token-based authentication
- 24-hour token expiration
- Secure password hashing (bcrypt)
- CORS enabled for development

### Best Practices
- Input validation on all endpoints
- SQL injection prevention
- XSS protection
- Rate limiting (recommended for production)

## 📈 Compliance Scoring

### Score Calculation
```
Base Score: 100
- CRITICAL violation: -30 points
- WARNING violation: -15 points
- INFO violation: -5 points

Final Score = max(0, Base Score - Σ(violations))
```

### Score Interpretation
- **90-100**: ✅ Excellent - No major issues
- **70-89**: ⚠️ Good - Minor violations present
- **0-69**: ❌ Poor - Critical violations detected

## 🛠️ Development

### Error Handling
- Comprehensive try-catch blocks
- User-friendly error messages
- Detailed server logs
- Network error detection

### File Upload
- Supports: MP3, WAV, M4A
- Max size: 50MB
- Type validation
- Size validation

### Future Enhancements
- [ ] Speech-to-text integration (IBM Watson / OpenAI Whisper)
- [ ] FINRA report PDF generation
- [ ] Email notification system
- [ ] Multi-trade batch analysis
- [ ] Historical compliance trends
- [ ] Machine learning risk models

## 📞 Support

### Common Issues

**Q: Blank page on frontend**
- Ensure backend is running on port 8000
- Check browser console for errors
- Verify Carbon Charts CSS is loaded

**Q: Authentication failed**
- Backend server must be running
- Check token expiration (24 hours)
- Verify credentials in App.jsx

**Q: Analysis fails**
- Fill all required fields (Transcript, Ticker, Executed Price)
- Validate numeric inputs
- Check network connectivity

## 📝 License

Proprietary - ORQON Trade Intelligence Platform

## 👥 Contributors

Built for Goldman Sachs / J.P. Morgan style trade reconstruction compliance.

---

**Version**: 2.0.0  
**Last Updated**: November 22, 2024  
**Status**: Production Ready ✅
