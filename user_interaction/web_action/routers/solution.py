"""方案管理路由模块

提供方案录入和保存的API接口。
"""

import os
import sys
from datetime import datetime
from typing import Optional, Dict, Any

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from user_interaction.web_action.models import (
    SolutionInput, SolutionResponse, ApiResponse, PageResponse
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


@router.post("/input", response_class=HTMLResponse)
async def input_solution(request: Request, solution: SolutionInput):
    """a. 录入方案
    
    接收用户录入的方案信息，返回确认页面。
    """
    return _build_html_page(
        PageResponse(
            title="方案录入",
            message=f"方案 [{solution.name}] 录入成功",
            status="success",
            detail=f"方案ID: {solution.solution_id} | 优先级: {solution.priority.value} | 负责人: {solution.owner or '未指定'}"
        )
    )


@router.post("/save", response_class=HTMLResponse)
async def save_solution(request: Request, solution: SolutionInput):
    """b. 保存方案
    
    保存录入的方案信息到关系数据库，返回保存结果页面。
    """
    import json
    
    # 打印接收到的方案对象（JSON格式）
    solution_dict = solution.model_dump(mode='json')
    print("=" * 60)
    print("收到方案保存请求:")
    print(json.dumps(solution_dict, ensure_ascii=False, indent=2, default=str))
    print("=" * 60)
    
    # 将 SolutionInput 转换为 Solution 对象并保存到数据库
    try:
        from bo.solution import Solution
        
        # 创建 Solution 对象，将 SolutionInput 的字段映射到 Solution
        solution_obj = Solution(
            solution_id=solution.solution_id,
            name=solution.name,
            version=solution.version,
            priority=solution.priority,
            purpose=solution.purpose,
            objectives=solution.objectives,
            initiatives=solution.initiatives,
            working_mechanism=solution.working_mechanism,
            organization=solution.organization,
            personnel=solution.personnel,
            roles=solution.roles,
            work_content=solution.work_content,
            constraints=solution.constraints,
            risks=solution.risks,
            issues=solution.issues,
            other_notes=solution.other_notes,
            description=solution.description,
            owner=solution.owner,
            created_by=solution.created_by,
            tags=solution.tags
        )
        
        # 调用 Solution 对象的 save() 方法保存到数据库
        save_result = solution_obj.save()
        
        if save_result:
            print(f"方案 [{solution.name}] 保存到数据库成功")
            return _build_html_page(
                PageResponse(
                    title="方案保存",
                    message=f"方案 [{solution.name}] 保存成功",
                    status="success",
                    detail=f"方案ID: {solution.solution_id} | 版本: {solution.version} | 保存时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
            )
        else:
            print(f"方案 [{solution.name}] 保存到数据库失败")
            return _build_html_page(
                PageResponse(
                    title="方案保存",
                    message=f"方案 [{solution.name}] 保存失败",
                    status="error",
                    detail="数据库保存操作返回失败"
                )
            )
    except Exception as e:
        print(f"方案保存到数据库时发生错误: {str(e)}")
        return _build_html_page(
            PageResponse(
                title="方案保存",
                message=f"方案 [{solution.name}] 保存失败",
                status="error",
                detail=f"保存过程中发生错误: {str(e)}"
            )
        )


@router.get("/{solution_id}", response_class=HTMLResponse)
async def get_solution(solution_id: str, request: Request):
    """获取方案信息"""
    return _build_html_page(
        PageResponse(
            title="方案详情",
            message=f"获取方案 [{solution_id}] 信息",
            status="success",
            detail="方案信息展示页面（待实现）"
        )
    )


@router.get("/list", response_class=HTMLResponse)
async def list_solutions(request: Request):
    """获取方案列表"""
    return _build_html_page(
        PageResponse(
            title="方案列表",
            message="方案列表查询成功",
            status="success",
            detail="方案列表展示页面（待实现）"
        )
    )


@router.delete("/{solution_id}", response_class=HTMLResponse)
async def delete_solution(solution_id: str, request: Request):
    """删除方案"""
    return _build_html_page(
        PageResponse(
            title="删除方案",
            message=f"方案 [{solution_id}] 删除成功",
            status="success",
            detail="方案已删除"
        )
    )
