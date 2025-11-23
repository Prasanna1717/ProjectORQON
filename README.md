# ProjectORQON 🚀

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Vercel](https://img.shields.io/badge/Deployed%20on-Vercel-black)](https://frontend-35aeyyy00-prasanna1717s-projects.vercel.app)
[![IBM WatsonX](https://img.shields.io/badge/Powered%20by-IBM%20WatsonX-blue)](https://www.ibm.com/watsonx)

## 🎯 Overview

**ProjectORQON** is an enterprise-grade AI-powered compliance and trading platform that leverages IBM WatsonX AI to provide intelligent financial analysis, automated compliance monitoring, and real-time trade analytics. Built with a modern tech stack combining React, Python, and cutting-edge AI capabilities.

**🌐 Live Demo:** [https://frontend-35aeyyy00-prasanna1717s-projects.vercel.app](https://frontend-35aeyyy00-prasanna1717s-projects.vercel.app)

---

## ✨ Key Features

### 🤖 AI-Powered Intelligence
- **WatsonX Integration**: Advanced AI models for financial analysis and compliance
- **RAG System**: Retrieval-Augmented Generation for context-aware responses
- **Multi-Modal AI**: Support for text, voice, and document analysis

### 📊 Compliance & Analytics
- Real-time compliance monitoring and alerting
- Automated trade validation and risk assessment
- Executive dashboards with interactive charts
- Audit logging and reporting

### 💼 Trading & Portfolio Management
- Trade blotter with real-time updates
- Portfolio performance tracking
- Market data integration (Finnhub API)
- Email-based trade parsing and automation

### 🔗 Integrations
- **Google Workspace**: Gmail integration for trade notifications
- **IBM WatsonX AI**: Enterprise AI capabilities
- **Astra DB**: Vector database for RAG
- **ChromaDB**: Local vector storage for compliance memory
- **Model Context Protocol (MCP)**: Extensible tool system

---

## 🛠️ Tech Stack

### Frontend
- **React 18** with Vite
- **IBM Carbon Design System** - Enterprise UI components
- **Carbon Charts** - Data visualization
- **TailwindCSS** - Utility-first styling
- **Axios** - API communication
- **Zustand** - State management

### Backend
- **Python 3.13**
- **FastMCP** - Model Context Protocol server
- **IBM WatsonX AI SDK** - AI/ML capabilities
- **LangChain** - AI orchestration
- **ChromaDB** - Vector database
- **Google APIs** - Gmail, Docs, Sheets integration
- **Finnhub API** - Market data

### Infrastructure
- **Vercel** - Frontend hosting
- **Git** - Version control
- **Docker** - Containerization (optional)

---

## 📁 Project Structure

```
ProjectORQON/
├── orqon_core/                    # Main application directory
│   ├── frontend_pro/              # React frontend (Vite + Carbon)
│   │   ├── src/
│   │   │   ├── components/        # React components
│   │   │   ├── lib/               # Utilities
│   │   │   └── App.jsx            # Main app component
│   │   ├── package.json
│   │   └── vite.config.js
│   ├── tools/                     # MCP tools and integrations
│   │   ├── ibm_adk_tools/        # IBM Agent Development Kit tools
│   │   ├── google_workspace_tools.py
│   │   ├── finnhub_tools.py
│   │   └── rag_tools.py
│   ├── data/                      # Data storage
│   │   ├── trade_blotter.csv
│   │   └── compliance_memory/
│   ├── main.py                    # Main application entry
│   ├── mcp_server.py              # MCP server implementation
│   ├── watsonx_llm.py            # WatsonX integration
│   └── requirements.txt
├── IBM docs/                      # Documentation and configs
├── TECHNICAL_ARCHITECTURE.md      # System architecture
├── COMPLIANCE_PLATFORM_README.md  # Compliance details
└── README.md                      # This file
```

---

## 🚀 Quick Start

### Prerequisites
- **Node.js** 18+ and npm
- **Python** 3.13+
- **Git**
- IBM WatsonX API credentials
- Google Cloud credentials (for Gmail integration)
- Finnhub API key (optional, for market data)

### Frontend Setup

```bash
# Navigate to frontend directory
cd orqon_core/frontend_pro

# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

The frontend will be available at `http://localhost:3000`

### Backend Setup

```bash
# Navigate to orqon_core directory
cd orqon_core

# Create virtual environment
python -m venv orqon_env

# Activate virtual environment
# Windows:
.\orqon_env\Scripts\activate
# Linux/Mac:
source orqon_env/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file with your credentials
cat > .env << EOL
WATSONX_API_KEY=your_watsonx_api_key
WATSONX_PROJECT_ID=your_project_id
FINNHUB_API_KEY=your_finnhub_key
ASTRA_DB_APPLICATION_TOKEN=your_astra_token
ASTRA_DB_API_ENDPOINT=your_astra_endpoint
EOL

# Run the MCP server
python mcp_server.py

# Or run the main application
python main.py
```

---

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the `orqon_core/` directory:

```env
# IBM WatsonX
WATSONX_API_KEY=your_watsonx_api_key_here
WATSONX_PROJECT_ID=your_project_id_here
WATSONX_URL=https://us-south.ml.cloud.ibm.com

# Astra DB (Vector Database)
ASTRA_DB_APPLICATION_TOKEN=your_token_here
ASTRA_DB_API_ENDPOINT=your_endpoint_here

# Finnhub (Market Data)
FINNHUB_API_KEY=your_finnhub_key_here

# Google Workspace (Optional)
GOOGLE_CREDENTIALS_PATH=./data/google_credentials.json
```

### Google Workspace Setup

1. Create a Google Cloud project
2. Enable Gmail API and Google Workspace APIs
3. Create OAuth 2.0 credentials
4. Download credentials as `google_credentials.json`
5. Place in `orqon_core/data/` directory

---

## 📊 Features Overview

### Dashboard
- Executive summary with KPIs
- Real-time market overview
- Portfolio performance metrics
- Compliance status indicators

### Trade Management
- Trade blotter with filtering and search
- Email parsing for automated trade entry
- Trade validation and compliance checks
- Historical trade analysis

### Compliance Monitoring
- Real-time compliance rule engine
- Automated alert generation
- Audit trail and logging
- Compliance reports and analytics

### AI Chat Interface
- WatsonX-powered conversational AI
- Context-aware responses using RAG
- Multi-modal input (text, voice, documents)
- Integration with all platform features

---

## 🔒 Security

- API keys and credentials stored in `.env` (not committed to Git)
- OAuth 2.0 for Google Workspace integration
- Secure credential management with Python-dotenv
- Input validation and sanitization
- Audit logging for compliance

---

## 📈 Performance

- **Frontend**: Optimized Vite build with code splitting
- **Backend**: Async operations with FastMCP
- **Database**: Vector search with ChromaDB and Astra DB
- **Caching**: Smart caching for API responses
- **CDN**: Vercel Edge Network for global distribution

---

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **IBM WatsonX** - For providing enterprise AI capabilities
- **Carbon Design System** - For the beautiful UI components
- **Vercel** - For seamless deployment and hosting
- **FastMCP** - For the Model Context Protocol implementation

---

## 📧 Contact

**Project Maintainer**: [@Prasanna1717](https://github.com/Prasanna1717)

**Repository**: [https://github.com/Prasanna1717/ProjectORQON](https://github.com/Prasanna1717/ProjectORQON)

---

## 🗺️ Roadmap

- [ ] Add more compliance rules and regulations
- [ ] Enhanced ML models for trade prediction
- [ ] Mobile app support
- [ ] Advanced reporting features
- [ ] Multi-language support
- [ ] Real-time collaboration features

---

**Built with ❤️ using IBM WatsonX AI**
