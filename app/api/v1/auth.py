import logging
import re
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError
from passlib.hash import pbkdf2_sha256
from pydantic import BaseModel, EmailStr, ConfigDict, Field
from sqlalchemy.orm import Session

from app.auth.jwt_auth import get_current_user
from app.config.settings import settings
from app.db.models import Usuario
from app.db.session import get_db

logger = logging.getLogger(__name__)
router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


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
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(hours=settings.JWT_EXPIRATION_HOURS))
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

    password_hash = pbkdf2_sha256.hash(user_data.password)

    user = Usuario(
        email=user_data.email,
        password_hash=password_hash,
        password_salt=None,
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

    if not pbkdf2_sha256.verify(form_data.password, user.password_hash):
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