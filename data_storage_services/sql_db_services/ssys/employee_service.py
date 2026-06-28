"""系统空间 · 人员对象持久化服务 (SsysEmployeeService)

直接通过 SQLiteOperator 对 ssys_employee 表做增、删、改、查。
查找支持:
  - 按ID查本身           get_by_id(emp_id)
  - 按员工编码查本身      get_by_code(emp_code)
  - 按名称模糊查          search_by_name(keyword)
  - 按归属组织查          list_by_org(org_id, include_subtree)
  - 查全量                list_all(...)
  - 统计                  count(...)

员工-角色关联 (M:N):
  - assign_role / revoke_role / list_roles / list_role_ids / has_role / employees_with_role
"""
from __future__ import annotations
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from data_storage_services.SQLite.sqlite_operator import SQLiteOperator
from data_storage_services.sql_db_services.ssys.organization_service import (
    SsysOrganizationService,
)
from bo.ssys.employee import Employee


logger = logging.getLogger("SsysEmployeeService")


def _now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


class SsysEmployeeService:
    """系统空间 · Employee 持久化服务。"""

    TABLE = "ssys_employee"

    def __init__(
        self,
        db_path: Optional[str] = None,
        db_name: Optional[str] = None,
        operator: Optional[SQLiteOperator] = None,
    ) -> None:
        if operator is not None:
            self._op = operator
        else:
            if db_path is None:
                db_path = "DB/SQLite"
            if db_name is None:
                db_name = "simulation.db"
            self._op = SQLiteOperator(db_path=db_path, db_name=db_name)
            self._op.connect()
        self._org_svc = None

    def __enter__(self) -> "SsysEmployeeService":
        return self

    def __exit__(self, *args: Any) -> None:
        self.disconnect()

    def disconnect(self) -> None:
        try:
            self._op.disconnect()
        except Exception:
            pass

    @property
    def cursor(self):
        return self._op.cursor

    @property
    def connection(self):
        return self._op.connection

    # ---------- 基础 CRUD ----------
    def add(self, emp: Employee) -> Employee:
        if not emp.created_at:
            emp.created_at = _now_iso()
        emp.updated_at = _now_iso()
        emp_dict = emp.model_dump()
        emp_dict.pop("id", None)
        columns = ", ".join(emp_dict.keys())
        placeholders = ", ".join(["?"] * len(emp_dict))
        self._op.cursor.execute(
            f"INSERT INTO {self.TABLE} ({columns}) VALUES ({placeholders})",
            list(emp_dict.values()),
        )
        self._op.connection.commit()
        emp.id = self._op.cursor.lastrowid
        return self.get_by_id(emp.id)

    def get_by_id(self, emp_id: int) -> Optional[Employee]:
        self._op.cursor.execute(
            f"SELECT * FROM {self.TABLE} WHERE id = ?", [int(emp_id)]
        )
        row = self._op.cursor.fetchone()
        return self._from_row(dict(row)) if row else None

    def get_by_code(self, emp_code: str) -> Optional[Employee]:
        self._op.cursor.execute(
            f"SELECT * FROM {self.TABLE} WHERE emp_code = ?", [emp_code]
        )
        row = self._op.cursor.fetchone()
        return self._from_row(dict(row)) if row else None

    def update(self, emp: Employee) -> Optional[Employee]:
        if emp.id is None:
            return None
        emp.updated_at = _now_iso()
        fields: List[str] = []
        values: List[Any] = []
        for k, v in emp.model_dump().items():
            if k == "id":
                continue
            fields.append(f"{k} = ?")
            values.append(v)
        values.append(emp.id)
        self._op.cursor.execute(
            f"UPDATE {self.TABLE} SET {', '.join(fields)} WHERE id = ?",
            values,
        )
        self._op.connection.commit()
        return self.get_by_id(emp.id)

    def delete(self, emp_id: int) -> bool:
        self._op.cursor.execute(
            f"DELETE FROM {self.TABLE} WHERE id = ?", [int(emp_id)]
        )
        self._op.connection.commit()
        return self._op.cursor.rowcount > 0

    # ---------- 查找 ----------
    def list_all(
        self,
        status: Optional[str] = None,
        org_id: Optional[int] = None,
        keyword: Optional[str] = None,
        page: int = 1,
        page_size: int = 100,
    ) -> List[Employee]:
        clauses: List[str] = []
        params: List[Any] = []
        if status:
            clauses.append("status = ?")
            params.append(status)
        if org_id is not None:
            clauses.append("org_id = ?")
            params.append(int(org_id))
        if keyword:
            clauses.append("(emp_name LIKE ? OR emp_code LIKE ? OR position LIKE ?)")
            params += [f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"]
        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        offset = max(0, (page - 1)) * page_size
        self._op.cursor.execute(
            f"SELECT * FROM {self.TABLE} {where} "
            f"ORDER BY id ASC LIMIT ? OFFSET ?",
            params + [page_size, offset],
        )
        return [self._from_row(dict(r)) for r in self._op.cursor.fetchall()]

    def search_by_name(self, keyword: str) -> List[Employee]:
        return self.list_all(keyword=keyword)

    def list_by_org(
        self,
        org_id: int,
        include_subtree: bool = False,
    ) -> List[Employee]:
        org_ids: List[int] = [int(org_id)]
        if include_subtree:
            if self._org_svc is None:
                self._org_svc = SsysOrganizationService(operator=self._op)
            tree = self._org_svc.build_organization_tree(int(org_id))
            if tree is not None:
                collected: List[int] = []

                def _walk(node) -> None:
                    collected.append(int(node.id))
                    for ch in node.children:
                        _walk(ch)

                _walk(tree)
                org_ids = collected
        if len(org_ids) == 1:
            return self.list_all(org_id=org_ids[0])
        placeholders = ",".join(["?"] * len(org_ids))
        self._op.cursor.execute(
            f"SELECT * FROM {self.TABLE} WHERE org_id IN ({placeholders}) "
            f"ORDER BY org_id ASC, id ASC",
            org_ids,
        )
        return [self._from_row(dict(r)) for r in self._op.cursor.fetchall()]

    def count(
        self,
        status: Optional[str] = None,
        org_id: Optional[int] = None,
        keyword: Optional[str] = None,
    ) -> int:
        clauses: List[str] = []
        params: List[Any] = []
        if status:
            clauses.append("status = ?")
            params.append(status)
        if org_id is not None:
            clauses.append("org_id = ?")
            params.append(int(org_id))
        if keyword:
            clauses.append("(emp_name LIKE ? OR emp_code LIKE ? OR position LIKE ?)")
            params += [f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"]
        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        self._op.cursor.execute(
            f"SELECT COUNT(*) AS cnt FROM {self.TABLE} {where}", params
        )
        row = self._op.cursor.fetchone()
        return int(dict(row)["cnt"]) if row else 0

    # ---------- 员工-角色关联 (M:N) ----------
    def assign_role(self, emp_id: int, role_id: int) -> bool:
        self._op.cursor.execute(
            "INSERT OR IGNORE INTO ssys_employee_role (emp_id, role_id, assigned_at) "
            "VALUES (?, ?, ?)",
            [int(emp_id), int(role_id), _now_iso()],
        )
        self._op.connection.commit()
        return self.has_role(emp_id, role_id)

    def revoke_role(self, emp_id: int, role_id: int) -> bool:
        self._op.cursor.execute(
            "DELETE FROM ssys_employee_role WHERE emp_id = ? AND role_id = ?",
            [int(emp_id), int(role_id)],
        )
        self._op.connection.commit()
        return self._op.cursor.rowcount > 0

    def list_roles(self, emp_id: int):
        from data_storage_services.sql_db_services.ssys.role_service import SsysRoleService
        svc = SsysRoleService(operator=self._op)
        self._op.cursor.execute(
            "SELECT role_id FROM ssys_employee_role WHERE emp_id = ?",
            [int(emp_id)],
        )
        role_ids = [int(dict(r)['role_id']) for r in self._op.cursor.fetchall()]
        return [svc.get_by_id(rid) for rid in role_ids if svc.get_by_id(rid)]

    def list_role_ids(self, emp_id: int) -> List[int]:
        self._op.cursor.execute(
            "SELECT role_id FROM ssys_employee_role WHERE emp_id = ?",
            [int(emp_id)],
        )
        return [int(dict(r)['role_id']) for r in self._op.cursor.fetchall()]

    def has_role(self, emp_id: int, role_id: int) -> bool:
        self._op.cursor.execute(
            "SELECT 1 FROM ssys_employee_role WHERE emp_id = ? AND role_id = ?",
            [int(emp_id), int(role_id)],
        )
        return self._op.cursor.fetchone() is not None

    def employees_with_role(self, role_id: int) -> List[Employee]:
        self._op.cursor.execute(
            "SELECT emp_id FROM ssys_employee_role WHERE role_id = ?",
            [int(role_id)],
        )
        emp_ids = [int(dict(r)['emp_id']) for r in self._op.cursor.fetchall()]
        return [self.get_by_id(eid) for eid in emp_ids if self.get_by_id(eid)]

    def assign_roles(self, emp_id: int, role_ids: List[int]) -> int:
        added = 0
        for rid in role_ids:
            if self.assign_role(emp_id, rid):
                added += 1
        return added

    def revoke_all_roles(self, emp_id: int) -> int:
        self._op.cursor.execute(
            "DELETE FROM ssys_employee_role WHERE emp_id = ?",
            [int(emp_id)],
        )
        self._op.connection.commit()
        return self._op.cursor.rowcount

    # ---------- 辅助 ----------
    def _from_row(self, row: Dict[str, Any]) -> Employee:
        emp = Employee(**row)
        if emp.org_id is not None and not emp.org_name:
            try:
                if self._org_svc is None:
                    self._org_svc = SsysOrganizationService(operator=self._op)
                org = self._org_svc.get_by_id(emp.org_id)
                if org is not None:
                    emp.org_name = org.org_name
            except Exception as ex:
                logger.debug("resolve org_name failed: %s", ex)
        return emp
