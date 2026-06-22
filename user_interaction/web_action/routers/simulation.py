"""仿真管理路由模块

提供仿真启动和仿真日志查看的API接口。
"""

import os
import sys
from datetime import datetime
from typing import Optional, Dict, Any

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from user_interaction.web_action.models import (
    SimulationStartRequest, SimulationLogResponse, ApiResponse, PageResponse
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


@router.post("/start", response_class=HTMLResponse)
async def start_simulation(request: Request, req: SimulationStartRequest):
    """e. 启动仿真
    
    接收仿真启动请求，返回启动结果页面。
    """
    simulation_id = f"SIM_{req.solution_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    return _build_html_page(
        PageResponse(
            title="仿真启动",
            message=f"方案 [{req.solution_id}] 仿真已启动",
            status="success",
            detail=f"仿真ID: {simulation_id} | 任务清单: {req.manifest_id or '默认清单'} | 启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
    )


@router.get("/log/{solution_id}/{simulation_id}", response_class=HTMLResponse)
async def get_simulation_log(solution_id: str, simulation_id: str, request: Request):
    """e. 查看仿真日志
    
    获取指定方案的仿真日志，返回日志页面。
    """
    return _build_html_page(
        PageResponse(
            title="仿真日志",
            message=f"方案 [{solution_id}] 仿真日志",
            status="success",
            detail=f"仿真ID: {simulation_id} | 日志内容展示页面（待实现）"
        )
    )


@router.get("/status/{solution_id}/{simulation_id}", response_class=HTMLResponse)
async def get_simulation_status(solution_id: str, simulation_id: str, request: Request):
    """获取仿真状态"""
    return _build_html_page(
        PageResponse(
            title="仿真状态",
            message=f"方案 [{solution_id}] 仿真状态",
            status="success",
            detail=f"仿真ID: {simulation_id} | 状态: 运行中 | 进度: 45%"
        )
    )


@router.post("/stop/{solution_id}/{simulation_id}", response_class=HTMLResponse)
async def stop_simulation(solution_id: str, simulation_id: str, request: Request):
    """停止仿真"""
    return _build_html_page(
        PageResponse(
            title="停止仿真",
            message=f"方案 [{solution_id}] 仿真已停止",
            status="success",
            detail=f"仿真ID: {simulation_id} | 停止时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
    )


@router.get("/list/{solution_id}", response_class=HTMLResponse)
async def list_simulations(solution_id: str, request: Request):
    """获取仿真列表"""
    return _build_html_page(
        PageResponse(
            title="仿真列表",
            message=f"方案 [{solution_id}] 仿真列表",
            status="success",
            detail="仿真历史列表（待实现）"
        )
    )
