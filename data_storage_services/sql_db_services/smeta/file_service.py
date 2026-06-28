"""方案元空间 · 方案文件元数据持久化服务 (SmetaFileService)

负责 smeta_file 表的增/删/改/查, 与 SmetaFileStorage(实体文件服务) 配合使用。

典型用法:
    db_svc = SmetaFileService()
    file_svc = SmetaFileStorage()
    # 1) 实体文件落盘 + 获取完整 File 元数据
    f = file_svc.save_text(solution_id, file_name, category, content)
    # 2) 元数据入库
    saved = db_svc.add(f)
"""
from __future__ import annotations
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from data_storage_services.SQLite.sqlite_operator import SQLiteOperator
from bo.smeta.file import File


logger = logging.getLogger("SmetaFileService")


def _now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


class SmetaFileService:
    """方案元空间 · File 元数据持久化服务。"""

    TABLE = "smeta_file"

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

    def __enter__(self) -> "SmetaFileService":
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
    def add(self, file: File) -> File:
        if not file.id:
            raise ValueError("File.id 必须由上层(通常是 SmetaFileStorage.save)生成后再 add")
        if not file.created_at:
            file.created_at = _now_iso()
        file.updated_at = _now_iso()
        file_dict = file.model_dump()
        columns = ", ".join(file_dict.keys())
        placeholders = ", ".join(["?"] * len(file_dict))
        try:
            self._op.cursor.execute(
                f"INSERT INTO {self.TABLE} ({columns}) VALUES ({placeholders})",
                list(file_dict.values()),
            )
            self._op.connection.commit()
        except Exception:
            existing = self.get_by_id(file.id)
            if existing is not None:
                return self.update(file)
            raise
        return self.get_by_id(file.id)

    def get_by_id(self, file_id: str) -> Optional[File]:
        self._op.cursor.execute(
            f"SELECT * FROM {self.TABLE} WHERE id = ?", [file_id]
        )
        row = self._op.cursor.fetchone()
        return self._from_row(dict(row)) if row else None

    def get_by_name(self, solution_id: str, file_name: str) -> List[File]:
        self._op.cursor.execute(
            f"SELECT * FROM {self.TABLE} WHERE solution_id = ? AND file_name = ? "
            f"ORDER BY updated_at DESC",
            [solution_id, file_name],
        )
        return [self._from_row(dict(r)) for r in self._op.cursor.fetchall()]

    def update(self, file: File) -> Optional[File]:
        if not file.id:
            return None
        file.updated_at = _now_iso()
        fields: List[str] = []
        values: List[Any] = []
        for k, v in file.model_dump().items():
            if k == "id":
                continue
            fields.append(f"{k} = ?")
            values.append(v)
        values.append(file.id)
        self._op.cursor.execute(
            f"UPDATE {self.TABLE} SET {', '.join(fields)} WHERE id = ?",
            values,
        )
        self._op.connection.commit()
        return self.get_by_id(file.id)

    def delete(self, file_id: str) -> bool:
        self._op.cursor.execute(
            f"DELETE FROM {self.TABLE} WHERE id = ?", [file_id]
        )
        self._op.connection.commit()
        return self._op.cursor.rowcount > 0

    def delete_by_solution(self, solution_id: str) -> int:
        self._op.cursor.execute(
            f"DELETE FROM {self.TABLE} WHERE solution_id = ?",
            [solution_id],
        )
        self._op.connection.commit()
        return self._op.cursor.rowcount

    # ---------- 查找 ----------
    def list_all(
        self,
        solution_id: Optional[str] = None,
        file_category: Optional[str] = None,
        keyword: Optional[str] = None,
        page: int = 1,
        page_size: int = 100,
    ) -> List[File]:
        clauses: List[str] = []
        params: List[Any] = []
        if solution_id:
            clauses.append("solution_id = ?")
            params.append(solution_id)
        if file_category:
            from bo.smeta.file import _category_to_cn
            file_category_cn = _category_to_cn(file_category)
            clauses.append("file_category = ?")
            params.append(file_category_cn)
        if keyword:
            clauses.append("(file_name LIKE ? OR description LIKE ? OR solution_name LIKE ?)")
            params += [f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"]
        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        offset = max(0, (page - 1)) * page_size
        self._op.cursor.execute(
            f"SELECT * FROM {self.TABLE} {where} "
            f"ORDER BY updated_at DESC LIMIT ? OFFSET ?",
            params + [page_size, offset],
        )
        return [self._from_row(dict(r)) for r in self._op.cursor.fetchall()]

    def list_by_solution(self, solution_id: str) -> List[File]:
        return self.list_all(solution_id=solution_id)

    def count(
        self,
        solution_id: Optional[str] = None,
        file_category: Optional[str] = None,
    ) -> int:
        clauses: List[str] = []
        params: List[Any] = []
        if solution_id:
            clauses.append("solution_id = ?")
            params.append(solution_id)
        if file_category:
            from bo.smeta.file import _category_to_cn
            clauses.append("file_category = ?")
            params.append(_category_to_cn(file_category))
        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        self._op.cursor.execute(
            f"SELECT COUNT(*) AS cnt FROM {self.TABLE} {where}", params
        )
        row = self._op.cursor.fetchone()
        return int(dict(row)["cnt"]) if row else 0

    def list_solutions(self) -> List[Dict[str, Any]]:
        self._op.cursor.execute(
            f"SELECT DISTINCT solution_id, solution_name FROM {self.TABLE} "
            f"ORDER BY solution_id ASC"
        )
        return [dict(r) for r in self._op.cursor.fetchall()]

    # ---------- 辅助 ----------
    def _from_row(self, row: Dict[str, Any]) -> File:
        return File(**row)
