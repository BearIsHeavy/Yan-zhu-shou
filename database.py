from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

# 1. 数据库 URL
# 格式: postgresql+asyncpg://用户:密码@主机:端口/数据库名
# 注意：必须使用 +asyncpg 后缀来启用异步模式
DATABASE_URL = "postgresql+asyncpg://api:api@localhost:5432/fastapi_db"

# 2. 创建异步引擎
# echo=True 会在控制台打印 SQL 语句，方便调试
engine = create_async_engine(DATABASE_URL, echo=True, future=True)

# 3. 创建异步会话工厂
# expire_on_commit=False: 事务提交后不刷新对象属性，避免异步上下文中的常见问题
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# 4. 声明基类
# 所有 ORM 模型都将继承自这个 Base
Base = declarative_base()

# 5. 依赖注入：获取数据库会话
# 这是我们在路由中使用的 Depends(get_db) 的来源
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()