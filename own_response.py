import io
import os
from xml.dom.minidom import Element
from xml.etree.ElementTree import SubElement, tostring, Element
from typing import Any

import msgpack
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.responses import JSONResponse, Response
from starlette.responses import HTMLResponse, FileResponse, StreamingResponse

app = FastAPI()

class Item(BaseModel):
    name: str
    price: float

# Basic
@app.get("/items/{item_id}")
async def read_item(item_id: int):
    return {"item_id": item_id, "name": "Laptop", "price": 9999.99}

# 控制状态码，头信息
@app.get("/items/custom/{item_id}")
async def read_item_custom(item_id: int):
    content = {"item_id": item_id, "status": "ok"}

    return JSONResponse(
        content=content,
        status_code=200,
        headers={"X-Custom-Header": "SpecialValue"}
    )

# 返回HTML
@app.get("/html/website")
async def read_website():
    html_content = """
    <html>
        <head>
            <title>我的 FastAPI 页面</title>
            <style>
                body { font-family: Arial, sans-serif; background-color: #f0f0f0; }
                h1 { color: #333; }
            </style>
        </head>
        <body>
            <h1>你好，这是 HTML 响应！</h1>
            <p>FastAPI 也可以用来渲染简单的网页。</p>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content, status_code=200)

@app.get("/html/legacy")
async def read_legacy():
    return "<h1>This is HTML </h1>"

# 文件处理
@app.get("/download/{filename}")
async def download_file(filename: str):
    file_path = f"files/{filename}"

    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="File not find")
    return FileResponse(
        path=file_path,
        media_type="application/octet-stream",
        filename=filename,
        headers={"X-Download-Source:":"FastAPI"}
    )

# 如果想让浏览器预览图片，media_type 设为 "image/png" 或 "image/jpeg"
@app.get("/images/{filename}")
async def get_image(filename: str):
    if not os.path.isfile(filename):
        raise HTTPException(status_code=404, detail="File not find")
    return FileResponse(path=f"images/{filename}", media_type="image/png")

# SteamingRespone用于生成内容和内存文件
@app.get("/generate-csv")
async def generate_csv():
    stream = io.StringIO()
    stream.write("ID, name , Price\n")
    stream.write("1, Laptop, 999\n")
    stream.write("2, Phone, 599\n")

    stream.seek(0)

    return StreamingResponse(
        iter([stream.read()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=data.csv"}
    )

# Video
async def fake_video_stream(chunk_size: int = 1024):
    for i in range(10):
        yield b"fake video data chunk " + str(i).encode() * chunk_size

@app.get("/video-stream")
async def video_stream():
    return StreamingResponse(fake_video_stream(), media_type="video/mp4")

# XML
@app.get("/item/xml/{item_id}")
async def read_item_xml(item_id: int):
    root = Element("item")
    SubElement(root, "id").text = str(item_id)
    SubElement(root, "name").text = "Laptop"
    SubElement(root, "price").text = "999.99"

    xml_bytes = tostring(root, encoding='utf-8', method='xml')

    return Response(
        content=xml_bytes,
        media_type="application/xml",
        headers={"X-Custom-Format": "XML"}
    )

# 自定义回复类
class MessagePackResponse(Response):
    media_type = "application/x-msgpack"

    def render(self, content: Any) -> bytes:
        return msgpack.packb(content)
@app.post("/data/pack", response_class=MessagePackResponse)
async def send_packed_data(data: dict):
    return data