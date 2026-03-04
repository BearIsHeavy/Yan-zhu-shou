# 中间件学习
import time
import logging
from fastapi import FastAPI, Request, HTTPException, status
from starlette.responses import JSONResponse
from watchfiles import awatch

app = FastAPI()

@app.middleware("http")
async def custom_middleware(request: Request, call_next):
    start_time = time.time()
    print(f"received request: {request.method}{request.url.path}")

    response = await call_next(request)

    process_time = time.time() - start_time

    response.headers["X-Process-time"] = str(process_time)
    print(f"response status code: {response.status_code}, time: {process_time:.4f}s")

    return response

# 全日制记录
logger = logging.getLogger("my_app_logger")
logging.basicConfig(level=logging.INFO)

@app.middleware("http")
async def log_request(request: Request, call_next):
    client_host = request.client.host if request.client else "unknown"
    # Now this will work perfectly
    logger.info(f"Incoming request: {request.method} {request.url.path} from {client_host}")

    response = await call_next(request)

    logger.info(f"Outgoing response: {response.status_code}")
    return response

# 简单的身份认证和授权
@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    # 排除不需要认证的路径，比如登录接口
    if request.url.path in ["/docs", "/openapi.json", "/login"]:
        return await call_next(request)

    token = request.headers.get("Authorization")

    if not token or token != "Bearer secret-token-123":
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "error": "error",
                "message": "error"
            }
        )
    return await call_next(request)

# 跨域资源共享
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_options=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# GZip压缩
from fastapi.middleware.gzip import GZipMiddleware
app.add_middleware(GZipMiddleware, minimum_size=1000)
@app.get("/")
async def read_root():
    time.sleep(1)
    return {"message": "Hello world"}




