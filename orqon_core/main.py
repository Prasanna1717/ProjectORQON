"""
Main FastAPI application with IBM watsonx Orchestrate ADK integration
Includes JWT authentication for IBM Web Chat
"""
import os
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
import uvicorn
from dotenv import load_dotenv

# Import skills
from skills import (
    TradeParseInput,
    TradeParseOutput,
    parse_trade_skill,
    TradeRecord
)

# Load environment variables
load_dotenv()

# ============================================================================
# CONFIGURATION
# ============================================================================

JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# ============================================================================
# PYDANTIC MODELS FOR AUTH
# ============================================================================

class TokenRequest(BaseModel):
    """Request model for JWT token generation"""
    user_email: Optional[EmailStr] = "user@example.com"
    user_id: Optional[str] = "default_user"
    metadata: Optional[Dict[str, Any]] = {}


class TokenResponse(BaseModel):
    """Response model for JWT token"""
    access_token: str
    token_type: str = "Bearer"
    expires_in: int  # seconds
    user_email: str
    issued_at: datetime


# ============================================================================
# JWT UTILITIES
# ============================================================================

def create_jwt_token(user_email: str, user_id: str, metadata: Dict[str, Any] = None) -> str:
    """
    Create a JWT token for IBM Web Chat authentication
    
    Args:
        user_email: User's email address
        user_id: Unique user identifier
        metadata: Additional metadata to include in token
        
    Returns:
        Encoded JWT token string
    """
    now = datetime.utcnow()
    expiration = now + timedelta(hours=JWT_EXPIRATION_HOURS)
    
    payload = {
        "sub": user_id,  # Subject (user ID)
        "email": user_email,
        "iat": now,  # Issued at
        "exp": expiration,  # Expiration
        "metadata": metadata or {}
    }
    
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token


def verify_jwt_token(token: str) -> Dict[str, Any]:
    """
    Verify and decode a JWT token
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded token payload
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ============================================================================
# SECURITY DEPENDENCIES
# ============================================================================

security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    FastAPI dependency to validate JWT token and extract user info
    
    Args:
        credentials: HTTP Bearer token credentials
        
    Returns:
        User information from token payload
    """
    token = credentials.credentials
    payload = verify_jwt_token(token)
    return payload


# ============================================================================
# FASTAPI APPLICATION
# ============================================================================

app = FastAPI(
    title="Orqon Trade Parser - IBM watsonx Orchestrate Agent",
    description="Production-ready headless agent with JWT authentication and trade parsing skills",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"  # IBM discovers skills via this endpoint
)

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:5173",
        "http://localhost:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@app.post("/auth/token", response_model=TokenResponse, tags=["Authentication"])
async def generate_token(request: TokenRequest):
    """
    Generate a JWT token for IBM Web Chat authentication
    
    This endpoint is called by the React frontend to obtain a token
    that is then used as the identityToken in IBM watsonx Assistant Web Chat.
    
    Args:
        request: TokenRequest with user information
        
    Returns:
        TokenResponse with JWT token and metadata
    """
    token = create_jwt_token(
        user_email=request.user_email,
        user_id=request.user_id,
        metadata=request.metadata
    )
    
    return TokenResponse(
        access_token=token,
        token_type="Bearer",
        expires_in=JWT_EXPIRATION_HOURS * 3600,  # Convert to seconds
        user_email=request.user_email,
        issued_at=datetime.utcnow()
    )


@app.get("/auth/verify", tags=["Authentication"])
async def verify_token(user: Dict[str, Any] = Depends(get_current_user)):
    """
    Verify a JWT token and return user information
    
    This is a protected endpoint that requires a valid JWT token.
    Used to validate tokens and check user session status.
    
    Args:
        user: Injected user data from JWT token
        
    Returns:
        User information from token
    """
    return {
        "valid": True,
        "user_id": user.get("sub"),
        "email": user.get("email"),
        "metadata": user.get("metadata", {}),
        "expires_at": datetime.fromtimestamp(user.get("exp"))
    }


# ============================================================================
# SKILL ENDPOINTS (IBM ADK Pattern)
# ============================================================================

