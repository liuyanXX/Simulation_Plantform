# -*- coding: utf-8 -*-
"""知识空间 · 指标管理库路由模块

提供指标分类分级目录、通用指标、指标配套附件的 CRUD API。
路由前缀: /api/km/indicator (在 main.py 注册)。

约定响应: {"success": bool, "message": str, "data": Any}
底层通过 IndicatorLibraryManager (knowledge_management.evaluation_indices) 编排。
"""
import os
import sys
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from knowledge_management.evaluation_indices import IndicatorLibraryManager

router = APIRouter()

_manager: Optional[IndicatorLibraryManager] = None


def _mgr() -> IndicatorLibraryManager:
    global _manager
    if _manager is None:
        _manager = IndicatorLibraryManager()
    return _manager


def _ok(data: Any = None, message: str = "ok"):
    return JSONResponse({"success": True, "message": message, "data": data})


def _err(message: str, code: int = 400):
    return JSONResponse({"success": False, "message": message, "data": None}, status_code=code)


# ======================================================================
# 请求模型
# ======================================================================
class CategoryCreateRequest(BaseModel):
    category_name: str = Field(..., description="分类名称")
    category_code: str = Field(..., description="全局唯一分类编码")
    parent_id: int = Field(default=0, description="父分类ID, 根节点0")
    level: Optional[int] = Field(default=None, description="层级, 不传则按父级自动推导")
    sort: int = Field(default=0, description="排序序号")
    scene_tag: List[str] = Field(default_factory=list, description="适用场景标签")
    remark: Optional[str] = Field(default=None, description="业务描述")
    status: int = Field(default=1, description="0停用 1启用")


class CategoryUpdateRequest(BaseModel):
    category_name: Optional[str] = None
    category_code: Optional[str] = None
    parent_id: Optional[int] = None
    level: Optional[int] = None
    sort: Optional[int] = None
    scene_tag: Optional[List[str]] = None
    remark: Optional[str] = None
    status: Optional[int] = None


class IndicatorCreateRequest(BaseModel):
    category_id: int = Field(..., description="归属分类ID")
    indicator_name: str = Field(..., description="指标名称")
    indicator_code: str = Field(..., description="全局唯一指标编码")
    indicator_desc: Optional[str] = Field(default=None, description="指标定义/口径/计算说明")
    data_type: int = Field(default=1, description="1定量 2定性 3布尔 4枚举")
    unit: Optional[str] = None
    standard_value: Optional[str] = None
    min_threshold: Optional[float] = None
    max_threshold: Optional[float] = None
    positive_flag: int = Field(default=1, description="1正向 0负向")
    default_score_rule_id: Optional[int] = None
    tag_list: List[str] = Field(default_factory=list)
    version: int = 1
    status: int = Field(default=1, description="0停用 1正常 2草稿")
    create_user: Optional[int] = None


class IndicatorUpdateRequest(BaseModel):
    category_id: Optional[int] = None
    indicator_name: Optional[str] = None
    indicator_code: Optional[str] = None
    indicator_desc: Optional[str] = None
    data_type: Optional[int] = None
    unit: Optional[str] = None
    standard_value: Optional[str] = None
    min_threshold: Optional[float] = None
    max_threshold: Optional[float] = None
    positive_flag: Optional[int] = None
    default_score_rule_id: Optional[int] = None
    tag_list: Optional[List[str]] = None
    version: Optional[int] = None
    status: Optional[int] = None
    create_user: Optional[int] = None


class AttachCreateRequest(BaseModel):
    indicator_id: int = Field(..., description="关联指标ID")
    file_name: str = Field(..., description="附件展示名称")
    file_url: str = Field(..., description="文件访问地址")
    attach_type: int = Field(default=1, description="1行业标准 2打分示例 3评估细则")


# ======================================================================
# 分类分级目录
# ======================================================================
@router.get("/category/tree")
async def category_tree(status: Optional[int] = Query(None)):
    """获取完整指标分类树。"""
    try:
        tree = _mgr().get_category_tree(status=status)
        return _ok({"tree": tree})
    except Exception as e:
        return _err(f"获取分类树失败: {e}")


@router.get("/category/list")
async def category_list(
    parent_id: Optional[int] = Query(None),
    status: Optional[int] = Query(None),
):
    """获取分类列表(平铺)。"""
    try:
        cats = _mgr().list_categories(parent_id=parent_id, status=status)
        return _ok({"list": [c.model_dump() for c in cats], "total": len(cats)})
    except Exception as e:
        return _err(f"获取分类列表失败: {e}")


@router.post("/category/create")
async def category_create(req: CategoryCreateRequest):
    """新增分类。"""
    try:
        cat = _mgr().create_category(
            category_name=req.category_name,
            category_code=req.category_code,
            parent_id=req.parent_id,
            level=req.level,
            sort=req.sort,
            scene_tag=req.scene_tag,
            remark=req.remark,
            status=req.status,
        )
        return _ok(cat.model_dump(), "分类创建成功")
    except ValueError as e:
        return _err(str(e))
    except Exception as e:
        return _err(f"创建分类失败: {e}")


