"""User API: authentication and session endpoints.

Separate FastAPI app deployed as its own pod. Shares the Postgres `users`
table and the AUTH_SECRET JWT key with the main backend. Responsibilities:
verify credentials, issue JWTs, expose /auth/me for token introspection.
"""

import logging

from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

import jwt

from auth.jwt_tokens import decode, issue
from auth.passwords import verify_password
from database.database import get_db
from database.models.user import User
from logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title="Z-Alpha User API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str


class MeResponse(BaseModel):
    username: str
    email: str


def _require_bearer(authorization: str | None) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    return authorization.split(None, 1)[1].strip()


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.post("/auth/login", response_model=LoginResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """Verify password (username OR email), return JWT on success.
    Error message is intentionally generic to avoid user-enumeration."""
    user = db.query(User).filter(
        (User.username == req.username) | (User.email == req.username)
    ).first()

    if not user or not verify_password(req.password, user.password_hash):
        logger.info("Failed login for identifier=%s", req.username)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = issue(user.username)
    logger.info("Login OK for username=%s", user.username)
    return LoginResponse(access_token=token, username=user.username)


@app.get("/auth/me", response_model=MeResponse)
def me(authorization: str | None = Header(default=None), db: Session = Depends(get_db)):
    token = _require_bearer(authorization)
    try:
        claims = decode(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = db.query(User).filter(User.username == claims.get("sub")).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return MeResponse(username=user.username, email=user.email)
