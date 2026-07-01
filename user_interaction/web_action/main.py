# -*- coding: utf-8 -*-
"""仿真平台 - 用户交互模块（Web 端 FastAPI 主入口）。

职责：
  - 挂载各业务子模块的 API 路由（/api/solution、/api/decomposition 等）。
  - 挂载静态资源：web_front 前端目录下的 css / js / modules。
  - 提供根路径 "/" 返回 web_front/index.html，作为首页框架。
  - 提供轻量的内部 _build_html_page 用于少数 fallback 页面（如 /page_not_found、/admin）。
    该函数仅用于后端兜底；前端 UI 已迁移至 web_front，因此不再内联大段 HTML。

编码说明：
  历史版本使用 GBK(CP936) 中文字面量，并包含内联大段 HTML 字符串（_build_html_page）。
  现统一改为 UTF-8 + UTF-8 中文/英文，并保留 `# -*- coding: utf-8 -*-` 作为默认解码提示。
"""

import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles


_THIS_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
_ROOT_DIR = _THIS_DIR.parent.parent
sys.path.insert(0, str(_ROOT_DIR))


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="仿真平台 - 用户交互服务",
    description="仿真平台 Web 端用户交互与管理服务（FastAPI）",
    version="1.0.0",
    lifespan=lifespan,
)


# 跨域（便于前端直接开发调试）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 业务路由挂载
from user_interaction.web_action.routers import (
    solution,
    decomposition,
    display,
    simulation,
    evaluation,
    knowledge,
    system,
    smeta_solution,
    km_indicator,
    srlt_evaluation,
)

app.include_router(solution.router, prefix="/api/solution", tags=["方案管理"])
app.include_router(decomposition.router, prefix="/api/decomposition", tags=["方案拆分"])
app.include_router(display.router, prefix="/api/display", tags=["信息展示"])
app.include_router(simulation.router, prefix="/api/simulation", tags=["仿真管理"])
app.include_router(evaluation.router, prefix="/api/evaluation", tags=["评估管理"])
app.include_router(knowledge.router, prefix="/api/knowledge", tags=["知识管理"])
app.include_router(system.router, prefix="/api/system", tags=["系统管理"])
app.include_router(smeta_solution.router, prefix="/api/smeta/solution", tags=["方案元空间"])
app.include_router(km_indicator.router, prefix="/api/km/indicator", tags=["指标管理库"])
app.include_router(srlt_evaluation.router, prefix="/api/srlt/evaluation", tags=["指标评估管理"])


# 前端静态资源
_web_front_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "web_front")
if os.path.isdir(_web_front_dir):
    app.mount("/css",     StaticFiles(directory=os.path.join(_web_front_dir, "css")),     name="web_front_css")
    app.mount("/js",      StaticFiles(directory=os.path.join(_web_front_dir, "js")),      name="web_front_js")
    app.mount("/modules", StaticFiles(directory=os.path.join(_web_front_dir, "modules")), name="web_front_modules")


@app.get("/", response_class=HTMLResponse)
async def index():
    """返回首页框架（web_front/index.html）。"""
    index_path = os.path.join(_web_front_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path, media_type="text/html")
    return _build_html_page(
        title="页面未找到",
        message="前端首页文件不存在，请确认部署完整性。",
        status="error",
        detail=f"web_front 目录: {_web_front_dir}",
    )


@app.get("/page_not_found", response_class=HTMLResponse)
async def page_not_found():
    return _build_html_page(
        title="页面未找到",
        message="您访问的页面不存在，已返回首页。",
        status="warn",
        detail="",
    )


@app.get("/admin", response_class=HTMLResponse)
async def admin():
    return _build_html_page(
        title="管理页面",
        message="管理服务正在启动中，稍后刷新页面重试。",
        status="ok",
        detail="",
    )


def _build_html_page(title="", message="", status="ok", detail=""):
    """构造一个简单的内部 fallback 页面。

    注意：前端主 UI 已迁移至 web_front，因此这里只返回一个简洁的内部提示页。
    参数与历史版本保持兼容（title/message/status/detail）。
    """
    status_icon_map = {
        "ok":      "<div class='status-icon'>✓</div>",
        "success": "<div class='status-icon'>✓</div>",
        "warn":    "<div class='status-icon'>⚠</div>",
        "error":   "<div class='status-icon'>✕</div>",
    }
    status_css_map = {
        "ok":      "#10b981",
        "success": "#10b981",
        "warn":    "#f59e0b",
        "error":   "#ef4444",
    }
    icon_html = status_icon_map.get((status or "ok").lower(), "<div class='status-icon'>!</div>")
    color     = status_css_map.get((status or "ok").lower(), "#10b981")

    safe_title  = (title  or "").replace('"', "&quot;")
    safe_msg    = (message or "").replace('"', "&quot;")
    safe_detail = (detail or "").replace('"', "&quot;")

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{safe_title or '提示'}</title>
    <style>
        body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Microsoft YaHei", Roboto, sans-serif;
               background: #f8fafc; display: flex; align-items: center; justify-content: center; min-height: 100vh; }}
        .card {{ padding: 40px; border-radius: 16px; background: #fff; box-shadow: 0 10px 30px rgba(0,0,0,.08);
                 max-width: 520px; width: 100%; box-sizing: border-box; }}
        h1 {{ margin: 0 0 8px; color: #1e293b; font-size: 22px; }}
        .status-icon {{ display: inline-flex; align-items: center; justify-content: center; width: 32px; height: 32px;
                        border-radius: 50%; margin-right: 8px; color: #fff; background: {color};
                        font-size: 18px; font-weight: 700; line-height: 1; float: left; }}
        .header {{ display: flex; align-items: center; margin-bottom: 16px; }}
        .message {{ font-size: 14px; color: #475569; margin-bottom: 12px; white-space: pre-wrap; }}
        .detail  {{ font-size: 12px; color: #94a3b8; white-space: pre-wrap; word-break: break-all; }}
        a.back {{ display: inline-block; margin-top: 20px; color: #4f46e5; text-decoration: none; font-size: 13px; }}
        a.back:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <div class="card">
        <div class="header">
            {icon_html}
            <h1>{safe_title or '提示'}</h1>
        </div>
        <div class="message">{safe_msg}</div>
        {f'<div class="detail">{safe_detail}</div>' if safe_detail else ''}
        <a class="back" href="/">返回首页</a>
    </div>
</body>
</html>"""
    return HTMLResponse(content=html, status_code=200)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "user_interaction.web_action.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
    )
