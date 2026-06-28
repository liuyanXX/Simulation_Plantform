"""方案元空间 · 方案持久化服务 (SmetaSolutionService)

对应表:
  - smeta_solutions          当前状态快照 (主表)
  - smeta_solution_revision  修订历史表 (追加式, 一条修订一行)

列表字段 (目的/目标/举措/组织/人员/限制/风险/问题 + 文档信息 ID 列表)
在 DB 中以 TEXT 存储 JSON 字符串; Service 层透明序列化/反序列化。
"""
from __future__ import annotations
import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from data_storage_services.SQLite.sqlite_operator import SQLiteOperator
from bo.smeta.solution import (
    RevisionRecord,
    Solution,
    SolutionBaseInfo,
    SolutionDocInfo,
    SolutionKeyInfo,
    SolutionStatus,
    _gen_id,
    _now_iso,
    new_solution,
)


logger = logging.getLogger("SmetaSolutionService")


def _j(v: Any) -> str:
    return json.dumps(v, ensure_ascii=False, separators=(",", ":"))


def _jloads(raw: Any, default: Any = None) -> Any:
    if raw is None or raw == "":
        return default if default is not None else []
    try:
        return json.loads(raw)
    except Exception:
        return default if default is not None else []


class SmetaSolutionService:
    """方案持久化服务。"""

    TABLE = "smeta_solutions"
    REV_TABLE = "smeta_solution_revision"

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

    def __enter__(self) -> "SmetaSolutionService":
        return self

    def __exit__(self, *args: Any) -> None:
        self._op.disconnect()

    @property
    def cursor(self):
        return self._op.cursor

    @property
    def connection(self):
        return self._op.connection

    # ------------------------------------------------------------------
    # 增加方案
    # ------------------------------------------------------------------
    def add(self, solution: Solution) -> Solution:
        if not solution.base.id:
            solution.base.id = _gen_id()
        if not solution.created_at:
            solution.created_at = _now_iso()
        solution.updated_at = _now_iso()
        if not solution.revisions:
            solution.add_revision("system", "创建方案")
        cur = self.cursor
        cur.execute(f"SELECT 1 FROM {self.TABLE} WHERE id = ?", [solution.base.id])
        if cur.fetchone() is not None:
            return self.update(solution)
        cur.execute(
            f"SELECT 1 FROM {self.TABLE} WHERE solution_name = ?",
            [solution.base.solution_name],
        )
        if cur.fetchone() is not None:
            raise ValueError(f"方案名称已存在: {solution.base.solution_name}")
        self._upsert_main(solution)
        self._insert_revisions(solution)
        self.connection.commit()
        return self.get_by_id(solution.base.id)

    # ------------------------------------------------------------------
    # 删除方案 (同时清理修订表)
    # ------------------------------------------------------------------
    def delete(self, solution_id: str) -> bool:
        cur = self.cursor
        cur.execute(f"DELETE FROM {self.TABLE} WHERE id = ?", [solution_id])
        cur.execute(f"DELETE FROM {self.REV_TABLE} WHERE solution_id = ?", [solution_id])
        self.connection.commit()
        return cur.rowcount > 0

    # ------------------------------------------------------------------
    # 变更属性 (同时追加一次修订记录)
    # ------------------------------------------------------------------
    def update(
        self,
        solution: Solution,
        modifier: Optional[str] = None,
        change_summary: Optional[str] = None,
    ) -> Solution:
        if not solution.base.id:
            raise ValueError("update 需要 solution.base.id")
        existing = self.get_by_id(solution.base.id)
        if existing is None:
            return self.add(solution)
        if modifier and change_summary:
            solution.add_revision(modifier, change_summary)
        solution.updated_at = _now_iso()
        self._upsert_main(solution)
        self._insert_revisions(solution)
        self.connection.commit()
        return self.get_by_id(solution.base.id)

    def bump_version(
        self,
        solution_id: str,
        mode: str = "minor",
        modifier: str = "system",
        change_summary: str = "",
    ) -> Optional[Solution]:
        cur = self.get_by_id(solution_id)
        if cur is None:
            return None
        if mode == "major":
            cur.bump_major(modifier, change_summary or "主版本号递增")
        else:
            cur.bump_minor(modifier, change_summary or "次版本号递增")
        return self.update(cur)

    # ------------------------------------------------------------------
    # 查找
    # ------------------------------------------------------------------
    def get_by_id(self, solution_id: str) -> Optional[Solution]:
        cur = self.cursor
        cur.execute(f"SELECT * FROM {self.TABLE} WHERE id = ?", [solution_id])
        row = cur.fetchone()
        if not row:
            return None
        sol = self._row_to_solution(dict(row))
        cur.execute(
            f"SELECT * FROM {self.REV_TABLE} WHERE solution_id = ? ORDER BY revision_no ASC",
            [solution_id],
        )
        sol.revisions = [RevisionRecord(**dict(r)) for r in cur.fetchall()]
        return sol

    def get_by_name(self, solution_name: str) -> Optional[Solution]:
        cur = self.cursor
        cur.execute(f"SELECT * FROM {self.TABLE} WHERE solution_name = ?", [solution_name])
        row = cur.fetchone()
        if not row:
            return None
        return self.get_by_id(dict(row)["id"])

    def search_by_content(
        self,
        keyword: str,
        *,
        limit: int = 100,
        solution_id: Optional[str] = None,
    ) -> List[Solution]:
        if not keyword:
            return self.list_all(limit=limit, solution_id=solution_id)
        like = f"%{keyword}%"
        fields = [
            "solution_name",
            "summary",
            "key_purpose",
            "key_objectives",
            "key_measures",
            "key_organizations",
            "key_personnel",
            "key_work_mechanism",
            "key_work_content",
            "key_constraints",
            "key_risk_list",
            "key_issue_list",
            "key_notes",
        ]
        where = " OR ".join([f"{f} LIKE ?" for f in fields])
        params: List[Any] = [like] * len(fields)
        if solution_id:
            where = f"id = ? AND ({where})"
            params = [solution_id] + params
        cur = self.cursor
        cur.execute(
            f"SELECT * FROM {self.TABLE} WHERE {where} ORDER BY updated_at DESC LIMIT ?",
            params + [limit],
        )
        return [s for s in (self.get_by_id(dict(r)["id"]) for r in cur.fetchall()) if s is not None]

    def list_all(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
        status: Optional[str] = None,
    ) -> List[Solution]:
        clauses: List[str] = []
        params: List[Any] = []
        if status:
            clauses.append("status = ?")
            params.append(status)
        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        cur = self.cursor
        cur.execute(
            f"SELECT * FROM {self.TABLE} {where} ORDER BY updated_at DESC LIMIT ? OFFSET ?",
            params + [limit, offset],
        )
        return [s for s in (self.get_by_id(dict(r)["id"]) for r in cur.fetchall()) if s is not None]

    def count(self, status: Optional[str] = None) -> int:
        clauses: List[str] = []
        params: List[Any] = []
        if status:
            clauses.append("status = ?")
            params.append(status)
        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        cur = self.cursor
        cur.execute(f"SELECT COUNT(*) AS cnt FROM {self.TABLE} {where}", params)
        row = cur.fetchone()
        return int(dict(row)["cnt"]) if row else 0

    # ------------------------------------------------------------------
    # 导出 (JSON)
    # ------------------------------------------------------------------
    def export(self, solution_id: Optional[str] = None, keyword: Optional[str] = None) -> str:
        if solution_id:
            sol = self.get_by_id(solution_id)
            data = sol.model_dump() if sol else {}
        elif keyword:
            data = [s.model_dump() for s in self.search_by_content(keyword)]
        else:
            data = [s.model_dump() for s in self.list_all()]
        return json.dumps(data, ensure_ascii=False, indent=2)

    # ------------------------------------------------------------------
    # 内部: 主表 & 修订表
    # ------------------------------------------------------------------
    def _upsert_main(self, sol: Solution) -> None:
        cur = self.cursor
        row = self._solution_to_row(sol)
        columns = list(row.keys())
        placeholders = ", ".join(["?"] * len(columns))
        updates = ", ".join([f"{c} = excluded.{c}" for c in columns if c != "id"])
        cur.execute(
            f"INSERT INTO {self.TABLE} ({', '.join(columns)}) VALUES ({placeholders}) "
            f"ON CONFLICT(id) DO UPDATE SET {updates}",
            list(row.values()),
        )

    def _insert_revisions(self, sol: Solution) -> None:
        cur = self.cursor
        cur.execute(f"DELETE FROM {self.REV_TABLE} WHERE solution_id = ?", [sol.base.id])
        for r in sol.revisions:
            cur.execute(
                f"INSERT INTO {self.REV_TABLE} "
                f"(solution_id, revision_no, modifier, modified_at, change_summary) "
                f"VALUES (?, ?, ?, ?, ?)",
                [sol.base.id, r.revision_no, r.modifier, r.modified_at, r.change_summary],
            )

    def _solution_to_row(self, sol: Solution) -> Dict[str, Any]:
        return {
            "id": sol.base.id,
            "solution_name": sol.base.solution_name,
            "major_version": sol.base.major_version,
            "minor_version": sol.base.minor_version,
            "status": sol.base.status,
            "category": sol.base.category,
            "summary": sol.base.summary,
            "key_purpose": _j(sol.key.purpose),
            "key_objectives": _j(sol.key.objectives),
            "key_measures": _j(sol.key.measures),
            "key_organizations": _j(sol.key.organizations),
            "key_personnel": _j(sol.key.personnel),
            "key_work_mechanism": sol.key.work_mechanism,
            "key_work_content": sol.key.work_content,
            "key_constraints": _j(sol.key.constraints),
            "key_risk_list": _j(sol.key.risk_list),
            "key_issue_list": _j(sol.key.issue_list),
            "key_notes": sol.key.notes,
            "doc_main_docs": _j(sol.doc.main_docs),
            "doc_attachments": _j(sol.doc.attachments),
            "doc_references": _j(sol.doc.references),
            "created_at": sol.created_at,
            "updated_at": sol.updated_at,
        }

    def _row_to_solution(self, row: Dict[str, Any]) -> Solution:
        base = SolutionBaseInfo(
            id=row["id"],
            solution_name=row["solution_name"],
            major_version=int(row["major_version"]),
            minor_version=int(row["minor_version"]),
            status=row.get("status") or SolutionStatus.DRAFT.value,
            category=row.get("category"),
            summary=row.get("summary"),
        )
        key = SolutionKeyInfo(
            purpose=_jloads(row.get("key_purpose")),
            objectives=_jloads(row.get("key_objectives")),
            measures=_jloads(row.get("key_measures")),
            organizations=_jloads(row.get("key_organizations")),
            personnel=_jloads(row.get("key_personnel")),
            work_mechanism=row.get("key_work_mechanism"),
            work_content=row.get("key_work_content"),
            constraints=_jloads(row.get("key_constraints")),
            risk_list=_jloads(row.get("key_risk_list")),
            issue_list=_jloads(row.get("key_issue_list")),
            notes=row.get("key_notes"),
        )
        doc = SolutionDocInfo(
            main_docs=_jloads(row.get("doc_main_docs")),
            attachments=_jloads(row.get("doc_attachments")),
            references=_jloads(row.get("doc_references")),
        )
        return Solution(
            base=base,
            key=key,
            doc=doc,
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
