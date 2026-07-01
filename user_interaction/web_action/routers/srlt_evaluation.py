# -*- coding: utf-8 -*-
"""结果空间 · 指标评估管理路由模块

提供评估对象、计分规则、评估模板(含指标关联)、评估任务、指标填报、结果快照的 API。
路由前缀: /api/srlt/evaluation (在 main.py 注册)。

约定响应: {"success": bool, "message": str, "data": Any}
底层通过 EvaluationManager (solution_evaluation_services.evaluation_indices) 编排。
"""
import os
import sys
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from solution_evaluation_services.evaluation_indices import EvaluationManager

router = APIRouter()

_manager: Optional[EvaluationManager] = None


def _mgr() -> EvaluationManager:
    global _manager
    if _manager is None:
        _manager = EvaluationManager()
    return _manager


def _ok(data: Any = None, message: str = "ok"):
    return JSONResponse({"success": True, "message": message, "data": data})


def _err(message: str, code: int = 400):
    return JSONResponse({"success": False, "message": message, "data": None}, status_code=code)


def _page(result: Dict[str, Any], key: str = "list") -> Dict[str, Any]:
    result[key] = [x.model_dump() for x in result[key]]
    return result


# ======================================================================
# 请求模型
# ======================================================================
class ObjectCreateRequest(BaseModel):
    object_type: int = Field(..., description="关联对象类型ID")
    object_name: str = Field(..., description="对象名称")
    object_code: str = Field(..., description="业务实体编码")
    org_id: Optional[int] = None
    ext_json: Dict[str, Any] = Field(default_factory=dict)
    status: int = 1


class ObjectUpdateRequest(BaseModel):
    object_type: Optional[int] = None
    object_name: Optional[str] = None
    object_code: Optional[str] = None
    org_id: Optional[int] = None
    ext_json: Optional[Dict[str, Any]] = None
    status: Optional[int] = None


class RuleCreateRequest(BaseModel):
    rule_name: str = Field(..., description="规则名称")
    calc_type: int = Field(default=1, description="1固定分档 2线性公式 3阶梯阈值 4自定义表达式")
    rule_config_json: Dict[str, Any] = Field(default_factory=dict)
    expression: Optional[str] = None
    remark: Optional[str] = None


class RuleUpdateRequest(BaseModel):
    rule_name: Optional[str] = None
    calc_type: Optional[int] = None
    rule_config_json: Optional[Dict[str, Any]] = None
    expression: Optional[str] = None
    remark: Optional[str] = None


class TemplateCreateRequest(BaseModel):
    template_name: str = Field(..., description="模板名称")
    template_code: str = Field(..., description="全局模板编码")
    scene_type: int = Field(default=1, description="1企业绩效 2软件系统 3需求评审 4流程效能")
    template_desc: Optional[str] = None
    total_score: int = 100
    is_preset: int = 0
    version: int = 1
    status: int = 1
    create_user: Optional[int] = None


class TemplateUpdateRequest(BaseModel):
    template_name: Optional[str] = None
    template_code: Optional[str] = None
    scene_type: Optional[int] = None
    template_desc: Optional[str] = None
    total_score: Optional[int] = None
    is_preset: Optional[int] = None
    version: Optional[int] = None
    status: Optional[int] = None
    create_user: Optional[int] = None


class TemplateIndicatorItem(BaseModel):
    indicator_id: int
    weight: float = 0.0
    template_score_rule_id: Optional[int] = None
    sort: int = 0
    must_fill: int = 1


class TemplateIndicatorSetRequest(BaseModel):
    indicators: List[TemplateIndicatorItem] = Field(default_factory=list)


class TaskCreateRequest(BaseModel):
    template_id: int = Field(..., description="评估模板ID")
    object_id: int = Field(..., description="评估对象ID")
    task_name: str = Field(..., description="任务名称")
    evaluate_cycle: Optional[str] = None
    org_id: Optional[int] = None
    fill_user: Optional[int] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None


