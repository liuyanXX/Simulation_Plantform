"""信息展示路由模块

提供任务信息、任务流组信息和任务图谱信息查看的API接口。
"""

import os
import sys
from datetime import datetime
from typing import Optional, Dict, Any

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from user_interaction.web_action.models import (
    TaskInfoResponse, FlowGroupInfoResponse, TaskGraphInfoResponse,
    ApiResponse, PageResponse
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


@router.get("/tasks/{solution_id}", response_class=HTMLResponse)
async def get_tasks(solution_id: str, request: Request):
    """d. 查看任务信息
    
    获取指定方案拆分后的任务信息，返回任务列表页面。
    """
    return _build_html_page(
        PageResponse(
            title="任务信息",
            message=f"方案 [{solution_id}] 任务信息",
            status="success",
            detail="任务列表展示页面（待实现）"
        )
    )


@router.get("/tasks/{solution_id}/{task_id}", response_class=HTMLResponse)
async def get_task_detail(solution_id: str, task_id: str, request: Request):
    """查看单个任务详情"""
    return _build_html_page(
        PageResponse(
            title="任务详情",
            message=f"方案 [{solution_id}] 任务 [{task_id}] 详情",
            status="success",
            detail="任务详细信息展示页面（待实现）"
        )
    )


@router.get("/flow-groups/{solution_id}", response_class=HTMLResponse)
async def get_flow_groups(solution_id: str, request: Request):
    """d. 查看任务流组信息
    
    获取指定方案拆分后的任务流组信息，返回任务流组列表页面。
    """
    return _build_html_page(
        PageResponse(
            title="任务流组信息",
            message=f"方案 [{solution_id}] 任务流组信息",
            status="success",
            detail="任务流组列表展示页面（待实现）"
        )
    )


@router.get("/flow-groups/{solution_id}/{flow_id}", response_class=HTMLResponse)
async def get_flow_group_detail(solution_id: str, flow_id: str, request: Request):
    """查看单个任务流组详情"""
    return _build_html_page(
        PageResponse(
            title="任务流组详情",
            message=f"方案 [{solution_id}] 任务流组 [{flow_id}] 详情",
            status="success",
            detail="任务流组详细信息展示页面（待实现）"
        )
    )


@router.get("/graph/{solution_id}", response_class=HTMLResponse)
async def get_task_graph(solution_id: str, request: Request):
    """d. 查看任务图谱信息
    
    获取指定方案拆分后的任务图谱信息，返回任务图谱可视化页面。
    """
    return _build_html_page(
        PageResponse(
            title="任务图谱信息",
            message=f"方案 [{solution_id}] 任务图谱信息",
            status="success",
            detail="任务图谱可视化展示页面（待实现）"
        )
    )


@router.get("/manifest/{solution_id}", response_class=HTMLResponse)
async def get_task_manifest(solution_id: str, request: Request):
    """查看任务清单信息"""
    return _build_html_page(
        PageResponse(
            title="任务清单信息",
            message=f"方案 [{solution_id}] 任务清单信息",
            status="success",
            detail="任务清单信息展示页面（待实现）"
        )
    )
