# -*- coding: utf-8 -*-
"""系统管理路由模块

提供系统空间组织 / 人员 / 角色 / 权限（员工-角色关联） / 智能员工 的增删改查接口。
"""
import os
import sys
import json
from datetime import datetime
from typing import Optional, List, Any

from fastapi import APIRouter, Request, Query, Body, HTTPException
from fastapi.responses import JSONResponse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

router = APIRouter()


def _ok(data=None, message="ok"):
    return JSONResponse({"success": True, "message": message, "data": data})


def _err(message, code=400):
    return JSONResponse({"success": False, "message": message, "data": None}, status_code=code)


def _fmt_dt(s: Optional[str]) -> str:
    return s or ""


# ============ 组织 ============

@router.get("/organizations")
def list_organizations(
    page: int = 1,
    page_size: int = 100,
    parent_id: Optional[int] = None,
    status: Optional[str] = None,
    keyword: str = "",
):
    try:
        from data_storage_services.sql_db_services.ssys.organization_service import (
            SsysOrganizationService,
        )

        svc = SsysOrganizationService()
        
        if parent_id is not None:
            orgs = svc.list_all(
                parent_id=parent_id,
                status=status or None,
                keyword=keyword or None,
                page=page,
                page_size=page_size,
            )
            total = svc.count(
                parent_id=parent_id,
                status=status or None,
                keyword=keyword or None,
            )
        else:
            orgs = svc.list_all(
                parent_id=-1,
                status=status or None,
                keyword=keyword or None,
                page=page,
                page_size=page_size,
            )
            total = svc.count(
                parent_id=-1,
                status=status or None,
                keyword=keyword or None,
            )
        svc.disconnect()
        return _ok({
            "list": [o.model_dump() for o in orgs],
            "total": total,
            "page": page,
            "page_size": page_size,
        })
    except Exception as e:
        return _err(f"查询组织失败: {e}")


@router.get("/organizations/{oid}")
def get_organization(oid: int):
    try:
        from data_storage_services.sql_db_services.ssys.organization_service import (
            SsysOrganizationService,
        )

        svc = SsysOrganizationService()
        org = svc.get_by_id(oid)
        svc.disconnect()
        if org is None:
            return _err("组织不存在", 404)
        return _ok(org.model_dump())
    except Exception as e:
        return _err(f"查询组织失败: {e}")


@router.post("/organizations")
def add_organization(payload: dict = Body(...)):
    try:
        from bo.ssys.organization import Organization
        from data_storage_services.sql_db_services.ssys.organization_service import (
            SsysOrganizationService,
        )

        org = Organization(**payload)
        svc = SsysOrganizationService()
        saved = svc.add(org)
        svc.disconnect()
        return _ok(saved.model_dump())
    except Exception as e:
        return _err(f"新增组织失败: {e}")


@router.put("/organizations/{oid}")
def update_organization(oid: int, payload: dict = Body(...)):
    try:
        from bo.ssys.organization import Organization
        from data_storage_services.sql_db_services.ssys.organization_service import (
            SsysOrganizationService,
        )

        payload["id"] = oid
        org = Organization(**payload)
        svc = SsysOrganizationService()
        saved = svc.update(org)
        svc.disconnect()
        if saved is None:
            return _err("组织不存在", 404)
        return _ok(saved.model_dump())
    except Exception as e:
        return _err(f"更新组织失败: {e}")


@router.delete("/organizations/{oid}")
def delete_organization(oid: int, cascade: bool = True):
    try:
        from data_storage_services.sql_db_services.ssys.organization_service import (
            SsysOrganizationService,
        )

        svc = SsysOrganizationService()
        ok = svc.delete(oid, cascade=cascade)
        svc.disconnect()
        if not ok:
            return _err("组织不存在或删除失败", 404)
        return _ok({"id": oid})
    except Exception as e:
        return _err(f"删除组织失败: {e}")


# ============ 人员 ============

@router.get("/employees")
def list_employees(
    page: int = 1,
    page_size: int = 100,
    org_id: Optional[int] = None,
    status: Optional[str] = None,
    keyword: str = "",
):
    try:
        from data_storage_services.sql_db_services.ssys.employee_service import (
            SsysEmployeeService,
        )

        svc = SsysEmployeeService()
        emps = svc.list_all(
            org_id=org_id,
            status=status or None,
            keyword=keyword or None,
            page=page,
            page_size=page_size,
        )
        total = svc.count(
            org_id=org_id,
            status=status or None,
            keyword=keyword or None,
        )
        svc.disconnect()
        return _ok({
            "list": [e.model_dump() for e in emps],
            "total": total,
            "page": page,
            "page_size": page_size,
        })
    except Exception as e:
        return _err(f"查询人员失败: {e}")


