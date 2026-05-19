from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime, timedelta
from jose import jwt, JWTError
import secrets
import hashlib
import re
import logging

from app.db.session import get_db
from app.db.models import Usuario
from app.config.settings import settings

router = APIRouter()
logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def _hash_password(password: str, salt: str) -> str:
    return hashlib.sha256(salt.encode() + password.encode()).hexdigest()


def _validate_password(password: str) -> tuple[bool, str]:
    if len(password) < 8:
        return False, "La contraseña debe tener al menos 8 caracteres"
    if not re.search(r"[A-Z]", password):
        return False, "La contraseña debe tener al menos una mayúscula"
    if not re.search(r"[a-z]", password):
        return False, "La contraseña debe tener al menos una minúscula"
    if not re.search(r"\d", password):
        return False, "La contraseña debe tener al menos un dígito"
    return True, ""


def _validate_email(email: str) -> bool:
    return bool(re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email))


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(hours=settings.JWT_EXPIRATION_HOURS))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    email: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    activo: bool
    created_at: datetime | None = None


@router.post("/register", response_model=TokenResponse)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    if not _validate_email(user_data.email):
        raise HTTPException(status_code=400, detail="Email inválido")

    valid, msg = _validate_password(user_data.password)
    if not valid:
        raise HTTPException(status_code=400, detail=msg)

    existing = db.query(Usuario).filter(Usuario.email == user_data.email).first()
    if existing:
        raise HTTPException(status_code=409, detail="El email ya está registrado")

    salt = secrets.token_hex(16)
    password_hash = _hash_password(user_data.password, salt)

    user = Usuario(
        email=user_data.email,
        password_hash=password_hash,
        password_salt=salt,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    logger.info(f"Usuario registrado: {user.email}")
    access_token = create_access_token(data={"sub": user.email, "user_id": user.id})

    return TokenResponse(
        access_token=access_token,
        user_id=user.id,
        email=user.email,
    )


@router.post("/login", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(Usuario).filter(Usuario.email == form_data.username).first()

    if not user or not user.activo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
            headers={"WWW-Authenticate": "Bearer"},
        )

    computed_hash = _hash_password(form_data.password, user.password_salt)
    if computed_hash != user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.info(f"Login exitoso: {user.email}")
    access_token = create_access_token(data={"sub": user.email, "user_id": user.id})

    return TokenResponse(
        access_token=access_token,
        user_id=user.id,
        email=user.email,
    )


@router.get("/me", response_model=UserResponse)
def get_current_user_info(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Token inválido")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")

    user = db.query(Usuario).filter(Usuario.email == email).first()
    if not user or not user.activo:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    return UserResponse.model_validate(user)