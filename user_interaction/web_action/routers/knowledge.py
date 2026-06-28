"""知识管理路由模块

提供知识库列表、知识条目增删改查、评价指标增删改查、关键词检索的 API 接口。

路由约定:
  /api/knowledge/*            通用知识 (Knowledge) 接口 (category in decomposition / simulation / other)
  /api/knowledge/indices/*    评价指标 (EvaluationIndex) 专用接口 (category == evaluation)
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
from knowledge_management.index_manager import EvaluationIndexManager
from knowledge_management.models import (
    Knowledge, KnowledgeQueryParams,
    EvaluationIndex, IndexType, IndexLevel, IndexQueryParams,
)

router = APIRouter()

_knowledge_manager: Optional[KnowledgeManager] = None
_index_manager: Optional[EvaluationIndexManager] = None


def get_knowledge_manager() -> KnowledgeManager:
    global _knowledge_manager
    if _knowledge_manager is None:
        _knowledge_manager = KnowledgeManager()
    return _knowledge_manager


def get_index_manager() -> EvaluationIndexManager:
    global _index_manager
    if _index_manager is None:
        _index_manager = EvaluationIndexManager()
    return _index_manager


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


def _serialize_index(idx: EvaluationIndex) -> Dict[str, Any]:
    return {
        "index_id": idx.index_id,
        "name": idx.name,
        "description": idx.description,
        "evaluation_method": idx.evaluation_method,
        "agent_ids": list(idx.agent_ids) if idx.agent_ids else [],
        "index_type": idx.index_type.value if hasattr(idx.index_type, 'value') else str(idx.index_type),
        "index_level": idx.index_level.value if hasattr(idx.index_level, 'value') else str(idx.index_level),
        "parent_id": idx.parent_id,
        "weight": idx.weight,
        "score_range": list(idx.score_range) if isinstance(idx.score_range, (list, tuple)) else [0, 100],
        "is_active": idx.is_active,
        "category": "evaluation",
        "created_at": _fmt_datetime(idx.created_at),
        "updated_at": _fmt_datetime(idx.updated_at),
    }


class KnowledgeAddRequest(BaseModel):
    knowledge_base: str
    knowledge_id: str
    title: str
    summary: str
    content: str
    tags: List[str] = []
    category: str = "evaluation"


class KnowledgeUpdateRequest(BaseModel):
    knowledge_id: str
    title: str
    summary: str
    content: str
    tags: List[str] = []
    category: str


class KnowledgeDeleteRequest(BaseModel):
    knowledge_ids: List[str]


class IndexAddRequest(BaseModel):
    index_id: str
    name: str
    description: str
    evaluation_method: str
    index_type: str = "completeness"
    index_level: str = "level_1"
    parent_id: Optional[str] = None
    weight: float = 1.0
    score_min: float = 0.0
    score_max: float = 100.0
    agent_ids: List[str] = []


class IndexUpdateRequest(BaseModel):
    index_id: str
    name: Optional[str] = None
    description: Optional[str] = None
    evaluation_method: Optional[str] = None
    index_type: Optional[str] = None
    index_level: Optional[str] = None
    parent_id: Optional[str] = None
    weight: Optional[float] = None
    score_min: Optional[float] = None
    score_max: Optional[float] = None


class IndexDeleteRequest(BaseModel):
    index_ids: List[str]


# ---------------------------------------------------------------------------
# 知识库清单
# ---------------------------------------------------------------------------

@router.get("/bases")
async def list_knowledge_bases():
    knowledge_bases = [
        {"id": "evaluation",   "name": "评价指标库", "description": "针对方案设定的多层级多维度评价指标体系（EvaluationIndex 对象）", "object_type": "EvaluationIndex"},
        {"id": "decomposition","name": "方案拆解库", "description": "方案拆解任务相关的知识条目（Knowledge 对象）",               "object_type": "Knowledge"},
        {"id": "simulation",   "name": "仿真知识库", "description": "仿真相关的知识条目（Knowledge 对象）",                    "object_type": "Knowledge"},
        {"id": "other",        "name": "其他知识库", "description": "其他类型的知识条目（Knowledge 对象）",                    "object_type": "Knowledge"},
    ]
    return ApiResponse(
        success=True, code=200, message="获取知识库列表成功",
        data={"knowledge_bases": knowledge_bases}
    )


# ---------------------------------------------------------------------------
# 评价指标库 (EvaluationIndex)
# ---------------------------------------------------------------------------

@router.get("/indices/list")
async def list_indices(
    page: int = 1,
    pageSize: int = 10,
    keyword: Optional[str] = Query(None, description="可选，按指标ID/名称/说明/评估方法模糊检索"),
    index_type: Optional[str] = None,
    index_level: Optional[str] = None,
):
    try:
        manager = get_index_manager()
        params = IndexQueryParams()
        if index_type:
            try:
                params.index_type = IndexType(index_type)
            except ValueError:
                pass
        if index_level:
            try:
                params.index_level = IndexLevel(index_level)
            except ValueError:
                pass
        all_items = manager.query_indices(params)

        if keyword:
            kw = keyword.lower()
            all_items = [
                i for i in all_items
                if kw in i.index_id.lower()
                or kw in i.name.lower()
                or kw in i.description.lower()
                or kw in i.evaluation_method.lower()
            ]

        total = len(all_items)
        start = max(0, (page - 1) * pageSize)
        end = start + pageSize
        items = all_items[start:end]

        return ApiResponse(
            success=True, code=200, message="获取评价指标列表成功",
            data={
                "items": [_serialize_index(i) for i in items],
                "total": total,
                "page": page,
                "pageSize": pageSize,
                "object_type": "EvaluationIndex",
            }
        )
    except Exception as e:
        return ApiResponse(success=False, code=500, message=f"获取评价指标列表失败: {e}", data=None)


@router.get("/indices/detail")
async def get_index_detail(index_id: str = Query(..., description="指标ID")):
    try:
        manager = get_index_manager()
        idx = manager.get_index(index_id)
        if idx is None:
            return ApiResponse(success=False, code=404, message=f"评价指标不存在: {index_id}", data=None)
        return ApiResponse(
            success=True, code=200, message="获取评价指标详情成功",
            data={**_serialize_index(idx), "object_type": "EvaluationIndex"}
        )
    except Exception as e:
        return ApiResponse(success=False, code=500, message=f"获取评价指标详情失败: {e}", data=None)


@router.post("/indices/add")
async def add_index(request: IndexAddRequest):
    try:
        manager = get_index_manager()
        try:
            idx_type = IndexType(request.index_type)
        except ValueError:
            idx_type = IndexType.COMPLETENESS
        try:
            idx_level = IndexLevel(request.index_level)
        except ValueError:
            idx_level = IndexLevel.LEVEL_1

        score_range = (float(request.score_min), float(request.score_max))
        index = EvaluationIndex(
            index_id=request.index_id,
            name=request.name,
            description=request.description,
            evaluation_method=request.evaluation_method,
            agent_ids=list(request.agent_ids or []),
            index_type=idx_type,
            index_level=idx_level,
            parent_id=request.parent_id or None,
            weight=float(request.weight),
            score_range=score_range,
            is_active=True,
        )
        manager.add_index(index)
        return ApiResponse(
            success=True, code=200, message="评价指标添加成功",
            data={**_serialize_index(index), "object_type": "EvaluationIndex"}
        )
    except ValueError as e:
        return ApiResponse(success=False, code=400, message=str(e), data=None)
    except Exception as e:
        return ApiResponse(success=False, code=500, message=f"评价指标添加失败: {e}", data=None)


@router.post("/indices/update")
async def update_index(request: IndexUpdateRequest):
    try:
        manager = get_index_manager()
        kwargs: Dict[str, Any] = {}
        if request.name is not None:
            kwargs['name'] = request.name
        if request.description is not None:
            kwargs['description'] = request.description
        if request.evaluation_method is not None:
            kwargs['evaluation_method'] = request.evaluation_method
        if request.index_type is not None:
            try:
                kwargs['index_type'] = IndexType(request.index_type)
            except ValueError:
                pass
        if request.index_level is not None:
            try:
                kwargs['index_level'] = IndexLevel(request.index_level)
            except ValueError:
                pass
        if request.parent_id is not None:
            kwargs['parent_id'] = request.parent_id or None
        if request.weight is not None:
            kwargs['weight'] = float(request.weight)
        if request.score_min is not None and request.score_max is not None:
            kwargs['score_range'] = (float(request.score_min), float(request.score_max))

        index = manager.update_index(request.index_id, **kwargs)
        return ApiResponse(
            success=True, code=200, message="评价指标更新成功",
            data={**_serialize_index(index), "object_type": "EvaluationIndex"}
        )
    except ValueError as e:
        return ApiResponse(success=False, code=404, message=str(e), data=None)
    except Exception as e:
        return ApiResponse(success=False, code=500, message=f"评价指标更新失败: {e}", data=None)


@router.post("/indices/delete")
async def delete_indices(request: IndexDeleteRequest):
    try:
        manager = get_index_manager()
        deleted = 0
        failed = []
        for iid in request.index_ids:
            try:
                manager.delete_index(iid)
                deleted += 1
            except ValueError as e:
                failed.append({"index_id": iid, "reason": str(e)})

        if deleted > 0:
            return ApiResponse(
                success=True, code=200, message=f"成功删除 {deleted} 个评价指标",
                data={"deleted_count": deleted, "failed": failed}
            )
        return ApiResponse(success=False, code=400, message="删除失败", data={"failed": failed})
    except Exception as e:
        return ApiResponse(success=False, code=500, message=f"评价指标删除失败: {e}", data=None)


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
    category: str = Query("evaluation", description="知识库标识: evaluation/decomposition/simulation/other"),
    page: int = 1,
    pageSize: int = 10,
):
    if category == "evaluation":
        return await list_indices(
            page=page, pageSize=pageSize,
            keyword=keyword, index_type=None, index_level=None,
        )
    return await list_knowledge(
        category=category, page=page, pageSize=pageSize, keyword=keyword,
    )
