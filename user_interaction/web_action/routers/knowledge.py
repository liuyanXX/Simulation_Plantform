"""知识管理路由模块

提供知识库列表、知识条目增删改查的API接口。
"""

import os
import sys
from datetime import datetime
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from user_interaction.web_action.models import ApiResponse
from knowledge_management.knowledge_manager import KnowledgeManager
from knowledge_management.models import Knowledge, KnowledgeQueryParams

router = APIRouter()

# 初始化知识管理器
_knowledge_manager = None


def get_knowledge_manager() -> KnowledgeManager:
    """获取知识管理器实例"""
    global _knowledge_manager
    if _knowledge_manager is None:
        _knowledge_manager = KnowledgeManager()
    return _knowledge_manager


class KnowledgeAddRequest(BaseModel):
    """知识添加请求"""
    knowledge_base: str
    knowledge_id: str
    title: str
    summary: str
    content: str
    tags: List[str] = []
    category: str = "evaluation"


class KnowledgeUpdateRequest(BaseModel):
    """知识更新请求"""
    knowledge_id: str
    title: str
    summary: str
    content: str
    tags: List[str] = []
    category: str


class KnowledgeDeleteRequest(BaseModel):
    """知识删除请求"""
    knowledge_ids: List[str]


@router.get("/list")
async def list_knowledge(
    category: str = "evaluation",
    page: int = 1,
    pageSize: int = 10
):
    """
    获取知识列表
    
    :param category: 知识分类
    :param page: 页码
    :param pageSize: 每页条数
    :return: 知识列表
    """
    try:
        manager = get_knowledge_manager()
        
        # 创建查询参数
        query_params = KnowledgeQueryParams(
            category=category,
            is_active=True
        )
        
        # 获取指定分类的知识
        all_knowledge = manager.query_knowledge(query_params)
        
        # 计算分页
        total = len(all_knowledge)
        start = (page - 1) * pageSize
        end = start + pageSize
        items = all_knowledge[start:end]
        
        # 转换为响应格式
        items_data = []
        for k in items:
            items_data.append({
                "knowledge_id": k.knowledge_id,
                "title": k.title,
                "summary": k.summary,
                "content": k.content,
                "tags": k.tags,
                "category": k.category,
                "created_at": k.created_at.isoformat() if hasattr(k.created_at, 'isoformat') else str(k.created_at),
                "updated_at": k.updated_at.isoformat() if hasattr(k.updated_at, 'isoformat') else str(k.updated_at)
            })
        
        return ApiResponse(
            success=True,
            code=200,
            message="获取知识列表成功",
            data={
                "items": items_data,
                "total": total,
                "page": page,
                "pageSize": pageSize
            }
        )
        
    except Exception as e:
        return ApiResponse(
            success=False,
            code=500,
            message=f"获取知识列表失败: {str(e)}",
            data=None
        )


@router.get("/detail")
async def get_knowledge_detail(knowledge_id: str):
    """
    获取知识详情
    
    :param knowledge_id: 知识ID
    :return: 知识详情
    """
    try:
        manager = get_knowledge_manager()
        knowledge = manager.get_knowledge(knowledge_id)
        
        if knowledge is None:
            return ApiResponse(
                success=False,
                code=404,
                message=f"知识不存在: {knowledge_id}",
                data=None
            )
        
        return ApiResponse(
            success=True,
            code=200,
            message="获取知识详情成功",
            data={
                "knowledge_id": knowledge.knowledge_id,
                "title": knowledge.title,
                "summary": knowledge.summary,
                "content": knowledge.content,
                "tags": knowledge.tags,
                "category": knowledge.category,
                "index_ids": knowledge.index_ids,
                "created_at": knowledge.created_at.isoformat() if hasattr(knowledge.created_at, 'isoformat') else str(knowledge.created_at),
                "updated_at": knowledge.updated_at.isoformat() if hasattr(knowledge.updated_at, 'isoformat') else str(knowledge.updated_at),
                "is_active": knowledge.is_active
            }
        )
        
    except Exception as e:
        return ApiResponse(
            success=False,
            code=500,
            message=f"获取知识详情失败: {str(e)}",
            data=None
        )