@router.post("/category/update")
async def category_update(category_id: int = Query(...), req: CategoryUpdateRequest = None):
    """更新分类。"""
    try:
        fields = req.model_dump(exclude_none=True) if req else {}
        cat = _mgr().update_category(category_id, **fields)
        return _ok(cat.model_dump(), "分类更新成功")
    except ValueError as e:
        return _err(str(e))
    except Exception as e:
        return _err(f"更新分类失败: {e}")


@router.delete("/category/delete")
async def category_delete(category_id: int = Query(...)):
    """删除分类(存在子分类或指标时禁止)。"""
    try:
        ok = _mgr().delete_category(category_id)
        if not ok:
            return _err("分类不存在", 404)
        return _ok({"category_id": category_id}, "分类删除成功")
    except ValueError as e:
        return _err(str(e))
    except Exception as e:
        return _err(f"删除分类失败: {e}")


# ======================================================================
# 通用指标
# ======================================================================
@router.get("/list")
async def indicator_list(
    category_id: Optional[int] = Query(None),
    status: Optional[int] = Query(None),
    data_type: Optional[int] = Query(None),
    keyword: str = Query(""),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
):
    """获取指标列表(分页/过滤/检索)。"""
    try:
        result = _mgr().list_indicators(
            category_id=category_id,
            status=status,
            data_type=data_type,
            keyword=keyword or None,
            page=page,
            page_size=page_size,
        )
        result["list"] = [i.model_dump() for i in result["list"]]
        return _ok(result)
    except Exception as e:
        return _err(f"获取指标列表失败: {e}")


@router.get("/detail")
async def indicator_detail(indicator_id: int = Query(...)):
    """获取指标详情(含配套附件)。"""
    try:
        mgr = _mgr()
        indicator = mgr.get_indicator(indicator_id)
        if indicator is None:
            return _err("指标不存在", 404)
        data = indicator.model_dump()
        data["attaches"] = [a.model_dump() for a in mgr.list_attaches(indicator_id)]
        return _ok(data)
    except Exception as e:
        return _err(f"获取指标详情失败: {e}")


@router.post("/create")
async def indicator_create(req: IndicatorCreateRequest):
    """新增指标。"""
    try:
        indicator = _mgr().create_indicator(
            category_id=req.category_id,
            indicator_name=req.indicator_name,
            indicator_code=req.indicator_code,
            indicator_desc=req.indicator_desc,
            data_type=req.data_type,
            unit=req.unit,
            standard_value=req.standard_value,
            min_threshold=req.min_threshold,
            max_threshold=req.max_threshold,
            positive_flag=req.positive_flag,
            default_score_rule_id=req.default_score_rule_id,
            tag_list=req.tag_list,
            version=req.version,
            status=req.status,
            create_user=req.create_user,
        )
        return _ok(indicator.model_dump(), "指标创建成功")
    except ValueError as e:
        return _err(str(e))
    except Exception as e:
        return _err(f"创建指标失败: {e}")


@router.post("/update")
async def indicator_update(indicator_id: int = Query(...), req: IndicatorUpdateRequest = None):
    """更新指标。"""
    try:
        fields = req.model_dump(exclude_none=True) if req else {}
        indicator = _mgr().update_indicator(indicator_id, **fields)
        return _ok(indicator.model_dump(), "指标更新成功")
    except ValueError as e:
        return _err(str(e))
    except Exception as e:
        return _err(f"更新指标失败: {e}")


@router.delete("/delete")
async def indicator_delete(indicator_id: int = Query(...)):
    """删除指标(级联删除其附件)。"""
    try:
        ok = _mgr().delete_indicator(indicator_id)
        if not ok:
            return _err("指标不存在", 404)
        return _ok({"indicator_id": indicator_id}, "指标删除成功")
    except Exception as e:
        return _err(f"删除指标失败: {e}")


# ======================================================================
# 配套附件
# ======================================================================
@router.get("/attach/list")
async def attach_list(indicator_id: int = Query(...)):
    """获取指标配套附件列表。"""
    try:
        items = _mgr().list_attaches(indicator_id)
        return _ok({"list": [a.model_dump() for a in items], "total": len(items)})
    except Exception as e:
        return _err(f"获取附件列表失败: {e}")


@router.post("/attach/create")
async def attach_create(req: AttachCreateRequest):
    """新增指标配套附件。"""
    try:
        attach = _mgr().add_attach(
            indicator_id=req.indicator_id,
            file_name=req.file_name,
            file_url=req.file_url,
            attach_type=req.attach_type,
        )
        return _ok(attach.model_dump(), "附件添加成功")
    except ValueError as e:
        return _err(str(e))
    except Exception as e:
        return _err(f"添加附件失败: {e}")


@router.delete("/attach/delete")
async def attach_delete(attach_id: int = Query(...)):
    """删除指标配套附件。"""
    try:
        ok = _mgr().delete_attach(attach_id)
        if not ok:
            return _err("附件不存在", 404)
        return _ok({"attach_id": attach_id}, "附件删除成功")
    except Exception as e:
        return _err(f"删除附件失败: {e}")
