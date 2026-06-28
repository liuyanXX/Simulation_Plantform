"""
方案拆分路由模块
提供：
- GET  /solutions              分页查询所有方案对象（下区清单数据源）
- GET  /solution/{solution_id} 查询单个方案详情（用于上区下拉的策略前置校验）
- GET  /behaviors               分页查询拆分行为历史
- GET  /behaviors/by_solution/{solution_id}  按方案查询拆分行为
- GET  /behavior/{behavior_id}  查询单个拆分行为详情（含拆分过程、结果JSON）
- POST /split                   触发拆分（auto / manual / hybrid），保存并返回 behavior_id
- POST /behavior/{behavior_id}/save  保存手动/混合拆分的调整内容
- DELETE /behavior/{behavior_id}     删除拆分行为记录
"""
from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from bo.decomposition_behavior import (
    DecompositionBehavior,
    DecompositionBehaviorStatus,
    DecompositionStrategy,
)
from bo.role import Role
from bo.organization import Organization
from bo.ai_worker import AIWorker
from bo.task import Task
from bo.task_manifest import TaskManifest
from bo.tasks_graph import TasksGraph
from bo.task_flow_group import TaskFlowGroup
from bo.solution import Solution

from data_storage_services.sql_db_services.solution_service import SolutionService
from data_storage_services.sql_db_services.decomposition_behavior_service import DecompositionBehaviorService
from data_storage_services.sql_db_services.role_service import RoleService
from data_storage_services.sql_db_services.organization_service import OrganizationService
from data_storage_services.sql_db_services.worker_service import WorkerService
from data_storage_services.sql_db_services.task_service import TaskService
from data_storage_services.sql_db_services.task_manifest_service import TaskManifestService
from data_storage_services.sql_db_services.tasks_graph_service import TasksGraphService
from data_storage_services.sql_db_services.task_flow_group_service import TaskFlowGroupService

logger = logging.getLogger("decomposition_router")

router = APIRouter(tags=["decomposition"])

NOW_FMT = "%Y-%m-%d %H:%M:%S"


def _now() -> str:
    return datetime.now().strftime(NOW_FMT)


def _ok(data: Any = None, message: str = "查询成功") -> Dict[str, Any]:
    return {"success": True, "message": message, "data": data}


def _err(message: str, code: int = 400, data: Any = None) -> Dict[str, Any]:
    return {"success": False, "message": message, "code": code, "data": data}


# ---------- Pydantic Request Models ----------

class SplitRequest(BaseModel):
    solution_id: str = Field(..., description="被拆分的方案唯一ID")
    strategy: str = Field("auto", description="拆分策略：auto / manual / hybrid")
    created_by: Optional[str] = Field(default="system")
    # 手动 / 混合拆分时前端传来的实体数据（可部分为空）
    organizations: Optional[List[Dict[str, Any]]] = Field(default=None)
    personnel: Optional[List[Dict[str, Any]]] = Field(default=None)
    roles: Optional[List[Dict[str, Any]]] = Field(default=None)
    tasks: Optional[List[Dict[str, Any]]] = Field(default=None)
    task_manifest: Optional[Dict[str, Any]] = Field(default=None)
    tasks_graph: Optional[Dict[str, Any]] = Field(default=None)
    flow_groups: Optional[List[Dict[str, Any]]] = Field(default=None)


class BehaviorSaveRequest(BaseModel):
    organizations: Optional[List[Dict[str, Any]]] = Field(default=None)
    personnel: Optional[List[Dict[str, Any]]] = Field(default=None)
    roles: Optional[List[Dict[str, Any]]] = Field(default=None)
    tasks: Optional[List[Dict[str, Any]]] = Field(default=None)
    task_manifest: Optional[Dict[str, Any]] = Field(default=None)
    tasks_graph: Optional[Dict[str, Any]] = Field(default=None)
    flow_groups: Optional[List[Dict[str, Any]]] = Field(default=None)
    status: Optional[str] = Field(default=None)
    result_summary: Optional[str] = Field(default=None)


# ---------- 内部：启发式自动拆分（无 LLM 时降级方案） ----------

