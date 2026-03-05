from contextlib import asynccontextmanager
from datetime import timedelta  # 补充缺失的导入
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import insert

# 假设这些模块在当前目录下存在
import models
import schemas
from database import engine, get_db, Base
from auth import hash_password, verify_password, create_access_token, verify_token


# ==================== LIFESPAN EVENT ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用启动时初始化数据库表
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield  # 应用运行期间
    # 这里可以添加关闭时的清理逻辑（如关闭连接池）


app = FastAPI(
    lifespan=lifespan,
    title="Login System Tutorial",
    description="A simple authentication system using FastAPI, SQLAlchemy (Async), and JWT",
    version="1.0.0"
)

# ==================== SECURITY & DEPENDENCIES ====================

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> models.User:
    """
    依赖项：验证 Token 并获取当前用户
    """
    # 1. 验证 Token
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # 2. 从 Token 中获取用户 ID
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # 3. 从数据库获取用户
    result = await db.execute(select(models.User).where(models.User.id == int(user_id)))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return user


# ==================== ENDPOINTS ====================

@app.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: schemas.UserRegister, db: AsyncSession = Depends(get_db)):
    """
    注册新用户
    - **email**: 用户邮箱
    - **username**: 唯一用户名 (3-50 字符)
    - **password**: 密码 (最少 6 字符)
    """
    # 1. 检查邮箱是否已存在
    result = await db.execute(select(models.User).where(models.User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    # 2. 检查用户名是否已存在
    result = await db.execute(select(models.User).where(models.User.username == user_data.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username already taken")

    # 3. 创建新用户（密码哈希化）
    db_user = models.User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=hash_password(user_data.password)
    )

    # 4. 提交到数据库
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)

    return db_user


@app.post("/login", response_model=schemas.Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    """
    登录并获取访问令牌
    - **username**: 可以是邮箱或用户名
    - **password**: 用户密码
    """
    # 1. 通过邮箱或用户名查找用户
    result = await db.execute(
        select(models.User).where(
            (models.User.email == form_data.username) |
            (models.User.username == form_data.username)
        )
    )
    user = result.scalar_one_or_none()

    # 2. 验证用户是否存在且密码正确
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # 3. 检查用户是否激活
    if not user.is_active:
        raise HTTPException(status_code=400, detail="User account is disabled")

    # 4. 创建 Access Token
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email},
        expires_delta=timedelta(minutes=30)
    )

    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/me", response_model=schemas.UserResponse)
async def get_current_user_info(current_user: models.User = Depends(get_current_user)):
    """
    获取当前登录用户的信息
    需要有效的认证令牌
    """
    return current_user


@app.get("/users/{user_id}", response_model=schemas.UserResponse)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    """
    根据 ID 获取用户信息 (公开接口，仅用于演示)
    """
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


@app.get("/")
async def root():
    """根路径欢迎信息"""
    return {
        "message": "Login System Tutorial",
        "endpoints": {
            "register": "POST /register",
            "login": "POST /login",
            "current_user": "GET /me",
            "get_user": "GET /users/{user_id}"
        }
    }