class TaskUpdateRequest(BaseModel):
    task_name: Optional[str] = None
    evaluate_cycle: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    task_status: Optional[int] = None
    fill_user: Optional[int] = None
    audit_user: Optional[int] = None
    evaluate_conclusion: Optional[str] = None


class RecordSubmitRequest(BaseModel):
    task_id: int = Field(..., description="评估任务ID")
    indicator_id: int = Field(..., description="指标ID")
    raw_value: Optional[str] = None
    score_rule_id: Optional[int] = None
    fill_remark: Optional[str] = None
    attach_ids: List[str] = Field(default_factory=list)
    auto_score: bool = True


class TaskFinishRequest(BaseModel):
    audit_user: Optional[int] = None
    evaluate_conclusion: Optional[str] = None


# ======================================================================
# 对象类型字典
# ======================================================================
@router.get("/object_type/list")
async def object_type_list():
    try:
        items = _mgr().list_object_types()
        return _ok({"list": [x.model_dump() for x in items], "total": len(items)})
    except Exception as e:
        return _err(f"获取对象类型失败: {e}")


# ======================================================================
# 评估对象
# ======================================================================
@router.get("/object/list")
async def object_list(
    object_type: Optional[int] = Query(None), org_id: Optional[int] = Query(None),
    status: Optional[int] = Query(None), keyword: str = Query(""),
    page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=100),
):
    try:
        return _ok(_page(_mgr().list_objects(object_type=object_type, org_id=org_id, status=status,
                                             keyword=keyword or None, page=page, page_size=page_size)))
    except Exception as e:
        return _err(f"获取评估对象列表失败: {e}")


@router.get("/object/detail")
async def object_detail(object_id: int = Query(...)):
    obj = _mgr().get_object(object_id)
    if obj is None:
        return _err("评估对象不存在", 404)
    return _ok(obj.model_dump())


@router.post("/object/create")
async def object_create(req: ObjectCreateRequest):
    try:
        obj = _mgr().create_object(object_type=req.object_type, object_name=req.object_name,
                                   object_code=req.object_code, org_id=req.org_id,
                                   ext_json=req.ext_json, status=req.status)
        return _ok(obj.model_dump(), "评估对象创建成功")
    except ValueError as e:
        return _err(str(e))
    except Exception as e:
        return _err(f"创建评估对象失败: {e}")


@router.post("/object/update")
async def object_update(object_id: int = Query(...), req: ObjectUpdateRequest = None):
    try:
        fields = req.model_dump(exclude_none=True) if req else {}
        return _ok(_mgr().update_object(object_id, **fields).model_dump(), "评估对象更新成功")
    except ValueError as e:
        return _err(str(e))
    except Exception as e:
        return _err(f"更新评估对象失败: {e}")


@router.delete("/object/delete")
async def object_delete(object_id: int = Query(...)):
    try:
        ok = _mgr().delete_object(object_id)
        return _ok({"object_id": object_id}, "评估对象删除成功") if ok else _err("评估对象不存在", 404)
    except ValueError as e:
        return _err(str(e))
    except Exception as e:
        return _err(f"删除评估对象失败: {e}")


# ======================================================================
# 计分规则
# ======================================================================
@router.get("/rule/list")
async def rule_list(calc_type: Optional[int] = Query(None)):
    try:
        items = _mgr().list_rules(calc_type=calc_type)
        return _ok({"list": [x.model_dump() for x in items], "total": len(items)})
    except Exception as e:
        return _err(f"获取计分规则失败: {e}")


@router.post("/rule/create")
async def rule_create(req: RuleCreateRequest):
    try:
        rule = _mgr().create_rule(rule_name=req.rule_name, calc_type=req.calc_type,
                                  rule_config_json=req.rule_config_json, expression=req.expression, remark=req.remark)
        return _ok(rule.model_dump(), "计分规则创建成功")
    except Exception as e:
        return _err(f"创建计分规则失败: {e}")


