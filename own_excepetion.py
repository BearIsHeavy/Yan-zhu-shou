from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

app = FastAPI()
items_db = {"foo": "Bar", "bar": "foo"}

@app.get("/item/{item_id)")
async def read_item(item_id: str):
    if item_id not in items_db:
        raise HTTPException(
            status_code=404,
            detail=f"item {item_id} is not find",
            headers={"X-Error-Code": "ITEM_NOT_FOUND"}
        )
    return {"item_id": item_id, "name": items_db[item_id]}

class CustomBusinessError(Exception):
    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message

# 1. 处理自定义异常
@app.exception_handler(CustomBusinessError)
async def custom_bussiness_error_hander(request: Request, exc: CustomBusinessError):
    return JSONResponse(
        status_code=exc.code,
        content={
            "error": "BusinessError",
            "code": exc.code,
            "message": exc.message,
            "path": request.url.path
        }
    )

# 2. 处理普通的python ValueError （全局捕获）
@app.exception_handler(ValueError)
async def value_error_hander(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=400,
        content={
            "error": "Bad Request",
            "message": f"not failed verified data: {str(exc)}"
        }
    )

@app.get("/trigger-custom-error")
async def trigger_custom():
    raise CustomBusinessError(code=409, message="source confiction, operation is fail")

@app.get("/trigger-value-error")
async def trigger_value():
    raise ValueError("This isn't a vaulid data")

# 重写默认的 422 处理逻辑
@app.exception_handler(RequestValidationError)
async def validation_exception_hand(request: Request, exc: RequestValidationError):
    errors = []
    for error in exc.errors():
        loc = "->".join(str(x) for x in error['loc'])
        errors.append(f"{loc}: {error['msg']}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content= {
            "error": "Validation Failed",
            "details": errors
        }
    )