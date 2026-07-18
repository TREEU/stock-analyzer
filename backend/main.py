"""FastAPI 应用入口"""

import math
import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from backend.api.routes import router


class SafeJSONResponse(JSONResponse):
    """自动处理 NaN/Infinity 的 JSON 响应"""
    def render(self, content) -> bytes:
        cleaned = _sanitize_json(content)
        return json.dumps(cleaned, ensure_ascii=False, allow_nan=False).encode("utf-8")


def _sanitize_json(obj):
    """递归替换 NaN/Infinity 为 None"""
    if isinstance(obj, dict):
        return {k: _sanitize_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize_json(v) for v in obj]
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
    return obj


app = FastAPI(
    title="A股量化分析平台",
    description="个人A股量化分析工具 — 技术指标、估值、风险、回测、操作建议",
    version="1.0.0",
    default_response_class=SafeJSONResponse,
)

# CORS — 允许所有来源（本地+手机+云部署）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
async def root():
    return {"message": "A股量化分析平台 API", "docs": "/docs"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
