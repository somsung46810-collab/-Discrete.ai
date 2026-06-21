from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Annotated
from uuid import uuid4

import httpx
import jwt
import stripe
from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from pwdlib import PasswordHash
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, sessionmaker


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="DISCRETE_", extra="ignore")
    env: str = "development"
    secret_key: str = "development-only-change-me"
    database_url: str = "sqlite:///./discrete_art_studio.db"
    storage_dir: str = "./storage"
    public_base_url: str = "http://127.0.0.1:8000"
    image_provider_url: str = ""
    image_provider_token: str = ""
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    starting_credits: int = 20


settings = Settings()
ROOT = Path(__file__).resolve().parent
STORAGE = Path(settings.storage_dir).resolve()
STORAGE.mkdir(parents=True, exist_ok=True)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    display_name: Mapped[str] = mapped_column(String(80))
    credits: Mapped[int] = mapped_column(Integer, default=20)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    creations: Mapped[list[Creation]] = relationship(back_populates="owner", cascade="all, delete-orphan")


class Creation(Base):
    __tablename__ = "creations"
    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    prompt: Mapped[str] = mapped_column(Text)
    style: Mapped[str] = mapped_column(String(50), default="Cinematic")
    mode: Mapped[str] = mapped_column(String(30), default="Wireframe")
    image_url: Mapped[str] = mapped_column(String(500), default="")
    likes: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    owner: Mapped[User] = relationship(back_populates="creations")


engine = create_engine(settings.database_url, connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {})
SessionLocal = sessionmaker(engine, expire_on_commit=False)
Base.metadata.create_all(engine)
password_hash = PasswordHash.recommended()
oauth2 = OAuth2PasswordBearer(tokenUrl="/api/auth/token")


class RegisterBody(BaseModel):
    email: EmailStr
    password: str
    display_name: str


class GenerateBody(BaseModel):
    prompt: str
    style: str = "Cinematic"
    mode: str = "Wireframe"


class CreationOut(BaseModel):
    id: int
    prompt: str
    style: str
    mode: str
    image_url: str
    likes: int
    owner_id: int


def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def issue_token(user_id: int) -> str:
    payload = {"sub": str(user_id), "exp": datetime.now(timezone.utc) + timedelta(hours=24)}
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def current_user(token: Annotated[str, Depends(oauth2)], db: Annotated[Session, Depends(db_session)]) -> User:
    try:
        user_id = int(jwt.decode(token, settings.secret_key, algorithms=["HS256"])["sub"])
    except Exception as exc:
        raise HTTPException(401, "Invalid or expired access token") from exc
    user = db.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(401, "User is unavailable")
    return user


async def provider_generate(body: GenerateBody) -> str:
    if not settings.image_provider_url:
        return ""
    headers = {"Authorization": f"Bearer {settings.image_provider_token}"} if settings.image_provider_token else {}
    async with httpx.AsyncClient(timeout=90) as client:
        response = await client.post(settings.image_provider_url, json=body.model_dump(), headers=headers)
        response.raise_for_status()
        data = response.json()
    return str(data.get("image_url", ""))


app = FastAPI(title="Discrete Art Studio API", version="0.2.0")


@app.get("/api/health")
def health():
    return {"status": "ok", "database": settings.database_url.split(":", 1)[0], "provider_configured": bool(settings.image_provider_url)}


@app.post("/api/auth/register")
def register(body: RegisterBody, db: Annotated[Session, Depends(db_session)]):
    if db.scalar(select(User).where(User.email == body.email.lower())):
        raise HTTPException(409, "Email is already registered")
    if len(body.password) < 8:
        raise HTTPException(400, "Password must contain at least 8 characters")
    user = User(email=body.email.lower(), password_hash=password_hash.hash(body.password), display_name=body.display_name.strip()[:80], credits=settings.starting_credits)
    db.add(user)
    db.commit()
    return {"access_token": issue_token(user.id), "token_type": "bearer"}


@app.post("/api/auth/token")
def token(form: Annotated[OAuth2PasswordRequestForm, Depends()], db: Annotated[Session, Depends(db_session)]):
    user = db.scalar(select(User).where(User.email == form.username.lower()))
    if not user or not password_hash.verify(form.password, user.password_hash):
        raise HTTPException(401, "Incorrect email or password")
    return {"access_token": issue_token(user.id), "token_type": "bearer"}


@app.get("/api/me")
def me(user: Annotated[User, Depends(current_user)]):
    return {"id": user.id, "email": user.email, "display_name": user.display_name, "credits": user.credits}


@app.get("/api/creations")
def list_creations(db: Annotated[Session, Depends(db_session)]):
    rows = db.scalars(select(Creation).order_by(Creation.created_at.desc()).limit(100)).all()
    return [CreationOut.model_validate(row, from_attributes=True) for row in rows]


@app.post("/api/creations")
async def create_art(body: GenerateBody, user: Annotated[User, Depends(current_user)], db: Annotated[Session, Depends(db_session)]):
    if user.credits < 1:
        raise HTTPException(402, "Not enough credits")
    if len(body.prompt.strip()) < 3:
        raise HTTPException(400, "Prompt is too short")
    image_url = await provider_generate(body)
    creation = Creation(owner_id=user.id, prompt=body.prompt.strip(), style=body.style, mode=body.mode, image_url=image_url)
    user.credits -= 1
    db.add(creation)
    db.commit()
    return CreationOut.model_validate(creation, from_attributes=True)


@app.post("/api/creations/{creation_id}/like")
def like_creation(creation_id: int, db: Annotated[Session, Depends(db_session)]):
    creation = db.get(Creation, creation_id)
    if not creation:
        raise HTTPException(404, "Creation not found")
    creation.likes += 1
    db.commit()
    return {"id": creation.id, "likes": creation.likes}


@app.post("/api/uploads")
async def upload(file: UploadFile = File(...), user: User = Depends(current_user)):
    suffix = Path(file.filename or "upload.bin").suffix.lower()
    if suffix not in {".png", ".jpg", ".jpeg", ".webp"}:
        raise HTTPException(400, "Unsupported image type")
    target = STORAGE / f"{user.id}-{uuid4().hex}{suffix}"
    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(413, "File exceeds 10 MB")
    target.write_bytes(contents)
    return {"url": f"/storage/{target.name}"}


@app.post("/api/billing/checkout")
def checkout(user: Annotated[User, Depends(current_user)]):
    if not settings.stripe_secret_key:
        raise HTTPException(503, "Stripe is not configured")
    stripe.api_key = settings.stripe_secret_key
    session = stripe.checkout.Session.create(
        mode="payment",
        line_items=[{"price_data": {"currency": "usd", "product_data": {"name": "100 Discrete credits"}, "unit_amount": 999}, "quantity": 1}],
        success_url=f"{settings.public_base_url}/?payment=success",
        cancel_url=f"{settings.public_base_url}/?payment=cancelled",
        metadata={"user_id": str(user.id), "credits": "100"},
    )
    return {"checkout_url": session.url}


app.mount("/storage", StaticFiles(directory=STORAGE), name="storage")
app.mount("/", StaticFiles(directory=ROOT, html=True), name="site")
