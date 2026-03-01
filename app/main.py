# app/main.py
from fastapi import FastAPI
from app.api.auth import router as auth_router
from app.api.questions import router as questions_router
from app.core.database import engine, Base

app = FastAPI(title="Question Bank API")

# 创建数据库表
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

# 注册路由
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(questions_router, prefix="/questions", tags=["Questions"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)