@router.post("/rule/update")
async def rule_update(rule_id: int = Query(...), req: RuleUpdateRequest = None):
    try:
        fields = req.model_dump(exclude_none=True) if req else {}
        return _ok(_mgr().update_rule(rule_id, **fields).model_dump(), "计分规则更新成功")
    except ValueError as e:
        return _err(str(e))
    except Exception as e:
        return _err(f"更新计分规则失败: {e}")


@router.delete("/rule/delete")
async def rule_delete(rule_id: int = Query(...)):
    try:
        ok = _mgr().delete_rule(rule_id)
        return _ok({"rule_id": rule_id}, "计分规则删除成功") if ok else _err("计分规则不存在", 404)
    except Exception as e:
        return _err(f"删除计分规则失败: {e}")


# ======================================================================
# 评估模板 + 指标关联
# ======================================================================
@router.get("/template/list")
async def template_list(
    scene_type: Optional[int] = Query(None), is_preset: Optional[int] = Query(None),
    status: Optional[int] = Query(None), keyword: str = Query(""),
    page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=100),
):
    try:
        return _ok(_page(_mgr().list_templates(scene_type=scene_type, is_preset=is_preset, status=status,
                                               keyword=keyword or None, page=page, page_size=page_size)))
    except Exception as e:
        return _err(f"获取模板列表失败: {e}")


@router.get("/template/detail")
async def template_detail(template_id: int = Query(...)):
    data = _mgr().get_template_detail(template_id)
    if data is None:
        return _err("评估模板不存在", 404)
    return _ok(data)


@router.post("/template/create")
async def template_create(req: TemplateCreateRequest):
    try:
        tpl = _mgr().create_template(**req.model_dump())
        return _ok(tpl.model_dump(), "评估模板创建成功")
    except ValueError as e:
        return _err(str(e))
    except Exception as e:
        return _err(f"创建评估模板失败: {e}")


@router.post("/template/update")
async def template_update(template_id: int = Query(...), req: TemplateUpdateRequest = None):
    try:
        fields = req.model_dump(exclude_none=True) if req else {}
        return _ok(_mgr().update_template(template_id, **fields).model_dump(), "评估模板更新成功")
    except ValueError as e:
        return _err(str(e))
    except Exception as e:
        return _err(f"更新评估模板失败: {e}")


@router.delete("/template/delete")
async def template_delete(template_id: int = Query(...)):
    try:
        ok = _mgr().delete_template(template_id)
        return _ok({"template_id": template_id}, "评估模板删除成功") if ok else _err("评估模板不存在", 404)
    except ValueError as e:
        return _err(str(e))
    except Exception as e:
        return _err(f"删除评估模板失败: {e}")


@router.post("/template/set_indicators")
async def template_set_indicators(template_id: int = Query(...), req: TemplateIndicatorSetRequest = None):
    try:
        indicators = [it.model_dump() for it in (req.indicators if req else [])]
        rels = _mgr().set_template_indicators(template_id, indicators)
        return _ok({"list": [r.model_dump() for r in rels], "total": len(rels)}, "模板指标已保存")
    except ValueError as e:
        return _err(str(e))
    except Exception as e:
        return _err(f"设置模板指标失败: {e}")


@router.get("/template/indicators")
async def template_indicators(template_id: int = Query(...)):
    try:
        rels = _mgr().list_template_indicators(template_id)
        return _ok({"list": [r.model_dump() for r in rels], "total": len(rels)})
    except Exception as e:
        return _err(f"获取模板指标失败: {e}")


