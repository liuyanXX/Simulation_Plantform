"""用户Web端服务子模块 - FastAPI主应用

为Web端用户界面提供RESTful API服务。
遵循面向对象设计原则和微服务设计原则。
"""

import os
import sys
from datetime import datetime
from typing import Optional, Dict, Any

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from user_interaction.web_action.models import ApiResponse, PageResponse
from user_interaction.web_action.routers import solution, decomposition, simulation, evaluation, display, knowledge

# 创建FastAPI应用实例
app = FastAPI(
    title="仿真平台用户交互服务",
    description="为Web端用户界面提供API服务的FastAPI应用",
    version="1.0.0"
)

# 配置CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(solution.router, prefix="/api/solution", tags=["方案管理"])
app.include_router(decomposition.router, prefix="/api/decomposition", tags=["方案拆分"])
app.include_router(simulation.router, prefix="/api/simulation", tags=["仿真管理"])
app.include_router(evaluation.router, prefix="/api/evaluation", tags=["评估管理"])
app.include_router(display.router, prefix="/api/display", tags=["信息展示"])
app.include_router(knowledge.router, prefix="/api/knowledge", tags=["知识管理"])


@app.get("/", response_class=HTMLResponse)
async def root():
    """根路径 - 返回前端页面"""
    index_path = os.path.join(os.path.dirname(__file__), "..", "web_front", "index.html")
    try:
        with open(index_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return _build_html_page(
            PageResponse(
                title="页面未找到",
                message="前端页面文件不存在",
                status="error",
                detail=f"请确保文件存在: {index_path}"
            )
        )


@app.get("/admin", response_class=HTMLResponse)
async def admin():
    """管理页面 - 返回服务状态页面"""
    return _build_html_page(
        PageResponse(
            title="仿真平台用户交互服务",
            message="服务运行正常",
            status="success",
            detail=f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
    )


@app.get("/api/health")
async def health_check():
    """健康检查接口"""
    return ApiResponse(
        success=True,
        code=200,
        message="服务健康",
        data={
            "service": "user_interaction",
            "status": "running",
            "timestamp": datetime.now().isoformat()
        }
    )


def _build_html_page(page: PageResponse) -> str:
    """构建HTML页面"""
    status_color = {
        "success": "#2ecc71",
        "error": "#e74c3c",
        "warning": "#f39c12",
        "info": "#3498db"
    }.get(page.status, "#3498db")
    
    html = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{page.title}</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;
                background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
                min-height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
                color: #fff;
            }}
            .container {{
                text-align: center;
                padding: 40px;
                background: rgba(255, 255, 255, 0.05);
                border-radius: 20px;
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255, 255, 255, 0.1);
                max-width: 600px;
                width: 90%;
            }}
            .status-icon {{
                width: 80px;
                height: 80px;
                margin: 0 auto 24px;
                border-radius: 50%;
                background: {status_color};
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 40px;
            }}
            h1 {{ font-size: 28px; margin-bottom: 16px; font-weight: 600; }}
            .message {{ font-size: 18px; margin-bottom: 12px; opacity: 0.9; }}
            .detail {{ font-size: 14px; opacity: 0.7; margin-top: 16px; }}
            .api-links {{
                margin-top: 24px;
                padding-top: 24px;
                border-top: 1px solid rgba(255, 255, 255, 0.1);
            }}
            .api-links a {{
                display: inline-block;
                margin: 8px;
                padding: 8px 16px;
                background: rgba(255, 255, 255, 0.1);
                color: #fff;
                text-decoration: none;
                border-radius: 8px;
                font-size: 14px;
                transition: background 0.3s;
            }}
            .api-links a:hover {{ background: rgba(255, 255, 255, 0.2); }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="status-icon">{'✓' if page.status == 'success' else '!'}</div>
            <h1>{page.title}</h1>
            <p class="message">{page.message}</p>
            {f'<p class="detail">{page.detail}</p>' if page.detail else ''}
            <div class="api-links">
                <a href="/api/health">健康检查</a>
                <a href="/docs">API文档</a>
            </div>
        </div>
    </body>
    </html>
    """
    return html


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