def _auto_split_from_solution(solution: Solution) -> Dict[str, Any]:
    """
    从结构化方案对象中抽取内容，生成仿真组织 / 人员 / 角色 / 任务清单 / 任务图 / 任务流组 / 任务
    优先使用方案中已有的 organization / personnel / roles / work_content / initiatives 字段。
    """
    now = _now()
    sid = solution.solution_id
    name = solution.name or "未命名方案"

    org_text = solution.organization or []
    if isinstance(org_text, list):
        org_items = [str(x).strip() for x in org_text if str(x).strip()]
    else:
        org_items = [x.strip() for x in str(org_text).replace("；", ";").replace("、", ";").replace(",", ";").split(";") if x.strip()]

    role_text = solution.roles or []
    if isinstance(role_text, list):
        role_items = [str(x).strip() for x in role_text if str(x).strip()]
    else:
        role_items = [x.strip() for x in str(role_text).replace("；", ";").replace("、", ";").replace(",", ";").split(";") if x.strip()]

    person_text = solution.personnel or []
    if isinstance(person_text, list):
        person_items = [str(x).strip() for x in person_text if str(x).strip()]
    else:
        person_items = [x.strip() for x in str(person_text).replace("；", ";").replace("、", ";").replace(",", ";").split(";") if x.strip()]

    objectives = solution.objectives or []
    if isinstance(objectives, list):
        obj_items = [str(x).strip() for x in objectives if str(x).strip()]
    else:
        obj_items = [x.strip() for x in str(objectives).replace("；", ";").replace("、", ";").replace("\n", ";").split(";") if x.strip()]

    initiatives = solution.initiatives or []
    if isinstance(initiatives, list):
        init_items = [str(x).strip() for x in initiatives if str(x).strip()]
    else:
        init_items = [x.strip() for x in str(initiatives).replace("；", ";").replace("、", ";").replace("\n", ";").split(";") if x.strip()]

    work = solution.work_content or ""
    if isinstance(work, list):
        work_str = "；".join(str(x) for x in work if str(x).strip())
    else:
        work_str = str(work) if work else ""

    # ---------- 组织 ----------
    orgs: List[Dict[str, Any]] = []
    if org_items:
        for i, on in enumerate(org_items):
            oi = f"O{i+1}"
            orgs.append({"org_id": f"{sid}_org_{oi}", "name": on, "parent_id": None})
    if not orgs:
        orgs.append({"org_id": f"{sid}_org_O1", "name": f"{name}指挥机构", "parent_id": None})

    # ---------- 角色 ----------
    roles_list: List[Dict[str, Any]] = []
    if role_items:
        for i, rn in enumerate(role_items):
            roles_list.append({"name": rn, "description": f"来自方案《{name}》自动拆分"})
    if not roles_list:
        roles_list.append({"name": "指挥员", "description": "指挥决策角色"})
        roles_list.append({"name": "参谋", "description": "方案执行参谋"})
        roles_list.append({"name": "执行人员", "description": "任务执行人员"})

    # ---------- 人员 ----------
    personnel: List[Dict[str, Any]] = []
    if person_items:
        for i, pn in enumerate(person_items):
            role = roles_list[i % len(roles_list)]["name"] if roles_list else "执行人员"
            org = orgs[i % len(orgs)]["org_id"]
            personnel.append({
                "employee_id": f"{sid}_w_{i+1}",
                "name": pn,
                "department": pn,
                "roles": role,
                "daily_work_hours": 8,
                "org_id": org,
            })
    if not personnel:
        for i, r in enumerate(roles_list):
            org = orgs[i % len(orgs)]["org_id"]
            personnel.append({
                "employee_id": f"{sid}_w_{i+1}",
                "name": f"{r['name']}_{i+1}",
                "department": orgs[0]["name"] if orgs else "总体",
                "roles": r["name"],
                "daily_work_hours": 8,
                "org_id": org,
            })

    # ---------- 任务 ----------
    tasks: List[Dict[str, Any]] = []
    task_bullets: List[str] = []
    for items_src in [init_items, obj_items]:
        for line in items_src:
            line = line.strip(" \t-*·")
            if line and len(line) >= 2:
                task_bullets.append(line)
        if len(task_bullets) >= 6:
            break
    # 再从 work_str 切
    if len(task_bullets) < 6 and work_str:
        for line in work_str.replace("；", "\n").replace(";", "\n").split("\n"):
            line = line.strip(" \t-*·")
            if line and len(line) >= 2:
                task_bullets.append(line)
            if len(task_bullets) >= 10:
                break

    if not task_bullets:
        task_bullets = ["方案理解", "任务分解", "组织协调", "执行实施", "效果评估", "总结复盘"]

    tasks_per_flow = max(1, (len(task_bullets) + 2) // 3)
    flow_names = ["准备阶段", "执行阶段", "收尾阶段"]
    flow_groups: List[Dict[str, Any]] = []
    fg_tasks_map: Dict[str, List[str]] = {}
    graph_edges: List[Dict[str, str]] = []

    task_id_list: List[str] = []
    for i, bullet in enumerate(task_bullets):
        tid = f"{sid}_t_{i+1:02d}"
        flow_idx = min(len(flow_names) - 1, i // tasks_per_flow)
        flow_name = flow_names[flow_idx]
        flow_id = f"{sid}_fg_{flow_idx+1}"
        if flow_id not in fg_tasks_map:
            fg_tasks_map[flow_id] = []
            flow_groups.append({
                "flow_id": flow_id,
                "flow_name": flow_name,
                "manifest_id": f"{sid}_mf",
                "description": f"拆分自《{name}》方案",
                "created_at": now,
                "updated_at": now,
            })
        fg_tasks_map[flow_id].append(tid)
        # 串行图边
        if task_id_list:
            graph_edges.append({"from": task_id_list[-1], "to": tid})
        task_id_list.append(tid)

        role = roles_list[i % len(roles_list)]["name"] if roles_list else "执行人员"
        priority = ["high", "medium", "low"][i % 3]
        tasks.append({
            "task_id": tid,
            "task_name": bullet[:80],
            "expected_start_time": f"T+{i*2}h",
            "expected_end_time": f"T+{(i+1)*2}h",
            "content": bullet,
            "execute_role": role,
            "resource_consumption": "CPU/人工",
            "priority": priority,
            "output_target_role": "",
            "next_task_info": "",
            "task_type": "normal",
            "flow_group_id": flow_id,
            "graph_id": f"{sid}_gph",
            "manifest_id": f"{sid}_mf",
        })

    manifest = {
        "manifest_id": f"{sid}_mf",
        "manifest_name": f"{name} - 任务清单",
        "description": f"自动拆分自方案《{name}》",
        "status": "completed",
        "created_at": now,
        "updated_at": now,
    }

    tasks_graph = {
        "graph_id": f"{sid}_gph",
        "graph_name": f"{name} - 任务图谱",
        "description": f"包含 {len(tasks)} 个任务，{len(graph_edges)} 条依赖边",
        "edges": graph_edges,
    }

    return {
        "organizations": orgs,
        "personnel": personnel,
        "roles": roles_list,
        "tasks": tasks,
        "task_manifest": manifest,
        "tasks_graph": tasks_graph,
        "flow_groups": flow_groups,
        "process_log": [f"[{now}] 启发式自动拆分完成：方案《{name}》 生成 {len(orgs)} 组织 / {len(roles_list)} 角色 / {len(personnel)} 人员 / {len(tasks)} 任务 / {len(flow_groups)} 流组"],
        "result_summary": f"自动拆分：{len(orgs)} 组织, {len(roles_list)} 角色, {len(personnel)} 人员, {len(tasks)} 任务, {len(flow_groups)} 流组",
    }


# ---------- 内部：实体持久化 ----------

def _coerce_worker_roles(raw) -> List[str]:
    if isinstance(raw, list):
        return [str(x) for x in raw if str(x).strip()]
    if isinstance(raw, str) and raw.strip():
        parts = [p.strip() for p in raw.replace("；", ",").replace(";", ",").split(",")]
        return [p for p in parts if p]
    return []


def _coerce_resource_consumption(raw) -> float:
    if isinstance(raw, (int, float)):
        return float(raw)
    if isinstance(raw, str) and raw.strip():
        digits = [c for c in raw if c.isdigit() or c == "."]
        if digits:
            try:
                return float("".join(digits))
            except Exception:
                pass
    return 1.0


def _coerce_task_time(raw, fallback_now: str):
    if isinstance(raw, str):
        try:
            return datetime.strptime(raw, "%Y-%m-%d %H:%M:%S")
        except Exception:
            pass
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00").replace(" ", "T"))
        except Exception:
            pass
    try:
        return datetime.strptime(fallback_now, "%Y-%m-%d %H:%M:%S")
    except Exception:
        return datetime.now()


def _persist_entities(result: Dict[str, Any], solution_id: str) -> None:
    now = _now()

    try:
        svc = OrganizationService()
        for o in result.get("organizations") or []:
            try:
                org = Organization(
                    org_id=o.get("org_id") or f"{solution_id}_org_{uuid.uuid4().hex[:6]}",
                    name=o.get("name", "未命名组织"),
                    parent=o.get("parent"),
                    children=[],
                    workers=[],
                    created_at=o.get("created_at") or now,
                    updated_at=now,
                )
                svc.create(org)
            except Exception:
                org = Organization(
                    org_id=o.get("org_id") or f"{solution_id}_org_{uuid.uuid4().hex[:6]}",
                    name=o.get("name", "未命名组织"),
                    parent=o.get("parent"),
                    children=[],
                    workers=[],
                    created_at=o.get("created_at") or now,
                    updated_at=now,
                )
                svc.update(org)
        svc.disconnect()
    except Exception as e:
        logger.warning("保存组织失败: %s", e)

    try:
        svc = RoleService()
        for r in result.get("roles") or []:
            try:
                role = Role(name=r.get("name", "未命名角色"), description=r.get("description", ""))
                svc.create(role)
            except Exception:
                pass
        svc.disconnect()
    except Exception as e:
        logger.warning("保存角色失败: %s", e)

    try:
        svc = WorkerService()
        for w in result.get("personnel") or []:
            try:
                worker = AIWorker(
                    employee_id=w.get("employee_id") or f"{solution_id}_w_{uuid.uuid4().hex[:6]}",
                    name=w.get("name", "未命名人员"),
                    department=w.get("department", ""),
                    roles=_coerce_worker_roles(w.get("roles")),
                    daily_work_hours=int(w.get("daily_work_hours") or 8),
                    org_id=w.get("org_id", ""),
                    created_at=now,
                    updated_at=now,
                )
                svc.create(worker)
            except Exception:
                worker = AIWorker(
                    employee_id=w.get("employee_id") or f"{solution_id}_w_{uuid.uuid4().hex[:6]}",
                    name=w.get("name", "未命名人员"),
                    department=w.get("department", ""),
                    roles=_coerce_worker_roles(w.get("roles")),
                    daily_work_hours=int(w.get("daily_work_hours") or 8),
                    org_id=w.get("org_id", ""),
                    created_at=now,
                    updated_at=now,
                )
                svc.update(worker)
        svc.disconnect()
    except Exception as e:
        logger.warning("保存人员失败: %s", e)

    mf = result.get("task_manifest") or {}
    if mf:
        try:
            svc = TaskManifestService()
            fm_items = []
            for fg in result.get("flow_groups") or []:
                from bo.task_flow_group import TaskFlowGroup as _Tfg
                try:
                    fm_items.append(_Tfg(**{
                        "flow_id": fg.get("flow_id") or f"{solution_id}_fg_{uuid.uuid4().hex[:6]}",
                        "flow_name": fg.get("flow_name", "未命名流组"),
                        "tasks": [],
                        "description": fg.get("description", ""),
                    }))
                except Exception:
                    pass
            tm = TaskManifest(
                manifest_id=mf.get("manifest_id") or f"{solution_id}_mf",
                manifest_name=mf.get("manifest_name", f"{solution_id}任务清单"),
                flow_groups=fm_items,
                description=mf.get("description", ""),
                status=mf.get("status", "completed"),
                created_at=now,
                updated_at=now,
            )
            try:
                svc.create(tm)
            except Exception:
                svc.update(tm)
            svc.disconnect()
        except Exception as e:
            logger.warning("保存任务清单失败: %s", e)

    gph = result.get("tasks_graph") or {}
    if gph:
        try:
            svc = TasksGraphService()
            from bo.task_flow_group import TaskFlowGroup as _Tfg  # noqa
            try:
                _dummy_task = Task(
                    task_id="__dummy__", task_name="__dummy__",
                    expected_start_time=_coerce_task_time(now, now),
                    expected_end_time=_coerce_task_time(now, now),
                    content="", execute_role="", resource_consumption=0.0, priority="medium",
                    output_target_role="",
                    next_task_info=None,
                    task_destinations=[],
                    task_type="normal",
                )
            except Exception:
                _dummy_task = None
            tasks_for_graph = []
            for t in result.get("tasks") or []:
                try:
                    tasks_for_graph.append(Task(
                        task_id=t.get("task_id") or f"{solution_id}_t_{uuid.uuid4().hex[:6]}",
                        task_name=t.get("task_name", "未命名任务"),
                        expected_start_time=_coerce_task_time(t.get("expected_start_time"), now),
                        expected_end_time=_coerce_task_time(t.get("expected_end_time"), now),
                        content=t.get("content", ""),
                        execute_role=t.get("execute_role", ""),
                        resource_consumption=_coerce_resource_consumption(t.get("resource_consumption")),
                        priority=t.get("priority", "medium"),
                        output_target_role=t.get("output_target_role", ""),
                        next_task_info=None,
                        task_destinations=[],
                        task_type=t.get("task_type", "normal"),
                    ))
                except Exception:
                    pass
            tg = TasksGraph(
                graph_id=gph.get("graph_id") or f"{solution_id}_gph",
                graph_name=gph.get("graph_name", f"{solution_id}任务图谱"),
                tasks=tasks_for_graph,
                description=gph.get("description", ""),
            )
            try:
                svc.create(tg)
            except Exception:
                svc.update(tg)
            svc.disconnect()
        except Exception as e:
            logger.warning("保存任务图谱失败: %s", e)

    try:
        svc = TaskFlowGroupService()
        for fg in result.get("flow_groups") or []:
            try:
                tfg = TaskFlowGroup(
                    flow_id=fg.get("flow_id") or f"{solution_id}_fg_{uuid.uuid4().hex[:6]}",
                    flow_name=fg.get("flow_name", "未命名流组"),
                    tasks=[],
                    description=fg.get("description", ""),
                )
                try:
                    svc.create(tfg)
                except Exception:
                    svc.update(tfg)
            except Exception as e2:
                logger.warning("保存单个流组失败: %s", e2)
        svc.disconnect()
    except Exception as e:
        logger.warning("保存任务流组失败: %s", e)

    try:
        svc = TaskService()
        for t in result.get("tasks") or []:
            try:
                task = Task(
                    task_id=t.get("task_id") or f"{solution_id}_t_{uuid.uuid4().hex[:6]}",
                    task_name=t.get("task_name", "未命名任务"),
                    expected_start_time=_coerce_task_time(t.get("expected_start_time"), now),
                    expected_end_time=_coerce_task_time(t.get("expected_end_time"), now),
                    scheduled_start_time=None,
                    scheduled_end_time=None,
                    actual_start_time=None,
                    actual_end_time=None,
                    content=t.get("content", ""),
                    execute_role=t.get("execute_role", ""),
                    resource_consumption=_coerce_resource_consumption(t.get("resource_consumption")),
                    priority=t.get("priority", "medium"),
                    output_target_role=t.get("output_target_role", ""),
                    next_task_info=None,
                    task_destinations=[],
                    task_type=t.get("task_type", "normal"),
                )
                try:
                    svc.create(task)
                except Exception:
                    svc.update(task)
            except Exception as te:
                logger.warning("保存单个任务失败: %s", te)
        svc.disconnect()
    except Exception as e:
        logger.warning("保存任务失败: %s", e)


# ---------- 对外：HTTP ----------

@router.get("/solutions")
def list_solutions(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页条数"),
    keyword: Optional[str] = Query(None, description="关键字（名称/描述）"),
):
    """分页查询方案清单 —— 用于上区下拉 + 下区方案清单"""
    svc = SolutionService()
    try:
        where: Dict[str, Any] = {}
        all_items = svc.read_all(where=where)
        items = []
        for s in all_items:
            d = {
                "solution_id": s.solution_id,
                "name": s.name,
                "version": getattr(s, "version", None),
                "status": getattr(s, "status", None),
                "priority": getattr(s, "priority", None),
                "purpose": (getattr(s, "purpose", "") or "")[:120],
                "description": (getattr(s, "description", "") or "")[:120],
                "created_at": getattr(s, "created_at", None),
                "updated_at": getattr(s, "updated_at", None),
            }
            if keyword:
                k = keyword.lower()
                if k not in (d["name"] or "").lower() and k not in (d["description"] or "").lower() and k not in (d["purpose"] or "").lower():
                    continue
            items.append(d)

        total = len(items)
        start = (page - 1) * page_size
        end = start + page_size
        page_items = items[start:end]
        return _ok({"list": page_items, "total": total, "page": page, "page_size": page_size})
    finally:
        svc.disconnect()


@router.get("/solution/{solution_id}")
def get_solution(solution_id: str):
    svc = SolutionService()
    try:
        s = svc.read(solution_id)
        if not s:
            return _err(f"方案不存在: {solution_id}", 404)
        return _ok(s.model_dump())
    finally:
        svc.disconnect()


@router.get("/behaviors")
def list_behaviors(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    strategy: Optional[str] = Query(None, description="按策略筛选 auto/manual/hybrid"),
):
    svc = DecompositionBehaviorService()
    try:
        items = svc.read_all()
        items.sort(key=lambda x: x.updated_at or x.created_at or "", reverse=True)
        out = []
        for b in items:
            if strategy and b.strategy.value != strategy:
                continue
            out.append({
                "behavior_id": b.behavior_id,
                "solution_id": b.solution_id,
                "solution_name": b.solution_name,
                "strategy": b.strategy.value,
                "status": b.status.value,
                "task_manifest_id": b.task_manifest_id,
                "tasks_graph_id": b.tasks_graph_id,
                "result_summary": b.result_summary,
                "created_by": b.created_by,
                "created_at": b.created_at,
                "updated_at": b.updated_at,
            })
        total = len(out)
        start = (page - 1) * page_size
        return _ok({"list": out[start:start+page_size], "total": total, "page": page, "page_size": page_size})
    finally:
        svc.disconnect()


@router.get("/behaviors/by_solution/{solution_id}")
def list_behaviors_by_solution(solution_id: str):
    svc = DecompositionBehaviorService()
    try:
        items = svc.list_by_solution(solution_id)
        items.sort(key=lambda x: x.updated_at or x.created_at or "", reverse=True)
        return _ok([b.model_dump() for b in items])
    finally:
        svc.disconnect()


@router.get("/behavior/{behavior_id}")
def get_behavior(behavior_id: str):
    svc = DecompositionBehaviorService()
    try:
        b = svc.read(behavior_id)
        if not b:
            return _err(f"拆分行为不存在: {behavior_id}", 404)
        d = b.model_dump()
        # 给 process_log 一个视图友好的列表
        proc = d.get("process_log")
        if isinstance(proc, str):
            try:
                d["process_log_list"] = json.loads(proc)
            except Exception:
                d["process_log_list"] = [proc]
        elif isinstance(proc, list):
            d["process_log_list"] = proc
        else:
            d["process_log_list"] = []
        # organizations / personnel / roles / tasks / flow_groups / task_manifest / tasks_graph 给前端也展开为 list/dict
        for k in ["organizations", "personnel", "roles", "tasks", "flow_groups"]:
            v = d.get(k)
            if isinstance(v, str):
                try:
                    d[k] = json.loads(v)
                except Exception:
                    d[k] = []
        for k in ["task_manifest", "tasks_graph"]:
            v = d.get(k)
            if isinstance(v, str):
                try:
                    d[k] = json.loads(v)
                except Exception:
                    d[k] = {}
        return _ok(d)
    finally:
        svc.disconnect()


@router.post("/split")
def split(req: SplitRequest):
    """触发一次拆分，返回拆分行为ID及拆分结果 JSON"""
    strategy = (req.strategy or "auto").lower()
    if strategy not in ("auto", "manual", "hybrid"):
        return _err(f"未知拆分策略: {req.strategy}", 400)

    # 1. 读取方案
    sol_svc = SolutionService()
    try:
        solution = sol_svc.read(req.solution_id)
    finally:
        sol_svc.disconnect()
    if not solution:
        return _err(f"方案不存在: {req.solution_id}", 404)

    result: Dict[str, Any] = {}
    process_log: List[str] = []
    now = _now()
    strategy_label = {"auto": "自动拆分", "manual": "手动拆分", "hybrid": "混合拆分"}[strategy]
    process_log.append(f"[{now}] 开始执行《{solution.name}》的{strategy_label}")

    if strategy == "auto":
        try:
            result = _auto_split_from_solution(solution)
            process_log.extend(result.get("process_log") or [])
            result_summary = result.get("result_summary") or "自动拆分完成"
        except Exception as e:
            logger.exception("自动拆分失败")
            process_log.append(f"[{_now()}] 自动拆分失败：{e}")
            return _err(f"自动拆分失败: {e}", 500)

    elif strategy == "manual":
        if not (req.organizations or req.personnel or req.roles or req.tasks):
            return _err("手动拆分请至少录入一项内容（组织/角色/人员/任务）", 400)
        result = {
            "organizations": req.organizations or [],
            "personnel": req.personnel or [],
            "roles": req.roles or [],
            "tasks": req.tasks or [],
            "task_manifest": req.task_manifest or {"manifest_id": f"{req.solution_id}_mf", "manifest_name": f"{solution.name}任务清单", "created_at": now, "updated_at": now},
            "tasks_graph": req.tasks_graph or {"graph_id": f"{req.solution_id}_gph", "graph_name": f"{solution.name}任务图谱"},
            "flow_groups": req.flow_groups or [],
            "process_log": [f"[{_now()}] 手动拆分：由用户录入上述对象"],
            "result_summary": f"手动拆分：组织 {len(req.organizations or [])} / 角色 {len(req.roles or [])} / 人员 {len(req.personnel or [])} / 任务 {len(req.tasks or [])} / 流组 {len(req.flow_groups or [])}",
        }

    elif strategy == "hybrid":
        auto_result = _auto_split_from_solution(solution)
        merged_process = [f"[{_now()}] 混合拆分：先自动拆分"]
        merged_process.extend(auto_result.get("process_log") or [])

        def _merge_list(auto_list: List[Dict], manual_list: Optional[List[Dict]], key_field: str) -> List[Dict]:
            out: List[Dict] = []
            seen: set = set()
            if manual_list:
                for m in manual_list:
                    out.append(dict(m))
                    k = m.get(key_field)
                    if k:
                        seen.add(k)
            for a in auto_list or []:
                k = a.get(key_field)
                if k and k not in seen:
                    out.append(dict(a))
                    seen.add(k)
                elif not k:
                    out.append(dict(a))
            return out

        merged_orgs = _merge_list(auto_result.get("organizations", []), req.organizations, "org_id")
        merged_personnel = _merge_list(auto_result.get("personnel", []), req.personnel, "employee_id")
        merged_roles = _merge_list(auto_result.get("roles", []), req.roles, "name")
        merged_tasks = _merge_list(auto_result.get("tasks", []), req.tasks, "task_id")
        merged_flow = _merge_list(auto_result.get("flow_groups", []), req.flow_groups, "flow_id")
        merged_mf = dict(auto_result.get("task_manifest") or {})
        if req.task_manifest:
            merged_mf.update(req.task_manifest)
        merged_gph = dict(auto_result.get("tasks_graph") or {})
        if req.tasks_graph:
            merged_gph.update(req.tasks_graph)
        merged_process.append(f"[{_now()}] 混合拆分：合并用户调整后的内容（组织 {len(merged_orgs)}，角色 {len(merged_roles)}，人员 {len(merged_personnel)}，任务 {len(merged_tasks)}，流组 {len(merged_flow)}）")
        result = {
            "organizations": merged_orgs,
            "personnel": merged_personnel,
            "roles": merged_roles,
            "tasks": merged_tasks,
            "task_manifest": merged_mf,
            "tasks_graph": merged_gph,
            "flow_groups": merged_flow,
            "process_log": merged_process,
            "result_summary": f"混合拆分：组织 {len(merged_orgs)} / 角色 {len(merged_roles)} / 人员 {len(merged_personnel)} / 任务 {len(merged_tasks)} / 流组 {len(merged_flow)}",
        }

    # 2. 级联保存实体
    try:
        _persist_entities(result, req.solution_id)
    except Exception as e:
        logger.warning("实体级联保存异常（继续保存拆分行为）: %s", e)
        process_log.append(f"[{_now()}] 实体级联保存异常：{e}（拆分行为仍已记录）")

    # 3. 保存拆分行为
    try:
        behavior_id = f"bh_{uuid.uuid4().hex[:10]}"
        b = DecompositionBehavior(
            behavior_id=behavior_id,
            solution_id=req.solution_id,
            solution_name=solution.name,
            strategy=DecompositionStrategy(strategy),
            status=DecompositionBehaviorStatus.COMPLETED,
            organizations=result.get("organizations"),
            personnel=result.get("personnel"),
            roles=result.get("roles"),
            task_manifest_id=(result.get("task_manifest") or {}).get("manifest_id") if result.get("task_manifest") else None,
            tasks_graph_id=(result.get("tasks_graph") or {}).get("graph_id") if result.get("tasks_graph") else None,
            flow_groups=result.get("flow_groups"),
            tasks=result.get("tasks"),
            process_log="\n".join(process_log),
            result_summary=result.get("result_summary"),
            created_by=req.created_by or "system",
            created_at=now,
            updated_at=now,
        )
        bsvc = DecompositionBehaviorService()
        try:
            bsvc.create(b)
        finally:
            bsvc.disconnect()
    except Exception as e:
        logger.exception("保存拆分行为失败")
        return _err(f"保存拆分行为失败: {e}", 500)

    return _ok({"behavior_id": behavior_id, "result": result}, message=f"{strategy_label}完成")


@router.post("/behavior/{behavior_id}/save")
def save_behavior_manual(behavior_id: str, req: BehaviorSaveRequest):
    """保存手动/混合拆分的调整内容 —— 更新拆分行为本身 + 重新级联实体表"""
    bsvc = DecompositionBehaviorService()
    try:
        b = bsvc.read(behavior_id)
    finally:
        bsvc.disconnect()
    if not b:
        return _err(f"拆分行为不存在: {behavior_id}", 404)

    now = _now()
    # 更新行为本身
    new_orgs = req.organizations if req.organizations is not None else b.organizations
    new_personnel = req.personnel if req.personnel is not None else b.personnel
    new_roles = req.roles if req.roles is not None else b.roles
    new_tasks = req.tasks if req.tasks is not None else b.tasks
    new_flow = req.flow_groups if req.flow_groups is not None else b.flow_groups
    new_mf = req.task_manifest if req.task_manifest is not None else (
        json.loads(b.task_manifest) if isinstance(b.task_manifest, str) else b.task_manifest
    )
    new_gph = req.tasks_graph if req.tasks_graph is not None else (
        json.loads(b.tasks_graph) if isinstance(b.tasks_graph, str) else b.tasks_graph
    )

    # 追加一条保存动作日志
    proc = b.process_log if isinstance(b.process_log, list) else (
        json.loads(b.process_log) if isinstance(b.process_log, str) else []
    )
    proc.append(f"[{now}] 用户保存手动/混合拆分调整")

    if isinstance(proc, list) and isinstance(b.process_log, str):
        proc_str = json.dumps(proc, ensure_ascii=False)
    elif isinstance(proc, list):
        proc_str = json.dumps(proc, ensure_ascii=False)
    else:
        proc_str = str(proc)

    # DecompositionBehavior 对象不接受直接 process_log list 转 str，我们这里构造 dict 再 update 更灵活
    try:
        b2 = DecompositionBehavior(
            behavior_id=b.behavior_id,
            solution_id=b.solution_id,
            solution_name=b.solution_name,
            strategy=b.strategy,
            status=b.status,
            organizations=new_orgs,
            personnel=new_personnel,
            roles=new_roles,
            task_manifest_id=(new_mf or {}).get("manifest_id") if new_mf else b.task_manifest_id,
            tasks_graph_id=(new_gph or {}).get("graph_id") if new_gph else b.tasks_graph_id,
            flow_groups=new_flow,
            tasks=new_tasks,
            process_log=proc,
            result_summary=req.result_summary or b.result_summary,
            created_by=b.created_by,
            created_at=b.created_at,
            updated_at=now,
        )
        bsvc = DecompositionBehaviorService()
        try:
            bsvc.update(b2)
        finally:
            bsvc.disconnect()
    except Exception as e:
        logger.exception("更新拆分行为失败")
        return _err(f"更新拆分行为失败: {e}", 500)

    # 再次级联保存实体
    _persist_entities({
        "organizations": new_orgs,
        "personnel": new_personnel,
        "roles": new_roles,
        "tasks": new_tasks,
        "task_manifest": new_mf,
        "tasks_graph": new_gph,
        "flow_groups": new_flow,
    }, b.solution_id)

    return _ok({"behavior_id": behavior_id}, message="拆分调整已保存")


@router.delete("/behavior/{behavior_id}")
def delete_behavior(behavior_id: str):
    bsvc = DecompositionBehaviorService()
    try:
        b = bsvc.read(behavior_id)
        if not b:
            return _err(f"拆分行为不存在: {behavior_id}", 404)
        bsvc.delete(behavior_id)
    finally:
        bsvc.disconnect()
    return _ok({"behavior_id": behavior_id}, message="已删除拆分行为")
