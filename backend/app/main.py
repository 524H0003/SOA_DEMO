import json
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session

from datetime import datetime, timedelta

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import get_settings
from .db import get_db, init_db
from .models import AbsentRequest, User
from .schemas import AbsentRequestCreate, AbsentRequestResponse, PubSubEnvelope
from .schemas_auth import Token, UserCreate, UserLogin
from .services.gmail import send_absent_request
from .services.gmail_watch import decode_pubsub_data, sync_history

settings = get_settings()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

# JWT settings
SECRET_KEY = "your-secret-key-here"  # Change this in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(username: str, is_admin: bool) -> Token:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": username, "is_admin": is_admin, "exp": expire}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return Token(access_token=encoded_jwt, token_type="bearer")

def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenPayload(sub=username, is_admin=payload.get("is_admin", False))
    except JWTError:
        raise credentials_exception
    
    user = db.scalar(select(User).where(User.username == username))
    if user is None:
        raise credentials_exception
    return user

def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/absent-requests", response_model=list[AbsentRequestResponse])
def list_absent_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[AbsentRequest]:
    return list(db.scalars(select(AbsentRequest).order_by(AbsentRequest.created_at.desc())))


@app.post("/api/absent-requests", response_model=AbsentRequestResponse, status_code=status.HTTP_201_CREATED)
def create_absent_request(
    payload: AbsentRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> AbsentRequest:
    if not settings.manager_email:
        raise HTTPException(status_code=500, detail="MANAGER_EMAIL is not configured")
    request = AbsentRequest(**payload.model_dump(), manager_email=settings.manager_email)
    try:
        db.add(request)
        db.flush()
        request.gmail_message_id = send_absent_request(request, settings)
        db.commit()
    except RuntimeError as error:
        db.rollback()
        raise HTTPException(status_code=503, detail=str(error)) from error
    db.refresh(request)
    return request


@app.post("/api/webhooks/gmail", status_code=status.HTTP_204_NO_CONTENT)
async def gmail_webhook(
    envelope: PubSubEnvelope,
    token: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> None:
    if settings.pubsub_verification_token and token != settings.pubsub_verification_token:
        raise HTTPException(status_code=401, detail="Invalid Pub/Sub subscription")
    try:
        notification = decode_pubsub_data(envelope.message.data)
        history_id = notification["historyId"]
        sync_history(db, settings, history_id)
    except (KeyError, ValueError, json.JSONDecodeError) as error:
        raise HTTPException(status_code=400, detail="Invalid Gmail notification") from error


@app.post("/api/auth/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
) -> Token:
    hashed_password = get_password_hash(payload.password)
    user = User(
        username=payload.username,
        email=payload.email,
        hashed_password=hashed_password,
        is_admin=payload.is_admin,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return create_access_token(user.username, user.is_admin)


@app.post("/api/auth/login", response_model=Token)
def login_user(
    payload: UserLogin,
    db: Session = Depends(get_db),
) -> Token:
    user = db.scalar(select(User).where(User.username == payload.username))
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    return create_access_token(user.username, user.is_admin)