@router.get("/employees/{emp_id}")
def get_employee(emp_id: int):
    try:
        from data_storage_services.sql_db_services.ssys.employee_service import (
            SsysEmployeeService,
        )

        svc = SsysEmployeeService()
        emp = svc.get_by_id(emp_id)
        svc.disconnect()
        if emp is None:
            return _err("人员不存在", 404)
        return _ok(emp.model_dump())
    except Exception as e:
        return _err(f"查询人员失败: {e}")


@router.post("/employees")
def add_employee(payload: dict = Body(...)):
    try:
        from bo.ssys.employee import Employee
        from data_storage_services.sql_db_services.ssys.employee_service import (
            SsysEmployeeService,
        )

        emp = Employee(**payload)
        svc = SsysEmployeeService()
        saved = svc.add(emp)
        svc.disconnect()
        return _ok(saved.model_dump())
    except Exception as e:
        return _err(f"新增人员失败: {e}")


@router.put("/employees/{emp_id}")
def update_employee(emp_id: int, payload: dict = Body(...)):
    try:
        from bo.ssys.employee import Employee
        from data_storage_services.sql_db_services.ssys.employee_service import (
            SsysEmployeeService,
        )

        payload["id"] = emp_id
        emp = Employee(**payload)
        svc = SsysEmployeeService()
        saved = svc.update(emp)
        svc.disconnect()
        if saved is None:
            return _err("人员不存在", 404)
        return _ok(saved.model_dump())
    except Exception as e:
        return _err(f"更新人员失败: {e}")


@router.delete("/employees/{emp_id}")
def delete_employee(emp_id: int):
    try:
        from data_storage_services.sql_db_services.ssys.employee_service import (
            SsysEmployeeService,
        )

        svc = SsysEmployeeService()
        ok = svc.delete(emp_id)
        svc.disconnect()
        if not ok:
            return _err("人员不存在或删除失败", 404)
        return _ok({"id": emp_id})
    except Exception as e:
        return _err(f"删除人员失败: {e}")


# ============ 角色 ============

@router.get("/roles")
def list_roles(
    page: int = 1,
    page_size: int = 100,
    status: Optional[str] = None,
    keyword: str = "",
):
    try:
        from data_storage_services.sql_db_services.ssys.role_service import (
            SsysRoleService,
        )

        svc = SsysRoleService()
        roles = svc.list_all(
            status=status or None,
            keyword=keyword or None,
            page=page,
            page_size=page_size,
        )
        total = svc.count(
            status=status or None,
            keyword=keyword or None,
        )
        svc.disconnect()
        return _ok({
            "list": [r.model_dump() for r in roles],
            "total": total,
            "page": page,
            "page_size": page_size,
        })
    except Exception as e:
        return _err(f"查询角色失败: {e}")


@router.post("/roles")
def add_role(payload: dict = Body(...)):
    try:
        from bo.ssys.role import Role
        from data_storage_services.sql_db_services.ssys.role_service import (
            SsysRoleService,
        )

        role = Role(**payload)
        svc = SsysRoleService()
        saved = svc.add(role)
        svc.disconnect()
        return _ok(saved.model_dump())
    except Exception as e:
        return _err(f"新增角色失败: {e}")


@router.put("/roles/{role_id}")
def update_role(role_id: int, payload: dict = Body(...)):
    try:
        from bo.ssys.role import Role
        from data_storage_services.sql_db_services.ssys.role_service import (
            SsysRoleService,
        )

        payload["id"] = role_id
        role = Role(**payload)
        svc = SsysRoleService()
        saved = svc.update(role)
        svc.disconnect()
        if saved is None:
            return _err("角色不存在", 404)
        return _ok(saved.model_dump())
    except Exception as e:
        return _err(f"更新角色失败: {e}")


@router.delete("/roles/{role_id}")
def delete_role(role_id: int):
    try:
        from data_storage_services.sql_db_services.ssys.role_service import (
            SsysRoleService,
        )

        svc = SsysRoleService()
        ok = svc.delete(role_id)
        svc.disconnect()
        if not ok:
            return _err("角色不存在或删除失败", 404)
        return _ok({"id": role_id})
    except Exception as e:
        return _err(f"删除角色失败: {e}")


# ============ 权限（员工-角色关联） ============

@router.get("/employees/{emp_id}/roles")
def get_employee_roles(emp_id: int):
    try:
        from data_storage_services.sql_db_services.ssys.employee_service import (
            SsysEmployeeService,
        )

        svc = SsysEmployeeService()
        roles = svc.list_roles(emp_id)
        svc.disconnect()
        return _ok([r.model_dump() for r in roles])
    except Exception as e:
        return _err(f"查询人员角色失败: {e}")


