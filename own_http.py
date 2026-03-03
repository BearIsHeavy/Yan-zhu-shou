from fastapi import FastAPI, Path, Header, Cookie, UploadFile, File
from typing import Optional
from pydantic import BaseModel, Field

app = FastAPI()

# 简单路由
@app.get("/simple")
async def read_items():
    return [{"item_id": 1, "name": "Laptop"},
            {"item_id": 2, "name": "phone"} ]

@app.post("/items")
async def create_item():
    return {"message": "Item created"}

# 路径参数
@app.get("/items/{item_id}")
async def read_item(item_id: int):
    return {"item_id": item_id}

@app.get("/items/details/{item_id}")
async def read_item_detail(item_id: int = Path(
    ...,
    title="The ID of the item",
    ge=1,
    le=1
)):
    return {"item_id": item_id}

# 查询参数
@app.get("/items")
async def read_items(skip: int = 0, limit: int = 10, q: Optional[str] = None):
    result = {"skip": skip, "limit": limit}
    if q:
        result.update({"q": q})
    return result

# 请求体
class Item(BaseModel):
    name: str
    price: float
    description: Optional[str] = None
    tags: list[str]
    quantity: int = Field(
        ...,
        ge = 0,
        description="数量必须大于等于0"
    )

@app.post("/cus/items")
async def create_item(item: Item):
    return item

# 混合使用
@app.put("/cus/items/{item_id}")
async def update_item(
        item: Item,
        item_id: int,
        q: Optional[str] = None
):
    results = {"item_id": item_id, "item": item}
    if q:
        results.update({"q": q})
    return results

# HTTP Header
@app.get("/http/items/")
async def read_items(
        user_agent: str | None = Header(default=None)
):
    return {"User-Agent": user_agent}

# Cookie
@app.get("/cookie/items")
async def read_items(ads_id: str | None = Cookie(default=None)):
    return {"ads_id": ads_id}

# 表单数据
class FileResponseModel(BaseModel):
    filename: str
    size: int

@app.post("/files/")
async def create_file(file: UploadFile = File(...)):
    contents = await file.read()
    return {"filename": file.filename, "size": len(contents)}