@app.post("/skills/parse_trade", response_model=TradeParseOutput, tags=["Skills"])
async def parse_trade_endpoint(
    input_data: TradeParseInput,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Trade Parser Skill - Parse natural language trade commands
    
    This endpoint follows the IBM watsonx Orchestrate skill pattern.
    It extracts structured trade data from natural language text.
    
    Pattern Matching:
    - "Buy 100 shares of Apple at market"
    - "Sell 50 TSLA at $250 limit"
    - "Purchase 200 Microsoft for John Smith"
    
    Args:
        input_data: TradeParseInput with transcript text
        user: Authenticated user from JWT token
        
    Returns:
        TradeParseOutput with parsed trade record
    """
    # Add authenticated user email to input
    if not input_data.user_email:
        input_data.user_email = user.get("email")
    
    # Call the skill function
    result = parse_trade_skill(input_data)
    
    return result


# ============================================================================
# CHAT ENDPOINT (For React UI)
# ============================================================================

class ChatMessage(BaseModel):
    """Chat message from frontend"""
    message: str
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Chat response to frontend"""
    response: str
    parsed_trade: Optional[TradeRecord] = None
    conversation_id: str
    timestamp: datetime


# ============================================================================
# COMPLIANCE ANALYSIS MODELS
# ============================================================================

class ComplianceViolation(BaseModel):
    """Individual compliance violation"""
    violation_type: str
    severity: str  # "CRITICAL", "WARNING", "INFO"
    description: str
    evidence: str
    timestamp: str
    risk_score: float


class ClientProfile(BaseModel):
    """Client suitability profile"""
    risk_tolerance: str  # "Conservative", "Moderate", "Aggressive"
    age_category: str  # "Young", "Middle-Age", "Elderly/Retired"
    net_worth: str  # "Low", "Medium", "High"


class ExecutionLog(BaseModel):
    """Trade execution log entry"""
    ticker: str
    quantity: int
    intended_price: Optional[float] = None
    executed_price: float
    order_type: str  # "MARKET", "LIMIT"
    timestamp: str


class ComplianceAnalysisInput(BaseModel):
    """Input for compliance analysis"""
    transcript: str
    execution_log: ExecutionLog
    client_profile: Optional[ClientProfile] = None
    audio_file: Optional[str] = None  # Base64 encoded audio or file path
    trader_id: Optional[str] = None


class ComplianceAnalysisOutput(BaseModel):
    """Output from compliance analysis"""
    compliance_score: float  # 0-100
    violations: list[ComplianceViolation]
    summary: str
    slippage_percent: Optional[float] = None
    trade_classification: str  # "Solicited" or "Unsolicited"
    recommendations: list[str]
    audit_trail: list[Dict[str, Any]]


# ============================================================================
# COMPLIANCE ANALYSIS FUNCTIONS
# ============================================================================

def detect_slippage(intended_price: Optional[float], executed_price: float, order_type: str) -> tuple[bool, float, str]:
    """
    Feature A: Slippage Detector (Best Execution)
    
    Detects if execution price deviated from client's intended price
    """
    if order_type == "MARKET":
        # Market orders have no intended price - no violation
        return False, 0.0, "Market order - no price guarantee"
    
    if intended_price is None:
        return False, 0.0, "No intended price specified"
    
    slippage_percent = ((executed_price - intended_price) / intended_price) * 100
    
    if abs(slippage_percent) > 2.0:  # More than 2% slippage
        severity = "CRITICAL" if abs(slippage_percent) > 5.0 else "WARNING"
        return True, slippage_percent, f"{severity}: {abs(slippage_percent):.2f}% negative slippage detected"
    
    return False, slippage_percent, "Acceptable execution"


def check_suitability(transcript: str, execution_log: ExecutionLog, client_profile: Optional[ClientProfile]) -> tuple[bool, str]:
    """
    Feature B: Suitability Check (KYC - Know Your Customer)
    
    Checks if trade is suitable for client's risk profile
    """
    if not client_profile:
        # Try to infer from transcript
        transcript_lower = transcript.lower()
        if any(word in transcript_lower for word in ["elderly", "retired", "pension", "fixed income"]):
            client_profile = ClientProfile(
                risk_tolerance="Conservative",
                age_category="Elderly/Retired",
                net_worth="Medium"
            )
        else:
            return False, "No client profile available for suitability check"
    
    # High-risk asset keywords
    high_risk_keywords = ["crypto", "bitcoin", "meme", "penny stock", "volatile", "speculative"]
    high_risk_tickers = ["GME", "AMC", "DOGE", "BTC"]
    
    is_high_risk = (
        any(keyword in transcript.lower() for keyword in high_risk_keywords) or
        execution_log.ticker in high_risk_tickers or
        execution_log.quantity > 5000  # Large position
    )
    
    if is_high_risk and client_profile.risk_tolerance == "Conservative":
        return True, f"VIOLATION: High-risk asset not suitable for conservative profile. Client is {client_profile.age_category} with {client_profile.risk_tolerance} risk tolerance."
    
    return False, "Trade suitable for client profile"


def classify_solicitation(transcript: str) -> tuple[str, str]:
    """
    Feature C: Solicited vs. Unsolicited Classification
    
    Determines if trade was initiated by client or broker
    """
    transcript_lower = transcript.lower()
    
    # Broker-initiated keywords
    broker_keywords = ["recommend", "suggest", "opportunity", "should buy", "should sell", "call you about"]
    
    # Client-initiated keywords
    client_keywords = ["i want", "i'd like", "please buy", "please sell", "can you", "i need"]
    
    broker_score = sum(1 for kw in broker_keywords if kw in transcript_lower)
    client_score = sum(1 for kw in client_keywords if kw in transcript_lower)
    
    if broker_score > client_score:
        return "Solicited", f"Broker-initiated: Detected {broker_score} broker prompts"
    else:
        return "Unsolicited", f"Client-initiated: Detected {client_score} client requests"


@app.post("/analyze_compliance", response_model=ComplianceAnalysisOutput, tags=["Compliance"])
async def analyze_compliance(
    input_data: ComplianceAnalysisInput,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Compliance Analysis Endpoint - SEC Trade Reconstruction
    
    Analyzes broker-client communications against actual trade execution
    to detect compliance violations:
    
    1. Slippage Detection (Best Execution)
    2. Suitability Checks (KYC)
    3. Solicitation Classification
    
    Used for SEC investigations and internal audits.
    """
    violations = []
    audit_trail = []
    recommendations = []
    
    # Feature A: Slippage Detection
    has_slippage, slippage_percent, slippage_msg = detect_slippage(
        input_data.execution_log.intended_price,
        input_data.execution_log.executed_price,
        input_data.execution_log.order_type
    )
    
    if has_slippage:
        violations.append(ComplianceViolation(
            violation_type="BEST_EXECUTION_VIOLATION",
            severity="CRITICAL" if abs(slippage_percent) > 5.0 else "WARNING",
            description=f"Negative slippage detected: {slippage_percent:.2f}%",
            evidence=f"Client requested {input_data.execution_log.order_type} at ${input_data.execution_log.intended_price}, executed at ${input_data.execution_log.executed_price}",
            timestamp=input_data.execution_log.timestamp,
            risk_score=min(abs(slippage_percent) * 10, 100)
        ))
        recommendations.append("Review execution quality and best execution policies")
    
    # Feature B: Suitability Check
    has_suitability_issue, suitability_msg = check_suitability(
        input_data.transcript,
        input_data.execution_log,
        input_data.client_profile
    )
    
    if has_suitability_issue:
        violations.append(ComplianceViolation(
            violation_type="SUITABILITY_VIOLATION",
            severity="CRITICAL",
            description=suitability_msg,
            evidence=f"Trade: {input_data.execution_log.quantity} shares of {input_data.execution_log.ticker}",
            timestamp=input_data.execution_log.timestamp,
            risk_score=95.0
        ))
        recommendations.append("Freeze account pending suitability review")
        recommendations.append("Generate FINRA report")
    
    # Feature C: Solicitation Classification
    classification, classification_reason = classify_solicitation(input_data.transcript)
    
    # Build audit trail
    audit_trail.append({
        "timestamp": "00:00",
        "event": "Call Started",
        "evidence": "Audio recording begins"
    })
    
    # Parse transcript for key moments
    if "limit" in input_data.transcript.lower():
        audit_trail.append({
            "timestamp": "00:45",
            "event": "Client mentions Limit order",
            "evidence": f"Client requested limit at ${input_data.execution_log.intended_price}"
        })
    
    audit_trail.append({
        "timestamp": "01:30",
        "event": "Trade Executed",
        "evidence": f"Execution at ${input_data.execution_log.executed_price}"
    })
    
    # Calculate compliance score - starts at 100%, reduces by 0.5% per violation
    base_score = 100.0
    for violation in violations:
        base_score -= 0.5
    
    compliance_score = max(base_score, 0.0)
    
    # Generate summary
    trader_ref = input_data.trader_id or "Unknown Trader"
    summary = f"Analysis of {trader_ref}. "
    
    if violations:
        summary += f"Detected {len(violations)} compliance issue(s): "
        summary += ", ".join([f"{v.violation_type}" for v in violations])
        summary += ". "
    else:
        summary += "No compliance violations detected. "
    
    summary += f"Trade classified as: {classification}. "
    
    if recommendations:
        summary += f"Recommendations: {', '.join(recommendations)}"
    
    return ComplianceAnalysisOutput(
        compliance_score=compliance_score,
        violations=violations,
        summary=summary,
        slippage_percent=slippage_percent if has_slippage else None,
        trade_classification=classification,
        recommendations=recommendations,
        audit_trail=audit_trail
    )


@app.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat_endpoint(
    chat: ChatMessage,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Chat endpoint for React frontend
    
    Processes natural language messages and returns parsed trade data
    with a friendly response message.
    
    Args:
        chat: ChatMessage with user input
        user: Authenticated user from JWT token
        
    Returns:
        ChatResponse with trade data and friendly message
    """
    # Parse the trade
    parse_input = TradeParseInput(
        transcript_text=chat.message,
        user_email=user.get("email")
    )
    
    result = parse_trade_skill(parse_input)
    
    # Generate conversation ID if not provided
    conversation_id = chat.conversation_id or f"conv_{datetime.utcnow().timestamp()}"
    
    # Create response message
    if result.success and result.trade_record:
        trade = result.trade_record
        response_text = (
            f"Trade parsed successfully: {trade.action} {trade.quantity} shares of "
            f"{trade.asset} at {trade.order_type.lower()} "
            f"{'price $' + str(trade.price) if trade.price else ''}"
        )
        if trade.client_name:
            response_text += f" for {trade.client_name}"
    else:
        response_text = result.error_message or "Unable to parse trade command"
    
    return ChatResponse(
        response=response_text,
        parsed_trade=result.trade_record if result.success else None,
        conversation_id=conversation_id,
        timestamp=datetime.utcnow()
    )


# ============================================================================
# UTILITY ENDPOINTS
# ============================================================================

@app.get("/", tags=["Utility"])
async def root():
    """Root endpoint with API information"""
    return {
        "name": "Orqon Trade Parser Agent",
        "version": "2.0.0",
        "framework": "IBM watsonx Orchestrate",
        "model": "granite-3-8b-instruct",
        "skills": ["parse_trade"],
        "authentication": "JWT Bearer Token",
        "endpoints": {
            "auth_token": "/auth/token",
            "auth_verify": "/auth/verify",
            "trade_parser": "/skills/parse_trade",
            "chat": "/chat",
            "openapi": "/openapi.json",
            "docs": "/docs"
        }
    }


@app.get("/health", tags=["Utility"])
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "service": "orqon-trade-parser"
    }


# ============================================================================
# STARTUP & MAIN
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Execute on application startup"""
    print("=" * 80)
    print("ORQON TRADE PARSER - IBM WATSONX ORCHESTRATE AGENT")
    print("=" * 80)
    print(f"\nJWT Authentication: Enabled")
    print(f"JWT Secret: {'***' + JWT_SECRET[-4:] if len(JWT_SECRET) > 4 else '***'}")
    print(f"Token Expiration: {JWT_EXPIRATION_HOURS} hours")
    print(f"\nSkills Available:")
    print(f"  - Trade Parser (POST /skills/parse_trade)")
    print(f"\nEndpoints:")
    print(f"  - Token Generation: POST /auth/token")
    print(f"  - Token Verification: GET /auth/verify")
    print(f"  - Chat Interface: POST /chat")
    print(f"  - API Documentation: /docs")
    print(f"  - OpenAPI Spec: /openapi.json (IBM discovery)")
    print("=" * 80)


if __name__ == "__main__":
    # Production configuration
    PORT = int(os.getenv("PORT", 8000))
    HOST = os.getenv("HOST", "0.0.0.0")
    
    print(f"\nStarting server on {HOST}:{PORT}")
    print(f"Access at: http://localhost:{PORT}")
    print(f"API Docs at: http://localhost:{PORT}/docs")
    print("\nPress CTRL+C to stop\n")
    
    uvicorn.run(
        "main:app",
        host=HOST,
        port=PORT,
        reload=True,  # Development mode
        log_level="info"
    )
