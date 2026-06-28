"""仿真虚空间 · 人员对象持久化服务 (SenvEmployeeService)

所有操作限定在同一个 (task_id, batch_no) 命名空间内。
额外提供批量复制接口:
  - load_from_ssys(...)  — 从系统空间复制员工
  - load_from_smeta(...) — 从方案元空间复制员工
员工-角色关联 (M:N): assign_role / revoke_role / list_roles ...
"""
from __future__ import annotations
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from data_storage_services.SQLite.sqlite_operator import SQLiteOperator
from data_storage_services.sql_db_services.ssys.employee_service import (
    SsysEmployeeService,
)
from data_storage_services.sql_db_services.smeta.employee_service import (
    SmetaEmployeeService,
)
from bo.ssys.employee import Employee as SsysEmployee
from bo.smeta.employee import Employee as SmetaEmployee
from bo.senv.employee import Employee


logger = logging.getLogger("SenvEmployeeService")


def _now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


class SenvEmployeeService:
    """仿真虚空间 · Employee 持久化服务。"""

    TABLE = "senv_employee"

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
        self._ssys_emp_svc = None
        self._smeta_emp_svc = None
        self._task_id = None
        self._batch_no = None

    def __enter__(self) -> "SenvEmployeeService":
        return self

    def __exit__(self, *args: Any) -> None:
        self._op.disconnect()

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

    def get_by_code(self, task_id: str, batch_no: str, emp_code: str) -> Optional[Employee]:
        self._op.cursor.execute(
            f"SELECT * FROM {self.TABLE} "
            f"WHERE task_id = ? AND batch_no = ? AND emp_code = ?",
            [task_id, batch_no, emp_code],
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

    # ---------- 查找（限定任务批次命名空间） ----------
    def list_all(
        self,
        task_id: str,
        batch_no: str,
        status: Optional[str] = None,
        org_id: Optional[int] = None,
        keyword: Optional[str] = None,
        page: int = 1,
        page_size: int = 100,
    ) -> List[Employee]:
        clauses: List[str] = [
            "task_id = ?",
            "batch_no = ?",
        ]
        params: List[Any] = [task_id, batch_no]
        if status:
            clauses.append("status = ?")
            params.append(status)
        if org_id is not None:
            clauses.append("org_id = ?")
            params.append(int(org_id))
        if keyword:
            clauses.append(
                "(emp_name LIKE ? OR emp_code LIKE ? OR position LIKE ?)"
            )
            params += [f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"]
        where = "WHERE " + " AND ".join(clauses)
        offset = max(0, (page - 1)) * page_size
        self._op.cursor.execute(
            f"SELECT * FROM {self.TABLE} {where} "
            f"ORDER BY id ASC LIMIT ? OFFSET ?",
            params + [page_size, offset],
        )
        return [self._from_row(dict(r)) for r in self._op.cursor.fetchall()]

    def search_by_name(self, task_id: str, batch_no: str, keyword: str) -> List[Employee]:
        return self.list_all(task_id, batch_no, keyword=keyword)

    def list_by_org(self, task_id: str, batch_no: str, org_id: int) -> List[Employee]:
        return self.list_all(task_id, batch_no, org_id=int(org_id))

    def count(
        self,
        task_id: str,
        batch_no: str,
        status: Optional[str] = None,
        org_id: Optional[int] = None,
        keyword: Optional[str] = None,
    ) -> int:
        clauses: List[str] = [
            "task_id = ?",
            "batch_no = ?",
        ]
        params: List[Any] = [task_id, batch_no]
        if status:
            clauses.append("status = ?")
            params.append(status)
        if org_id is not None:
            clauses.append("org_id = ?")
            params.append(int(org_id))
        if keyword:
            clauses.append(
                "(emp_name LIKE ? OR emp_code LIKE ? OR position LIKE ?)"
            )
            params += [f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"]
        where = "WHERE " + " AND ".join(clauses)
        self._op.cursor.execute(
            f"SELECT COUNT(*) AS cnt FROM {self.TABLE} {where}", params
        )
        row = self._op.cursor.fetchone()
        return int(dict(row)["cnt"]) if row else 0

    def list_tasks(self) -> List[Dict[str, Any]]:
        self._op.cursor.execute(
            f"SELECT DISTINCT task_id, batch_no FROM {self.TABLE} "
            f"ORDER BY task_id ASC, batch_no ASC"
        )
        return [dict(r) for r in self._op.cursor.fetchall()]

    # ---------- 批量复制 ----------
    def load_from_ssys(
        self,
        task_id: str,
        batch_no: str,
        ssys_org_id: Optional[int] = None,
        ssys_emp_ids: Optional[List[int]] = None,
        overwrite: bool = False,
    ) -> int:
        self._task_id = task_id
        self._batch_no = batch_no
        if self._ssys_emp_svc is None:
            self._ssys_emp_svc = SsysEmployeeService(operator=self._op)
        if overwrite:
            self._op.cursor.execute(
                f"DELETE FROM {self.TABLE} WHERE task_id = ? AND batch_no = ?",
                [task_id, batch_no],
            )
            self._op.connection.commit()

        ssys_emps: List[SsysEmployee] = []
        if ssys_emp_ids:
            for eid in ssys_emp_ids:
                e = self._ssys_emp_svc.get_by_id(int(eid))
                if e is not None:
                    ssys_emps.append(e)
        if ssys_org_id is not None:
            ssys_emps += self._ssys_emp_svc.list_by_org(
                int(ssys_org_id), include_subtree=True
            )
        if not ssys_emp_ids and ssys_org_id is None:
            ssys_emps = self._ssys_emp_svc.list_all()

        return self._bulk_insert(
            ssys_emps, task_id, batch_no,
            code_getter=lambda e: e.emp_code,
            row_getter=lambda e: [
                task_id, batch_no,
                e.emp_code, e.emp_name, e.position,
                e.org_id, e.org_name,
                e.email, e.phone, e.status, e.extra_info,
                _now_iso(), _now_iso(),
            ],
        )

    def load_from_smeta(
        self,
        task_id: str,
        batch_no: str,
        solution_id: str,
        solution_version: str,
        smeta_org_id: Optional[int] = None,
        smeta_emp_ids: Optional[List[int]] = None,
        overwrite: bool = False,
    ) -> int:
        self._task_id = task_id
        self._batch_no = batch_no
        if self._smeta_emp_svc is None:
            self._smeta_emp_svc = SmetaEmployeeService(operator=self._op)
        if overwrite:
            self._op.cursor.execute(
                f"DELETE FROM {self.TABLE} WHERE task_id = ? AND batch_no = ?",
                [task_id, batch_no],
            )
            self._op.connection.commit()

        smeta_emps: List[SmetaEmployee] = []
        if smeta_emp_ids:
            for eid in smeta_emp_ids:
                e = self._smeta_emp_svc.get_by_id(int(eid))
                if e is not None:
                    smeta_emps.append(e)
        if smeta_org_id is not None:
            smeta_emps += self._smeta_emp_svc.list_by_org(
                solution_id, solution_version, int(smeta_org_id)
            )
        if not smeta_emp_ids and smeta_org_id is None:
            smeta_emps = self._smeta_emp_svc.list_all(solution_id, solution_version)

        return self._bulk_insert(
            smeta_emps, task_id, batch_no,
            code_getter=lambda e: e.emp_code,
            row_getter=lambda e: [
                task_id, batch_no,
                e.emp_code, e.emp_name, e.position,
                e.org_id, e.org_name,
                e.email, e.phone, e.status, e.extra_info,
                _now_iso(), _now_iso(),
            ],
        )

    def _bulk_insert(self, source_emps, task_id, batch_no, code_getter, row_getter) -> int:
        added = 0
        seen_codes = set()
        for e in source_emps:
            code = code_getter(e)
            if code in seen_codes:
                continue
            seen_codes.add(code)
            if self.get_by_code(task_id, batch_no, code):
                continue
            try:
                self._op.cursor.execute(
                    f"INSERT INTO {self.TABLE} "
                    f"(task_id, batch_no, emp_code, emp_name, position, "
                    f"org_id, org_name, email, phone, status, extra_info, "
                    f"created_at, updated_at) "
                    f"VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    row_getter(e),
                )
                self._op.connection.commit()
                added += 1
            except Exception as ex:
                logger.debug("bulk_insert skip: %s", ex)
        return added

    # ---------- 员工-角色关联 (M:N) ----------
    def assign_role(self, emp_id: int, role_id: int) -> bool:
        assert self._task_id and self._batch_no, "先调用 load_from_ssys/load_from_smeta 或手动设定"
        self._op.cursor.execute(
            "INSERT OR IGNORE INTO senv_employee_role "
            "(task_id, batch_no, emp_id, role_id, assigned_at) "
            "VALUES (?, ?, ?, ?, ?)",
            [self._task_id, self._batch_no, int(emp_id), int(role_id), _now_iso()],
        )
        self._op.connection.commit()
        return self.has_role(emp_id, role_id)

    def revoke_role(self, emp_id: int, role_id: int) -> bool:
        assert self._task_id and self._batch_no
        self._op.cursor.execute(
            "DELETE FROM senv_employee_role "
            "WHERE task_id = ? AND batch_no = ? AND emp_id = ? AND role_id = ?",
            [self._task_id, self._batch_no, int(emp_id), int(role_id)],
        )
        self._op.connection.commit()
        return self._op.cursor.rowcount > 0

    def list_roles(self, emp_id: int):
        from data_storage_services.sql_db_services.senv.role_service import SenvRoleService
        assert self._task_id and self._batch_no
        svc = SenvRoleService(operator=self._op)
        self._op.cursor.execute(
            "SELECT role_id FROM senv_employee_role "
            "WHERE task_id = ? AND batch_no = ? AND emp_id = ?",
            [self._task_id, self._batch_no, int(emp_id)],
        )
        role_ids = [int(dict(r)['role_id']) for r in self._op.cursor.fetchall()]
        return [svc.get_by_id(rid) for rid in role_ids if svc.get_by_id(rid)]

    def list_role_ids(self, emp_id: int) -> List[int]:
        assert self._task_id and self._batch_no
        self._op.cursor.execute(
            "SELECT role_id FROM senv_employee_role "
            "WHERE task_id = ? AND batch_no = ? AND emp_id = ?",
            [self._task_id, self._batch_no, int(emp_id)],
        )
        return [int(dict(r)['role_id']) for r in self._op.cursor.fetchall()]

    def has_role(self, emp_id: int, role_id: int) -> bool:
        assert self._task_id and self._batch_no
        self._op.cursor.execute(
            "SELECT 1 FROM senv_employee_role "
            "WHERE task_id = ? AND batch_no = ? AND emp_id = ? AND role_id = ?",
            [self._task_id, self._batch_no, int(emp_id), int(role_id)],
        )
        return self._op.cursor.fetchone() is not None

    def employees_with_role(self, role_id: int):
        assert self._task_id and self._batch_no
        self._op.cursor.execute(
            "SELECT emp_id FROM senv_employee_role "
            "WHERE task_id = ? AND batch_no = ? AND role_id = ?",
            [self._task_id, self._batch_no, int(role_id)],
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
        assert self._task_id and self._batch_no
        self._op.cursor.execute(
            "DELETE FROM senv_employee_role "
            "WHERE task_id = ? AND batch_no = ? AND emp_id = ?",
            [self._task_id, self._batch_no, int(emp_id)],
        )
        self._op.connection.commit()
        return self._op.cursor.rowcount

    # ---------- 辅助 ----------
    def _from_row(self, row: Dict[str, Any]) -> Employee:
        return Employee(**row)
