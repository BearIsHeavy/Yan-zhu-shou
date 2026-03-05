from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import insert, update, delete
from typing import List
import models
import schemas
from database import engine, get_db, Base


# --- 初始化数据库表 (仅用于开发演示，生产请用 Alembic) ---
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时执行
    await init_db()
    yield
    # 关闭时清理（如果需要）


app = FastAPI(lifespan=lifespan)


# ================= 用户路由 =================

@app.post("/users/", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    # 1. 检查邮箱是否已存在
    result = await db.execute(select(models.User).where(models.User.email == user.email))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # 2. 创建 ORM 对象 (实际项目中密码需要哈希处理，这里简化)
    # 注意：在 SQLAlchemy 2.0 中，可以直接实例化
    db_user = models.User(
        email=user.email,
        username=user.username,
        hashed_password=user.password  # TODO: 请使用 passlib.hash.bcrypt_context.hash(user.password)
    )

    # 3. 添加到会话
    db.add(db_user)

    # 4. 提交事务 (flush 可以获取生成的 ID)
    await db.commit()
    await db.refresh(db_user)  # 刷新以获取服务器生成的默认值 (如 created_at)

    return db_user


@app.get("/users/{user_id}", response_model=schemas.UserResponse)
async def read_user(user_id: int, db: AsyncSession = Depends(get_db)):
    # 使用 select 查询
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    db_user = result.scalar_one_or_none()

    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    return db_user


@app.get("/users/", response_model=List[schemas.UserResponse])
async def read_users(skip: int = 0, limit: int = 10, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.User).offset(skip).limit(limit))
    users = result.scalars().all()  # scalars() 提取 ORM 对象列表
    return users


# ================= 物品路由 (带关联查询) =================

@app.post("/users/{user_id}/items/", response_model=schemas.ItemResponse)
async def create_item_for_user(user_id: int, item: schemas.ItemCreate, db: AsyncSession = Depends(get_db)):
    # 1. 确认用户存在
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    db_user = result.scalar_one_or_none()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    # 2. 创建物品
    db_item = models.Item(**item.model_dump(), owner_id=user_id)
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)

    return db_item


@app.get("/users/{user_id}/items", response_model=List[schemas.ItemResponse])
async def read_user_items(user_id: int, db: AsyncSession = Depends(get_db)):
    # 方法 A: 先查用户，再访问关系属性 (需要预先加载或懒加载)
    # 为了性能，通常建议使用 select options 进行 join 加载，这里演示简单写法

    result = await db.execute(select(models.User).where(models.User.id == user_id))
    db_user = result.scalar_one_or_none()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    # 访问关系属性会自动触发新的查询 (懒加载)，或者如果你在 User 模型定义了 options
    # 更好的方式是直接查 Item 表
    item_result = await db.execute(select(models.Item).where(models.Item.owner_id == user_id))
    items = item_result.scalars().all()

    return items