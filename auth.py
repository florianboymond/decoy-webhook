from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from jose import JWTError, jwt
from datetime import datetime, timedelta
import aiosqlite
import random
import string
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from config import config

router = APIRouter()
security = HTTPBearer()

class OTPRequest(BaseModel):
    email: EmailStr

class OTPVerify(BaseModel):
    email: EmailStr
    otp: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

def generate_otp() -> str:
    """Generate a 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=6))

def create_access_token(data: dict):
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=config.JWT_EXPIRATION_HOURS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, config.JWT_SECRET_KEY, algorithm=config.JWT_ALGORITHM)
    return encoded_jwt

async def send_otp_email(email: str, otp: str):
    """Send OTP via SendGrid"""
    if not config.SENDGRID_API_KEY:
        raise HTTPException(status_code=500, detail="Email service not configured")
    
    message = Mail(
        from_email=config.ALERT_SENDER,
        to_emails=email,
        subject="Your Honeypot Alerts Login Code",
        html_content=f"""
        <h2>Your Login Code</h2>
        <p>Use this code to log into Honeypot Alerts:</p>
        <h1 style="font-size: 32px; color: #007bff; letter-spacing: 4px;">{otp}</h1>
        <p>This code expires in 10 minutes.</p>
        <p>If you didn't request this, please ignore this email.</p>
        """
    )
    
    try:
        sg = SendGridAPIClient(config.SENDGRID_API_KEY)
        response = sg.send(message)
        print(f"OTP email sent to {email}, status: {response.status_code}")
    except Exception as e:
        print(f"Failed to send OTP email: {e}")
        raise HTTPException(status_code=500, detail="Failed to send OTP email")

async def is_user_authorized(email: str) -> bool:
    """Check if user is in authorized_users table"""
    async with aiosqlite.connect(config.DATABASE_PATH) as db:
        async with db.execute("SELECT email FROM authorized_users WHERE email = ?", (email,)) as cursor:
            result = await cursor.fetchone()
            return result is not None

async def store_otp(email: str, otp: str):
    """Store OTP in database with expiration"""
    expires_at = (datetime.utcnow() + timedelta(minutes=10)).isoformat()
    
    async with aiosqlite.connect(config.DATABASE_PATH) as db:
        await db.execute("""
            INSERT OR REPLACE INTO otps (email, code, expires_at, used)
            VALUES (?, ?, ?, FALSE)
        """, (email, otp, expires_at))
        await db.commit()

async def verify_otp_db(email: str, otp: str) -> bool:
    """Verify OTP from database"""
    async with aiosqlite.connect(config.DATABASE_PATH) as db:
        async with db.execute("""
            SELECT code, expires_at, used FROM otps 
            WHERE email = ? AND code = ?
        """, (email, otp)) as cursor:
            result = await cursor.fetchone()
            
            if not result:
                return False
            
            stored_code, expires_at, used = result
            
            # Check if already used
            if used:
                return False
            
            # Check if expired
            if datetime.utcnow() > datetime.fromisoformat(expires_at):
                return False
            
            # Mark as used
            await db.execute("""
                UPDATE otps SET used = TRUE WHERE email = ? AND code = ?
            """, (email, otp))
            await db.commit()
            
            return True

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user from JWT token"""
    try:
        payload = jwt.decode(credentials.credentials, config.JWT_SECRET_KEY, algorithms=[config.JWT_ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return email
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.post("/auth/request-otp")
async def request_otp(request: OTPRequest):
    """Request OTP for login"""
    # Check if user is authorized
    if not await is_user_authorized(request.email):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User not authorized"
        )
    
    # Generate and store OTP
    otp = generate_otp()
    await store_otp(request.email, otp)
    
    # Send OTP email
    await send_otp_email(request.email, otp)
    
    return {"message": "OTP sent to email"}

@router.post("/auth/verify-otp", response_model=TokenResponse)
async def verify_otp(request: OTPVerify):
    """Verify OTP and return JWT token"""
    # Verify OTP
    if not await verify_otp_db(request.email, request.otp):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired OTP"
        )
    
    # Create JWT token
    access_token = create_access_token(data={"sub": request.email})
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }