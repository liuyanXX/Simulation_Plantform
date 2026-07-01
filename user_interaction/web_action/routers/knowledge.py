"""知识管理路由模块

提供知识库列表、知识条目增删改查、关键词检索的 API 接口。

路由约定:
  /api/knowledge/*            通用知识 (Knowledge) 接口 (category in decomposition / simulation / other)
  /api/knowledge/search       关键词检索: 按 category 分发到对应 manager
"""

import os
import sys
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple

from fastapi import APIRouter, Request, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from user_interaction.web_action.models import ApiResponse
from knowledge_management.knowledge_manager import KnowledgeManager
from knowledge_management.models import (
    Knowledge, KnowledgeQueryParams,
)

router = APIRouter()

_knowledge_manager: Optional[KnowledgeManager] = None


def get_knowledge_manager() -> KnowledgeManager:
    global _knowledge_manager
    if _knowledge_manager is None:
        _knowledge_manager = KnowledgeManager()
    return _knowledge_manager


def _fmt_datetime(v) -> str:
    if v is None:
        return ''
    if hasattr(v, 'isoformat'):
        return v.isoformat()
    return str(v)


def _serialize_knowledge(k: Knowledge) -> Dict[str, Any]:
    return {
        "knowledge_id": k.knowledge_id,
        "title": k.title,
        "summary": k.summary,
        "content": k.content,
        "tags": list(k.tags) if k.tags else [],
        "category": k.category,
        "index_ids": list(k.index_ids) if k.index_ids else [],
        "is_active": k.is_active,
        "created_at": _fmt_datetime(k.created_at),
        "updated_at": _fmt_datetime(k.updated_at),
    }


class KnowledgeAddRequest(BaseModel):
    knowledge_base: str
    knowledge_id: str
    title: str
    summary: str
    content: str
    tags: List[str] = []
    category: str = "decomposition"


class KnowledgeUpdateRequest(BaseModel):
    knowledge_id: str
    title: str
    summary: str
    content: str
    tags: List[str] = []
    category: str


class KnowledgeDeleteRequest(BaseModel):
    knowledge_ids: List[str]


# ---------------------------------------------------------------------------
# 知识库清单
# ---------------------------------------------------------------------------

@router.get("/bases")
async def list_knowledge_bases():
    knowledge_bases = [
        {"id": "decomposition","name": "方案拆解库", "description": "方案拆解任务相关的知识条目（Knowledge 对象）",               "object_type": "Knowledge"},
        {"id": "simulation",   "name": "仿真知识库", "description": "仿真相关的知识条目（Knowledge 对象）",                    "object_type": "Knowledge"},
        {"id": "other",        "name": "其他知识库", "description": "其他类型的知识条目（Knowledge 对象）",                    "object_type": "Knowledge"},
    ]
    return ApiResponse(
        success=True, code=200, message="获取知识库列表成功",
        data={"knowledge_bases": knowledge_bases}
    )


# ---------------------------------------------------------------------------
# 通用知识 (Knowledge): decomposition / simulation / other
# ---------------------------------------------------------------------------

@router.get("/list")
async def list_knowledge(
    category: str = "decomposition",
    page: int = 1,
    pageSize: int = 10,
    keyword: Optional[str] = Query(None, description="可选，按标题/摘要/内容模糊检索"),
):
    try:
        manager = get_knowledge_manager()
        query_params = KnowledgeQueryParams(category=category, is_active=True)
        all_knowledge = manager.query_knowledge(query_params)

        if keyword:
            kw = keyword.lower()
            all_knowledge = [
                k for k in all_knowledge
                if kw in k.title.lower()
                or kw in k.summary.lower()
                or kw in k.content.lower()
            ]

        total = len(all_knowledge)
        start = max(0, (page - 1) * pageSize)
        end = start + pageSize
        items = all_knowledge[start:end]

        return ApiResponse(
            success=True, code=200, message="获取知识列表成功",
            data={
                "items": [_serialize_knowledge(k) for k in items],
                "total": total,
                "page": page,
                "pageSize": pageSize,
                "object_type": "Knowledge",
            }
        )
    except Exception as e:
        return ApiResponse(success=False, code=500, message=f"获取知识列表失败: {e}", data=None)


@router.get("/detail")
async def get_knowledge_detail(knowledge_id: str = Query(..., description="知识ID")):
    try:
        manager = get_knowledge_manager()
        knowledge = manager.get_knowledge(knowledge_id)
        if knowledge is None:
            return ApiResponse(success=False, code=404, message=f"知识不存在: {knowledge_id}", data=None)
        return ApiResponse(
            success=True, code=200, message="获取知识详情成功",
            data={**_serialize_knowledge(knowledge), "object_type": "Knowledge"}
        )
    except Exception as e:
        return ApiResponse(success=False, code=500, message=f"获取知识详情失败: {e}", data=None)


@router.post("/add")
async def add_knowledge(request: KnowledgeAddRequest):
    try:
        manager = get_knowledge_manager()
        knowledge = Knowledge(
            knowledge_id=request.knowledge_id,
            title=request.title,
            summary=request.summary,
            content=request.content,
            tags=list(request.tags or []),
            category=request.category or "decomposition",
            index_ids=[],
            is_active=True,
        )
        manager.add_knowledge(knowledge)
        return ApiResponse(
            success=True, code=200, message="知识添加成功",
            data={**_serialize_knowledge(knowledge), "object_type": "Knowledge"}
        )
    except ValueError as e:
        return ApiResponse(success=False, code=400, message=str(e), data=None)
    except Exception as e:
        return ApiResponse(success=False, code=500, message=f"知识添加失败: {e}", data=None)


@router.post("/update")
async def update_knowledge(request: KnowledgeUpdateRequest):
    try:
        manager = get_knowledge_manager()
        knowledge = manager.update_knowledge(
            request.knowledge_id,
            title=request.title,
            summary=request.summary,
            content=request.content,
            tags=list(request.tags or []),
            category=request.category,
        )
        return ApiResponse(
            success=True, code=200, message="知识更新成功",
            data={**_serialize_knowledge(knowledge), "object_type": "Knowledge"}
        )
    except ValueError as e:
        return ApiResponse(success=False, code=404, message=str(e), data=None)
    except Exception as e:
        return ApiResponse(success=False, code=500, message=f"知识更新失败: {e}", data=None)


@router.post("/delete")
async def delete_knowledge(request: KnowledgeDeleteRequest):
    try:
        manager = get_knowledge_manager()
        deleted_count = 0
        failed_ids = []
        for knowledge_id in request.knowledge_ids:
            try:
                manager.delete_knowledge(knowledge_id)
                deleted_count += 1
            except ValueError:
                failed_ids.append(knowledge_id)

        if deleted_count > 0:
            return ApiResponse(
                success=True, code=200,
                message=f"成功删除 {deleted_count} 条知识",
                data={"deleted_count": deleted_count, "failed_ids": failed_ids}
            )
        return ApiResponse(success=False, code=400, message="删除失败", data={"failed_ids": failed_ids})
    except Exception as e:
        return ApiResponse(success=False, code=500, message=f"知识删除失败: {e}", data=None)


# ---------------------------------------------------------------------------
# 通用检索 (按 category 分发)
# ---------------------------------------------------------------------------

@router.get("/search")
async def search_knowledge(
    keyword: str = Query(..., description="检索关键词"),
    category: str = Query("decomposition", description="知识库标识: decomposition/simulation/other"),
    page: int = 1,
    pageSize: int = 10,
):
    return await list_knowledge(
        category=category, page=page, pageSize=pageSize, keyword=keyword,
    )