# ======================================================================
# 评估任务
# ======================================================================
@router.get("/task/list")
async def task_list(
    template_id: Optional[int] = Query(None), object_id: Optional[int] = Query(None),
    task_status: Optional[int] = Query(None), evaluate_cycle: str = Query(""),
    org_id: Optional[int] = Query(None), keyword: str = Query(""),
    page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=100),
):
    try:
        return _ok(_page(_mgr().list_tasks(template_id=template_id, object_id=object_id, task_status=task_status,
                                           evaluate_cycle=evaluate_cycle or None, org_id=org_id,
                                           keyword=keyword or None, page=page, page_size=page_size)))
    except Exception as e:
        return _err(f"获取评估任务列表失败: {e}")


@router.get("/task/detail")
async def task_detail(task_id: int = Query(...)):
    data = _mgr().get_task_detail(task_id)
    if data is None:
        return _err("评估任务不存在", 404)
    return _ok(data)


@router.post("/task/create")
async def task_create(req: TaskCreateRequest):
    try:
        task = _mgr().create_task(**req.model_dump())
        return _ok(task.model_dump(), "评估任务创建成功")
    except ValueError as e:
        return _err(str(e))
    except Exception as e:
        return _err(f"创建评估任务失败: {e}")


@router.post("/task/update")
async def task_update(task_id: int = Query(...), req: TaskUpdateRequest = None):
    try:
        fields = req.model_dump(exclude_none=True) if req else {}
        return _ok(_mgr().update_task(task_id, **fields).model_dump(), "评估任务更新成功")
    except ValueError as e:
        return _err(str(e))
    except Exception as e:
        return _err(f"更新评估任务失败: {e}")


@router.delete("/task/delete")
async def task_delete(task_id: int = Query(...)):
    try:
        ok = _mgr().delete_task(task_id)
        return _ok({"task_id": task_id}, "评估任务删除成功") if ok else _err("评估任务不存在", 404)
    except Exception as e:
        return _err(f"删除评估任务失败: {e}")


@router.post("/task/finish")
async def task_finish(task_id: int = Query(...), req: TaskFinishRequest = None):
    try:
        result = _mgr().finish_task(task_id, audit_user=(req.audit_user if req else None),
                                    evaluate_conclusion=(req.evaluate_conclusion if req else None))
        return _ok(result, "评估已完成, 快照已生成")
    except ValueError as e:
        return _err(str(e))
    except Exception as e:
        return _err(f"完成评估失败: {e}")


# ======================================================================
# 指标填报
# ======================================================================
@router.get("/record/list")
async def record_list(task_id: int = Query(...)):
    try:
        items = _mgr().list_records(task_id)
        return _ok({"list": [x.model_dump() for x in items], "total": len(items)})
    except Exception as e:
        return _err(f"获取填报明细失败: {e}")


@router.post("/record/submit")
async def record_submit(req: RecordSubmitRequest):
    try:
        rec = _mgr().submit_record(task_id=req.task_id, indicator_id=req.indicator_id, raw_value=req.raw_value,
                                   score_rule_id=req.score_rule_id, fill_remark=req.fill_remark,
                                   attach_ids=req.attach_ids, auto_score=req.auto_score)
        return _ok(rec.model_dump(), "填报已保存")
    except ValueError as e:
        return _err(str(e))
    except Exception as e:
        return _err(f"提交填报失败: {e}")


# ======================================================================
# 结果快照
# ======================================================================
@router.get("/snapshot/detail")
async def snapshot_detail(task_id: int = Query(...)):
    snap = _mgr().get_snapshot(task_id)
    if snap is None:
        return _err("快照不存在", 404)
    return _ok(snap.model_dump())


@router.get("/snapshot/list")
async def snapshot_list(
    object_id: Optional[int] = Query(None), template_id: Optional[int] = Query(None),
    object_type: Optional[int] = Query(None), evaluate_rank: str = Query(""),
    page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=100),
):
    try:
        return _ok(_page(_mgr().list_snapshots(object_id=object_id, template_id=template_id, object_type=object_type,
                                               evaluate_rank=evaluate_rank or None, page=page, page_size=page_size)))
    except Exception as e:
        return _err(f"获取快照列表失败: {e}")
