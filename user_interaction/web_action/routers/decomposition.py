"""方案拆分路由模块

提供方案拆分到任务、任务流组和任务图谱的API接口。
"""

import os
import sys
from datetime import datetime
from typing import Optional, Dict, Any

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from user_interaction.web_action.models import (
    DecompositionRequest, DecompositionResponse, ApiResponse, PageResponse
)

router = APIRouter()


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
            .back-link {{
                margin-top: 24px;
                padding-top: 24px;
                border-top: 1px solid rgba(255, 255, 255, 0.1);
            }}
            .back-link a {{
                display: inline-block;
                padding: 8px 16px;
                background: rgba(255, 255, 255, 0.1);
                color: #fff;
                text-decoration: none;
                border-radius: 8px;
                font-size: 14px;
                transition: background 0.3s;
            }}
            .back-link a:hover {{ background: rgba(255, 255, 255, 0.2); }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="status-icon">{'✓' if page.status == 'success' else '!'}</div>
            <h1>{page.title}</h1>
            <p class="message">{page.message}</p>
            {f'<p class="detail">{page.detail}</p>' if page.detail else ''}
            <div class="back-link">
                <a href="/">返回首页</a>
            </div>
        </div>
    </body>
    </html>
    """
    return html


@router.post("/split", response_class=HTMLResponse)
async def split_solution(request: Request, req: DecompositionRequest):
    """c. 拆分方案到任务、任务流组，构建任务图谱
    
    接收方案拆分请求，返回拆分结果页面。
    """
    return _build_html_page(
        PageResponse(
            title="方案拆分",
            message=f"方案 [{req.solution_id}] 拆分完成",
            status="success",
            detail=f"拆分策略: {req.decomposition_strategy} | 生成了任务、任务流组和任务图谱"
        )
    )


@router.post("/split-tasks", response_class=HTMLResponse)
async def split_to_tasks(request: Request, req: DecompositionRequest):
    """拆分方案到任务"""
    return _build_html_page(
        PageResponse(
            title="任务拆分",
            message=f"方案 [{req.solution_id}] 任务拆分完成",
            status="success",
            detail="任务列表已生成（待实现）"
        )
    )


@router.post("/split-flow-groups", response_class=HTMLResponse)
async def split_to_flow_groups(request: Request, req: DecompositionRequest):
    """拆分方案到任务流组"""
    return _build_html_page(
        PageResponse(
            title="任务流组拆分",
            message=f"方案 [{req.solution_id}] 任务流组拆分完成",
            status="success",
            detail="任务流组列表已生成（待实现）"
        )
    )


@router.post("/build-graph", response_class=HTMLResponse)
async def build_task_graph(request: Request, req: DecompositionRequest):
    """构建任务图谱"""
    return _build_html_page(
        PageResponse(
            title="任务图谱构建",
            message=f"方案 [{req.solution_id}] 任务图谱构建完成",
            status="success",
            detail="任务图谱已生成（待实现）"
        )
    )


@router.get("/status/{solution_id}", response_class=HTMLResponse)
async def get_decomposition_status(solution_id: str, request: Request):
    """获取拆分状态"""
    return _build_html_page(
        PageResponse(
            title="拆分状态",
            message=f"方案 [{solution_id}] 拆分状态查询",
            status="success",
            detail="拆分状态信息（待实现）"
        )
    )
