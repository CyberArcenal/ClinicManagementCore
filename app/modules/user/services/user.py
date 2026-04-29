# app/modules/user/user_service.py
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select, or_
from passlib.context import CryptContext
from jose import JWTError, jwt
from app.common.schema.base import PaginatedResponse
from app.modules.user.models import User
from app.modules.user.schemas import UserCreate, UserUpdate, UserResponse
from app.common.exceptions import UserNotFoundError, InvalidCredentialsError, UserAlreadyExistsError
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # Password & JWT utilities
    # ------------------------------------------------------------------
    @staticmethod
    def hash_password(password: str) -> str:
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt

    # ------------------------------------------------------------------
    # User CRUD
    # ------------------------------------------------------------------
    async def get_user(self, user_id: int, load_profiles: bool = False) -> Optional[User]:
        query = select(User).where(User.id == user_id)
        if load_profiles:
            # Optionally load relationships (doctor_profile, patient_record, etc.)
            # For simplicity, we can leave to caller to join
            pass
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_users(
        self,
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        page_size: int = 100,
        order_by: str = "id",
        descending: bool = False,
    ) -> PaginatedResponse[User]:
        query = select(User)
        if filters:
            if "role" in filters:
                query = query.where(User.role == filters["role"])
            if "is_active" in filters:
                query = query.where(User.is_active == filters["is_active"])
            if "email_contains" in filters:
                query = query.where(User.email.ilike(f"%{filters['email_contains']}%"))
            if "full_name_contains" in filters:
                query = query.where(User.full_name.ilike(f"%{filters['full_name_contains']}%"))

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query)

        # Order by
        order_col = getattr(User, order_by, User.id)
        if descending:
            query = query.order_by(order_col.desc())
        else:
            query = query.order_by(order_col.asc())

        # Pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        result = await self.db.execute(query)
        items = result.scalars().all()

        pages = (total + page_size - 1) // page_size if total > 0 else 0
        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            size=page_size,
            pages=pages
        )

    async def create_user(self, data: UserCreate) -> User:
        # Check if email already exists
        existing = await self.get_user_by_email(data.email)
        if existing:
            raise UserAlreadyExistsError(f"User with email {data.email} already exists")
        hashed = self.hash_password(data.password)
        user = User(
            email=data.email,
            hashed_password=hashed,
            full_name=data.full_name,
            role=data.role,
            is_active=data.is_active,
            phone_number=data.phone_number,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update_user(self, user_id: int, data: UserUpdate) -> Optional[User]:
        user = await self.get_user(user_id)
        if not user:
            raise UserNotFoundError(f"User {user_id} not found")
        update_data = data.model_dump(exclude_unset=True)
        if "password" in update_data:
            update_data["hashed_password"] = self.hash_password(update_data.pop("password"))
        if "email" in update_data and update_data["email"] != user.email:
            existing = await self.get_user_by_email(update_data["email"])
            if existing:
                raise UserAlreadyExistsError(f"Email {update_data['email']} already used")
        for key, value in update_data.items():
            setattr(user, key, value)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def delete_user(self, user_id: int) -> bool:
        user = await self.get_user(user_id)
        if not user:
            return False
        # Optional: instead of hard delete, set is_active=False
        user.is_active = False
        await self.db.commit()
        return True

    async def authenticate(self, email: str, password: str) -> Optional[User]:
        user = await self.get_user_by_email(email)
        if not user or not self.verify_password(password, user.hashed_password):
            return None
        if not user.is_active:
            return None
        return user

    async def change_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        user = await self.get_user(user_id)
        if not user or not self.verify_password(old_password, user.hashed_password):
            raise InvalidCredentialsError("Current password is incorrect")
        user.hashed_password = self.hash_password(new_password)
        await self.db.commit()
        return True

    async def reset_password(self, email: str, new_password: str) -> bool:
        user = await self.get_user_by_email(email)
        if not user:
            raise UserNotFoundError(f"User with email {email} not found")
        user.hashed_password = self.hash_password(new_password)
        await self.db.commit()
        return True