@router.post("/employees/{emp_id}/roles/{role_id}")
def assign_role_to_employee(emp_id: int, role_id: int):
    try:
        from data_storage_services.sql_db_services.ssys.employee_service import (
            SsysEmployeeService,
        )

        svc = SsysEmployeeService()
        ok = svc.assign_role(emp_id, role_id)
        svc.disconnect()
        return _ok({"emp_id": emp_id, "role_id": role_id, "ok": ok})
    except Exception as e:
        return _err(f"分配角色失败: {e}")


@router.delete("/employees/{emp_id}/roles/{role_id}")
def revoke_role_from_employee(emp_id: int, role_id: int):
    try:
        from data_storage_services.sql_db_services.ssys.employee_service import (
            SsysEmployeeService,
        )

        svc = SsysEmployeeService()
        ok = svc.revoke_role(emp_id, role_id)
        svc.disconnect()
        return _ok({"emp_id": emp_id, "role_id": role_id, "ok": ok})
    except Exception as e:
        return _err(f"收回角色失败: {e}")


# ============ 智能员工 ============

@router.get("/workers")
def list_workers(
    page: int = 1,
    page_size: int = 100,
    department: Optional[str] = None,
    keyword: str = "",
):
    try:
        from data_storage_services.sql_db_services.worker_service import WorkerService

        svc = WorkerService()
        where = {}
        if department:
            where["department"] = department
        all_items = svc.read_all(where=where or None)
        if keyword:
            kw = keyword.lower()
            all_items = [
                w for w in all_items
                if kw in (w.name or "").lower()
                or kw in (w.employee_id or "").lower()
                or kw in (w.department or "").lower()
            ]
        total = len(all_items)
        start = max(0, (page - 1) * page_size)
        end = start + page_size
        items = all_items[start:end]
        svc.disconnect()
        return _ok({
            "list": [
                {
                    "employee_id": w.employee_id,
                    "name": w.name,
                    "department": w.department,
                    "roles": list(w.roles or []),
                    "daily_work_hours": getattr(w, "daily_work_hours", 8.0),
                }
                for w in items
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
        })
    except Exception as e:
        return _err(f"查询智能员工失败: {e}")


@router.post("/workers")
def create_worker(payload: dict = Body(...)):
    try:
        from bo.ai_worker import AIWorker
        from data_storage_services.sql_db_services.worker_service import WorkerService

        emp_id = (payload.get("employee_id") or "").strip()
        name = (payload.get("name") or "").strip()
        if not emp_id or not name:
            return _err("employee_id 和 name 必填")

        worker = AIWorker(
            employee_id=emp_id,
            name=name,
            department=payload.get("department") or "",
            roles=list(payload.get("roles") or []),
            daily_work_hours=float(payload.get("daily_work_hours") or 8),
        )
        svc = WorkerService()
        svc.create(worker)
        svc.disconnect()
        return _ok({
            "employee_id": worker.employee_id,
            "name": worker.name,
            "department": worker.department,
            "roles": list(worker.roles),
            "daily_work_hours": worker.daily_work_hours,
        })
    except Exception as e:
        return _err(f"新增智能员工失败: {e}")


@router.put("/workers/{emp_id}")
def update_worker(emp_id: str, payload: dict = Body(...)):
    try:
        from bo.ai_worker import AIWorker
        from data_storage_services.sql_db_services.worker_service import WorkerService

        svc = WorkerService()
        existing = svc.read(emp_id)
        if existing is None:
            return _err("智能员工不存在", 404)
        updated = AIWorker(
            employee_id=emp_id,
            name=payload.get("name") or existing.name,
            department=payload.get("department") if "department" in payload else existing.department,
            roles=list(payload.get("roles") if "roles" in payload else existing.roles or []),
            daily_work_hours=float(payload.get("daily_work_hours") if "daily_work_hours" in payload else getattr(existing, "daily_work_hours", 8.0)),
        )
        svc.update(updated)
        svc.disconnect()
        return _ok({
            "employee_id": updated.employee_id,
            "name": updated.name,
            "department": updated.department,
            "roles": list(updated.roles),
            "daily_work_hours": updated.daily_work_hours,
        })
    except Exception as e:
        return _err(f"更新智能员工失败: {e}")


@router.delete("/workers/{emp_id}")
def delete_worker(emp_id: str):
    try:
        from data_storage_services.sql_db_services.worker_service import WorkerService

        svc = WorkerService()
        svc.delete(emp_id)
        svc.disconnect()
        return _ok({"employee_id": emp_id})
    except Exception as e:
        return _err(f"删除智能员工失败: {e}")
