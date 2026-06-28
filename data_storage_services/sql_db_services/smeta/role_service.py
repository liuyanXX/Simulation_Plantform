"""方案元空间 · 角色对象持久化服务 (SmetaRoleService)

方案元空间 = 系统空间 + solution_id(方案ID) + solution_version(方案版本号)。
所有操作限定在同一个 (solution_id, solution_version) 命名空间内。
额外提供批量复制接口: load_from_ssys(...) 从系统空间复制角色对象。
"""
from __future__ import annotations
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from data_storage_services.SQLite.sqlite_operator import SQLiteOperator
from data_storage_services.sql_db_services.ssys.role_service import (
    SsysRoleService,
)
from bo.ssys.role import Role as SsysRole
from bo.smeta.role import Role


logger = logging.getLogger("SmetaRoleService")


def _now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


class SmetaRoleService:
    """方案元空间 · Role 持久化服务。"""

    TABLE = "smeta_role"

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
        self._ssys_role_svc = None

    def __enter__(self) -> "SmetaRoleService":
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
    def add(self, role: Role) -> Role:
        if not role.created_at:
            role.created_at = _now_iso()
        role.updated_at = _now_iso()
        role_dict = role.model_dump()
        role_dict.pop("id", None)
        columns = ", ".join(role_dict.keys())
        placeholders = ", ".join(["?"] * len(role_dict))
        self._op.cursor.execute(
            f"INSERT INTO {self.TABLE} ({columns}) VALUES ({placeholders})",
            list(role_dict.values()),
        )
        self._op.connection.commit()
        role.id = self._op.cursor.lastrowid
        return self.get_by_id(role.id)

    def get_by_id(self, rid: int) -> Optional[Role]:
        self._op.cursor.execute(
            f"SELECT * FROM {self.TABLE} WHERE id = ?", [int(rid)]
        )
        row = self._op.cursor.fetchone()
        return self._from_row(dict(row)) if row else None

    def get_by_code(
        self, solution_id: str, solution_version: str, role_code: str
    ) -> Optional[Role]:
        self._op.cursor.execute(
            f"SELECT * FROM {self.TABLE} "
            f"WHERE solution_id = ? AND solution_version = ? AND role_code = ?",
            [solution_id, solution_version, role_code],
        )
        row = self._op.cursor.fetchone()
        return self._from_row(dict(row)) if row else None

    def update(self, role: Role) -> Optional[Role]:
        if role.id is None:
            return None
        role.updated_at = _now_iso()
        fields: List[str] = []
        values: List[Any] = []
        for k, v in role.model_dump().items():
            if k == "id":
                continue
            fields.append(f"{k} = ?")
            values.append(v)
        values.append(role.id)
        self._op.cursor.execute(
            f"UPDATE {self.TABLE} SET {', '.join(fields)} WHERE id = ?",
            values,
        )
        self._op.connection.commit()
        return self.get_by_id(role.id)

    def delete(self, rid: int) -> bool:
        self._op.cursor.execute(
            f"DELETE FROM {self.TABLE} WHERE id = ?", [int(rid)]
        )
        self._op.connection.commit()
        return self._op.cursor.rowcount > 0

    # ---------- 查找（限定方案命名空间） ----------
    def list_all(
        self,
        solution_id: str,
        solution_version: str,
        status: Optional[str] = None,
        keyword: Optional[str] = None,
        page: int = 1,
        page_size: int = 100,
    ) -> List[Role]:
        clauses: List[str] = [
            "solution_id = ?",
            "solution_version = ?",
        ]
        params: List[Any] = [solution_id, solution_version]
        if status:
            clauses.append("status = ?")
            params.append(status)
        if keyword:
            clauses.append(
                "(role_name LIKE ? OR role_code LIKE ? OR description LIKE ?)"
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

    def search_by_name(
        self, solution_id: str, solution_version: str, keyword: str
    ) -> List[Role]:
        return self.list_all(
            solution_id=solution_id,
            solution_version=solution_version,
            keyword=keyword,
        )

    def count(
        self,
        solution_id: str,
        solution_version: str,
        status: Optional[str] = None,
        keyword: Optional[str] = None,
    ) -> int:
        clauses: List[str] = [
            "solution_id = ?",
            "solution_version = ?",
        ]
        params: List[Any] = [solution_id, solution_version]
        if status:
            clauses.append("status = ?")
            params.append(status)
        if keyword:
            clauses.append(
                "(role_name LIKE ? OR role_code LIKE ? OR description LIKE ?)"
            )
            params += [f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"]
        where = "WHERE " + " AND ".join(clauses)
        self._op.cursor.execute(
            f"SELECT COUNT(*) AS cnt FROM {self.TABLE} {where}", params
        )
        row = self._op.cursor.fetchone()
        return int(dict(row)["cnt"]) if row else 0

    def list_solutions(self) -> List[Dict[str, Any]]:
        self._op.cursor.execute(
            f"SELECT DISTINCT solution_id, solution_version FROM {self.TABLE} "
            f"ORDER BY solution_id ASC, solution_version ASC"
        )
        return [dict(r) for r in self._op.cursor.fetchall()]

    # ---------- 批量复制（系统空间 → 方案元空间） ----------
    def load_from_ssys(
        self,
        solution_id: str,
        solution_version: str,
        ssys_role_ids: Optional[List[int]] = None,
        overwrite: bool = False,
    ) -> int:
        if self._ssys_role_svc is None:
            self._ssys_role_svc = SsysRoleService(operator=self._op)

        if overwrite:
            self._op.cursor.execute(
                f"DELETE FROM {self.TABLE} "
                f"WHERE solution_id = ? AND solution_version = ?",
                [solution_id, solution_version],
            )
            self._op.connection.commit()

        if ssys_role_ids:
            ssys_roles: List[SsysRole] = []
            for rid in ssys_role_ids:
                r = self._ssys_role_svc.get_by_id(int(rid))
                if r is not None:
                    ssys_roles.append(r)
        else:
            ssys_roles = self._ssys_role_svc.list_all()

        added = 0
        seen_codes = set()
        for sr in ssys_roles:
            if sr.role_code in seen_codes:
                continue
            seen_codes.add(sr.role_code)
            if self.get_by_code(solution_id, solution_version, sr.role_code):
                continue
            try:
                self._op.cursor.execute(
                    f"INSERT INTO {self.TABLE} "
                    f"(solution_id, solution_version, role_code, role_name, description, "
                    f"status, extra_info, created_at, updated_at) "
                    f"VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    [
                        solution_id, solution_version,
                        sr.role_code, sr.role_name, sr.description,
                        sr.status, sr.extra_info,
                        _now_iso(), _now_iso(),
                    ],
                )
                self._op.connection.commit()
                added += 1
            except Exception as ex:
                logger.debug("load_from_ssys skip: %s", ex)
        return added

    # ---------- 辅助 ----------
    def _from_row(self, row: Dict[str, Any]) -> Role:
        return Role(**row)
