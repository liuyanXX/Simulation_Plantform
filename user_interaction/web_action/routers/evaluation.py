"""评估管理路由模块

提供评估启动、结果查看和评估中止的API接口。
"""

import os
import sys
from datetime import datetime
from typing import Optional, Dict, Any

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from user_interaction.web_action.models import (
    EvaluationStartRequest, EvaluationResultResponse, EvaluationAbortRequest,
    EvaluationAgentSelection, ApiResponse, PageResponse
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
async def start_evaluation(request: Request, req: EvaluationStartRequest):
    """f. 启动评估
    
    接收评估启动请求，包括选中的评估Agent和评价指标，返回启动结果页面。
    支持直接启动评估和带着仿真日志启动评估。
    """
    selected_agents_count = len([a for a in req.selected_agents if a.is_selected])
    selected_indices_count = len(req.selected_indices)
    
    return _build_html_page(
        PageResponse(
            title="评估启动",
            message=f"方案 [{req.solution_id}] 评估已启动",
            status="success",
            detail=f"评估ID: {req.evaluation_id} | 选中Agent: {selected_agents_count}个 | 选中指标: {selected_indices_count}个 | 使用仿真日志: {'是' if req.use_simulation_log else '否'} | 启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
    )


@router.get("/result/{evaluation_id}", response_class=HTMLResponse)
async def get_evaluation_result(evaluation_id: str, request: Request):
    """g. 查看评估结果
    
    获取指定评估的结果，返回结果展示页面。
    """
    return _build_html_page(
        PageResponse(
            title="评估结果",
            message=f"评估 [{evaluation_id}] 结果",
            status="success",
            detail="评估结果展示页面（待实现）"
        )
    )


@router.post("/abort/{evaluation_id}", response_class=HTMLResponse)
async def abort_evaluation(evaluation_id: str, request: Request, abort_req: EvaluationAbortRequest):
    """h. 中止评估
    
    接收评估中止请求，返回中止结果页面。
    """
    return _build_html_page(
        PageResponse(
            title="评估中止",
            message=f"评估 [{evaluation_id}] 已中止",
            status="warning",
            detail=f"中止原因: {abort_req.reason or '用户手动中止'} | 中止时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
    )


@router.get("/agents", response_class=HTMLResponse)
async def list_evaluation_agents(request: Request):
    """获取评估Agent列表"""
    return _build_html_page(
        PageResponse(
            title="评估Agent列表",
            message="评估Agent列表查询成功",
            status="success",
            detail="可用评估Agent列表（待实现）"
        )
    )


@router.get("/indices", response_class=HTMLResponse)
async def list_evaluation_indices(request: Request):
    """获取评价指标列表"""
    return _build_html_page(
        PageResponse(
            title="评价指标列表",
            message="评价指标列表查询成功",
            status="success",
            detail="可用评价指标列表（待实现）"
        )
    )


@router.get("/status/{evaluation_id}", response_class=HTMLResponse)
async def get_evaluation_status(evaluation_id: str, request: Request):
    """获取评估状态"""
    return _build_html_page(
        PageResponse(
            title="评估状态",
            message=f"评估 [{evaluation_id}] 状态",
            status="success",
            detail="评估状态信息（待实现）"
        )
    )


@router.get("/list/{solution_id}", response_class=HTMLResponse)
async def list_evaluations(solution_id: str, request: Request):
    """获取评估列表"""
    return _build_html_page(
        PageResponse(
            title="评估列表",
            message=f"方案 [{solution_id}] 评估列表",
            status="success",
            detail="评估历史列表（待实现）"
        )
    )
