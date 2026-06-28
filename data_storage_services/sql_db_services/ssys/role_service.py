"""系统空间 · 角色对象持久化服务 (SsysRoleService)

直接通过 SQLiteOperator 对 ssys_role 表做增、删、改、查。
查找支持:
  - 按ID查本身           get_by_id(rid)
  - 按角色编码查本身      get_by_code(role_code)
  - 按名称模糊查          search_by_name(keyword)
  - 查全量                list_all(...)
"""
from __future__ import annotations
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from data_storage_services.SQLite.sqlite_operator import SQLiteOperator
from bo.ssys.role import Role


logger = logging.getLogger("SsysRoleService")


def _now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


class SsysRoleService:
    """系统空间 · Role 持久化服务。"""

    TABLE = "ssys_role"

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

    def __enter__(self) -> "SsysRoleService":
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

    def get_by_code(self, role_code: str) -> Optional[Role]:
        self._op.cursor.execute(
            f"SELECT * FROM {self.TABLE} WHERE role_code = ?", [role_code]
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

    def list_all(
        self,
        status: Optional[str] = None,
        keyword: Optional[str] = None,
        page: int = 1,
        page_size: int = 100,
    ) -> List[Role]:
        clauses: List[str] = []
        params: List[Any] = []
        if status:
            clauses.append("status = ?")
            params.append(status)
        if keyword:
            clauses.append("(role_name LIKE ? OR role_code LIKE ? OR description LIKE ?)")
            params += [f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"]
        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        offset = max(0, (page - 1)) * page_size
        self._op.cursor.execute(
            f"SELECT * FROM {self.TABLE} {where} "
            f"ORDER BY id ASC LIMIT ? OFFSET ?",
            params + [page_size, offset],
        )
        return [self._from_row(dict(r)) for r in self._op.cursor.fetchall()]

    def search_by_name(self, keyword: str) -> List[Role]:
        return self.list_all(keyword=keyword)

    def count(
        self,
        status: Optional[str] = None,
        keyword: Optional[str] = None,
    ) -> int:
        clauses: List[str] = []
        params: List[Any] = []
        if status:
            clauses.append("status = ?")
            params.append(status)
        if keyword:
            clauses.append("(role_name LIKE ? OR role_code LIKE ? OR description LIKE ?)")
            params += [f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"]
        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        self._op.cursor.execute(
            f"SELECT COUNT(*) AS cnt FROM {self.TABLE} {where}", params
        )
        row = self._op.cursor.fetchone()
        return int(dict(row)["cnt"]) if row else 0

    # ---------- 辅助 ----------
    def _from_row(self, row: Dict[str, Any]) -> Role:
        return Role(**row)
