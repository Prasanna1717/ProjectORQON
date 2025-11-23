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

from skills import (
    TradeParseInput,
    TradeParseOutput,
    parse_trade_skill,
    TradeRecord
)

load_dotenv()


JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24


class TokenRequest(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    user_email: str
    issued_at: datetime



def create_jwt_token(user_email: str, user_id: str, metadata: Dict[str, Any] = None) -> str:
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



security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    token = credentials.credentials
    payload = verify_jwt_token(token)
    return payload



app = FastAPI(
    title="Orqon Trade Parser - IBM watsonx Orchestrate Agent",
    description="Production-ready headless agent with JWT authentication and trade parsing skills",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"  # IBM discovers skills via this endpoint
)

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



@app.post("/auth/token", response_model=TokenResponse, tags=["Authentication"])
async def generate_token(request: TokenRequest):
    token = create_jwt_token(
        user_email=request.user_email,
        user_id=request.user_id,
        metadata=request.metadata
    )
    
    return TokenResponse(
        access_token=token,
        token_type="Bearer",
        expires_in=JWT_EXPIRATION_HOURS * 3600,
        user_email=request.user_email,
        issued_at=datetime.utcnow()
    )


@app.get("/auth/verify", tags=["Authentication"])
async def verify_token(user: Dict[str, Any] = Depends(get_current_user)):
    return {
        "valid": True,
        "user_id": user.get("sub"),
        "email": user.get("email"),
        "metadata": user.get("metadata", {}),
        "expires_at": datetime.fromtimestamp(user.get("exp"))
    }



@app.post("/skills/parse_trade", response_model=TradeParseOutput, tags=["Skills"])
async def parse_trade_endpoint(
    input_data: TradeParseInput,
    user: Dict[str, Any] = Depends(get_current_user)
):
    if not input_data.user_email:
        input_data.user_email = user.get("email")
    
    result = parse_trade_skill(input_data)
    
    return result



class ChatMessage(BaseModel):
    response: str
    parsed_trade: Optional[TradeRecord] = None
    conversation_id: str
    timestamp: datetime



class ComplianceViolation(BaseModel):
    risk_tolerance: str  # "Conservative", "Moderate", "Aggressive"
    age_category: str  # "Young", "Middle-Age", "Elderly/Retired"
    net_worth: str  # "Low", "Medium", "High"


class ExecutionLog(BaseModel):
    transcript: str
    execution_log: ExecutionLog
    client_profile: Optional[ClientProfile] = None
    audio_file: Optional[str] = None
    trader_id: Optional[str] = None


class ComplianceAnalysisOutput(BaseModel):
    Feature A: Slippage Detector (Best Execution)
    
    Detects if execution price deviated from client's intended price
    Feature B: Suitability Check (KYC - Know Your Customer)
    
    Checks if trade is suitable for client's risk profile
    Feature C: Solicited vs. Unsolicited Classification
    
    Determines if trade was initiated by client or broker
    Compliance Analysis Endpoint - SEC Trade Reconstruction
    
    Analyzes broker-client communications against actual trade execution
    to detect compliance violations:
    
    1. Slippage Detection (Best Execution)
    2. Suitability Checks (KYC)
    3. Solicitation Classification
    
    Used for SEC investigations and internal audits.
    Chat endpoint for React frontend
    
    Processes natural language messages and returns parsed trade data
    with a friendly response message.
    
    Args:
        chat: ChatMessage with user input
        user: Authenticated user from JWT token
        
    Returns:
        ChatResponse with trade data and friendly message
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
        reload=True,
        log_level="info"
    )