@router.post("/add")
async def add_knowledge(request: KnowledgeAddRequest):
    """
    添加知识
    
    :param request: 知识添加请求
    :return: 添加结果
    """
    try:
        manager = get_knowledge_manager()
        
        # 创建知识对象
        knowledge = Knowledge(
            knowledge_id=request.knowledge_id,
            title=request.title,
            summary=request.summary,
            content=request.content,
            tags=request.tags,
            category=request.category,
            index_ids=[],
            is_active=True
        )
        
        # 添加知识
        result = manager.add_knowledge(knowledge)
        
        if result:
            return ApiResponse(
                success=True,
                code=200,
                message="知识添加成功",
                data={
                    "knowledge_id": knowledge.knowledge_id,
                    "title": knowledge.title
                }
            )
        else:
            return ApiResponse(
                success=False,
                code=400,
                message="知识添加失败，可能ID已存在",
                data=None
            )
            
    except ValueError as e:
        return ApiResponse(
            success=False,
            code=400,
            message=f"知识添加失败: {str(e)}",
            data=None
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            code=500,
            message=f"知识添加失败: {str(e)}",
            data=None
        )


@router.post("/update")
async def update_knowledge(request: KnowledgeUpdateRequest):
    """
    更新知识
    
    :param request: 知识更新请求
    :return: 更新结果
    """
    try:
        manager = get_knowledge_manager()
        
        # 更新知识
        knowledge = manager.update_knowledge(
            request.knowledge_id,
            title=request.title,
            summary=request.summary,
            content=request.content,
            tags=request.tags,
            category=request.category
        )
        
        return ApiResponse(
            success=True,
            code=200,
            message="知识更新成功",
            data={
                "knowledge_id": request.knowledge_id,
                "title": request.title
            }
        )
            
    except ValueError as e:
        return ApiResponse(
            success=False,
            code=404,
            message=str(e),
            data=None
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            code=500,
            message=f"知识更新失败: {str(e)}",
            data=None
        )


@router.post("/delete")
async def delete_knowledge(request: KnowledgeDeleteRequest):
    """
    批量删除知识
    
    :param request: 知识删除请求
    :return: 删除结果
    """
    try:
        manager = get_knowledge_manager()
        
        deleted_count = 0
        failed_ids = []
        
        for knowledge_id in request.knowledge_ids:
            try:
                result = manager.delete_knowledge(knowledge_id)
                if result:
                    deleted_count += 1
            except ValueError:
                failed_ids.append(knowledge_id)
        
        if deleted_count > 0:
            message = f"成功删除 {deleted_count} 条知识"
            if failed_ids:
                message += f"，{len(failed_ids)} 条删除失败"
            
            return ApiResponse(
                success=True,
                code=200,
                message=message,
                data={
                    "deleted_count": deleted_count,
                    "failed_ids": failed_ids
                }
            )
        else:
            return ApiResponse(
                success=False,
                code=400,
                message="删除失败，所有知识都不存在",
                data={"failed_ids": failed_ids}
            )
            
    except Exception as e:
        return ApiResponse(
            success=False,
            code=500,
            message=f"知识删除失败: {str(e)}",
            data=None
        )


@router.get("/bases")
async def list_knowledge_bases():
    """
    获取知识库列表
    
    :return: 知识库列表
    """
    # 系统预定义的知识库
    knowledge_bases = [
        {"id": "evaluation", "name": "评价指标库", "description": "评估相关的知识条目"},
        {"id": "decomposition", "name": "方案拆解库", "description": "方案拆解相关的知识条目"},
        {"id": "simulation", "name": "仿真知识库", "description": "仿真相关的知识条目"},
        {"id": "other", "name": "其他知识库", "description": "其他类型的知识条目"}
    ]
    
    return ApiResponse(
        success=True,
        code=200,
        message="获取知识库列表成功",
        data={"knowledge_bases": knowledge_bases}
    )