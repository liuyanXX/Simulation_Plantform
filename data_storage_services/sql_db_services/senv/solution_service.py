"""仿真虚空间 · 方案持久化服务 (SenvSolutionService)

对应表:
  - senv_solutions          当前状态快照 (主表, 联合唯一主键)
  - senv_solution_revision  修订历史表 (追加式)

方法签名与方案元空间 SmetaSolutionService 保持一致, 区别仅在于:
  1) 操作 senv_solutions / senv_solution_revision 表
  2) 联合唯一键 (id, simulation_task_id, simulation_task_batch)
  3) 提供 from_smeta() 从方案元空间复制方案对象 (复制时指定仿真任务 ID + 批次)
"""
from __future__ import annotations
import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from data_storage_services.SQLite.sqlite_operator import SQLiteOperator
from bo.senv.solution import (
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


logger = logging.getLogger("SenvSolutionService")


def _j(v: Any) -> str:
    return json.dumps(v, ensure_ascii=False, separators=(",", ":"))


def _jloads(raw: Any, default: Any = None) -> Any:
    if raw is None or raw == "":
        return default if default is not None else []
    if not isinstance(raw, str):
        raw = str(raw)
    try:
        v = json.loads(raw)
    except Exception:
        return default if default is not None else []
    if v is None:
        return default if default is not None else []
    return v


class SenvSolutionService:
    """仿真虚空间 · 方案持久化服务。"""

    TABLE = "senv_solutions"
    REV_TABLE = "senv_solution_revision"

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

    def __enter__(self) -> "SenvSolutionService":
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
        if not solution.simulation_task_id or not solution.simulation_task_batch:
            raise ValueError(
                "仿真虚空间方案必须提供 simulation_task_id + simulation_task_batch"
            )
        if not solution.created_at:
            solution.created_at = _now_iso()
        solution.updated_at = _now_iso()
        if not solution.revisions:
            solution.add_revision("system", "创建仿真虚空间方案")
        cur = self.cursor
        cur.execute(
            f"SELECT 1 FROM {self.TABLE} "
            f"WHERE id = ? AND simulation_task_id = ? AND simulation_task_batch = ?",
            [
                solution.base.id,
                solution.simulation_task_id,
                solution.simulation_task_batch,
            ],
        )
        if cur.fetchone() is not None:
            return self.update(solution)
        cur.execute(
            f"SELECT 1 FROM {self.TABLE} "
            f"WHERE solution_name = ? AND simulation_task_id = ? AND simulation_task_batch = ?",
            [
                solution.base.solution_name,
                solution.simulation_task_id,
                solution.simulation_task_batch,
            ],
        )
        if cur.fetchone() is not None:
            raise ValueError(
                f"仿真任务 {solution.simulation_task_id}/{solution.simulation_task_batch} "
                f"下已存在同名方案: {solution.base.solution_name}"
            )
        self._upsert_main(solution)
        self._insert_revisions(solution)
        self.connection.commit()
        return self.get_by_unique(
            solution.base.id,
            solution.simulation_task_id,
            solution.simulation_task_batch,
        )

    # ------------------------------------------------------------------
    # 删除方案
    # ------------------------------------------------------------------
    def delete(
        self,
        solution_id: str,
        simulation_task_id: str,
        simulation_task_batch: str,
    ) -> bool:
        cur = self.cursor
        cur.execute(
            f"DELETE FROM {self.REV_TABLE} "
            f"WHERE solution_id = ? AND simulation_task_id = ? AND simulation_task_batch = ?",
            [solution_id, simulation_task_id, simulation_task_batch],
        )
        cur.execute(
            f"DELETE FROM {self.TABLE} "
            f"WHERE id = ? AND simulation_task_id = ? AND simulation_task_batch = ?",
            [solution_id, simulation_task_id, simulation_task_batch],
        )
        self.connection.commit()
        return cur.rowcount > 0

    def delete_by_task(
        self,
        simulation_task_id: str,
        simulation_task_batch: Optional[str] = None,
    ) -> int:
        cur = self.cursor
        if simulation_task_batch:
            cur.execute(
                f"DELETE FROM {self.REV_TABLE} "
                f"WHERE simulation_task_id = ? AND simulation_task_batch = ?",
                [simulation_task_id, simulation_task_batch],
            )
            cur.execute(
                f"DELETE FROM {self.TABLE} "
                f"WHERE simulation_task_id = ? AND simulation_task_batch = ?",
                [simulation_task_id, simulation_task_batch],
            )
        else:
            cur.execute(
                f"DELETE FROM {self.REV_TABLE} WHERE simulation_task_id = ?",
                [simulation_task_id],
            )
            cur.execute(
                f"DELETE FROM {self.TABLE} WHERE simulation_task_id = ?",
                [simulation_task_id],
            )
        self.connection.commit()
        return cur.rowcount

    # ------------------------------------------------------------------
    # 变更属性
    # ------------------------------------------------------------------
    def update(
        self,
        solution: Solution,
        modifier: Optional[str] = None,
        change_summary: Optional[str] = None,
    ) -> Solution:
        if not solution.base.id:
            raise ValueError("update 需要 solution.base.id")
        existing = self.get_by_unique(
            solution.base.id,
            solution.simulation_task_id,
            solution.simulation_task_batch,
        )
        if existing is None:
            return self.add(solution)
        if modifier and change_summary:
            solution.add_revision(modifier, change_summary)
        solution.updated_at = _now_iso()
        self._upsert_main(solution)
        self._insert_revisions(solution)
        self.connection.commit()
        return self.get_by_unique(
            solution.base.id,
            solution.simulation_task_id,
            solution.simulation_task_batch,
        )

    def bump_version(
        self,
        solution_id: str,
        simulation_task_id: str,
        simulation_task_batch: str,
        mode: str = "minor",
        modifier: str = "system",
        change_summary: str = "",
    ) -> Optional[Solution]:
        cur = self.get_by_unique(solution_id, simulation_task_id, simulation_task_batch)
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
    def get_by_unique(
        self,
        solution_id: str,
        simulation_task_id: str,
        simulation_task_batch: str,
    ) -> Optional[Solution]:
        cur = self.cursor
        cur.execute(
            f"SELECT * FROM {self.TABLE} "
            f"WHERE id = ? AND simulation_task_id = ? AND simulation_task_batch = ?",
            [solution_id, simulation_task_id, simulation_task_batch],
        )
        row = cur.fetchone()
        if not row:
            return None
        sol = self._row_to_solution(dict(row))
        self._load_revisions(sol)
        return sol

    def get_by_name(
        self,
        solution_name: str,
        simulation_task_id: str,
        simulation_task_batch: str,
    ) -> Optional[Solution]:
        cur = self.cursor
        cur.execute(
            f"SELECT * FROM {self.TABLE} "
            f"WHERE solution_name = ? AND simulation_task_id = ? AND simulation_task_batch = ?",
            [solution_name, simulation_task_id, simulation_task_batch],
        )
        row = cur.fetchone()
        if not row:
            return None
        return self.get_by_unique(
            dict(row)["id"],
            dict(row)["simulation_task_id"],
            dict(row)["simulation_task_batch"],
        )

    def search_by_content(
        self,
        keyword: str,
        *,
        simulation_task_id: Optional[str] = None,
        simulation_task_batch: Optional[str] = None,
        limit: int = 100,
    ) -> List[Solution]:
        if not keyword:
            return self.list_all(
                simulation_task_id=simulation_task_id,
                simulation_task_batch=simulation_task_batch,
                limit=limit,
            )
        like = f"%{keyword}%"
        fields = [
            "solution_name", "summary",
            "key_purpose", "key_objectives", "key_measures",
            "key_organizations", "key_personnel",
            "key_work_mechanism", "key_work_content",
            "key_constraints", "key_risk_list", "key_issue_list", "key_notes",
        ]
        where = " OR ".join([f"{f} LIKE ?" for f in fields])
        params: List[Any] = [like] * len(fields)
        extras: List[str] = []
        if simulation_task_id:
            extras.append("simulation_task_id = ?")
            params = [simulation_task_id] + params
        if simulation_task_batch:
            extras.append("simulation_task_batch = ?")
            params = [simulation_task_batch] + params
        if extras:
            where = "(" + where + ") AND " + " AND ".join(extras)
        cur = self.cursor
        cur.execute(
            f"SELECT * FROM {self.TABLE} WHERE {where} ORDER BY updated_at DESC LIMIT ?",
            params + [limit],
        )
        results: List[Solution] = []
        for r in cur.fetchall():
            sol = self._row_to_solution(dict(r))
            self._load_revisions(sol)
            results.append(sol)
        return results

    def list_all(
        self,
        *,
        simulation_task_id: Optional[str] = None,
        simulation_task_batch: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Solution]:
        clauses: List[str] = []
        params: List[Any] = []
        if simulation_task_id:
            clauses.append("simulation_task_id = ?")
            params.append(simulation_task_id)
        if simulation_task_batch:
            clauses.append("simulation_task_batch = ?")
            params.append(simulation_task_batch)
        if status:
            clauses.append("status = ?")
            params.append(status)
        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        cur = self.cursor
        cur.execute(
            f"SELECT * FROM {self.TABLE} {where} ORDER BY updated_at DESC LIMIT ? OFFSET ?",
            params + [limit, offset],
        )
        results: List[Solution] = []
        for r in cur.fetchall():
            sol = self._row_to_solution(dict(r))
            self._load_revisions(sol)
            results.append(sol)
        return results

    def count(
        self,
        *,
        simulation_task_id: Optional[str] = None,
        simulation_task_batch: Optional[str] = None,
        status: Optional[str] = None,
    ) -> int:
        clauses: List[str] = []
        params: List[Any] = []
        if simulation_task_id:
            clauses.append("simulation_task_id = ?")
            params.append(simulation_task_id)
        if simulation_task_batch:
            clauses.append("simulation_task_batch = ?")
            params.append(simulation_task_batch)
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
    def export(
        self,
        *,
        solution_id: Optional[str] = None,
        simulation_task_id: Optional[str] = None,
        simulation_task_batch: Optional[str] = None,
        keyword: Optional[str] = None,
    ) -> str:
        if solution_id and simulation_task_id and simulation_task_batch:
            sol = self.get_by_unique(solution_id, simulation_task_id, simulation_task_batch)
            data = sol.model_dump() if sol else {}
        elif keyword:
            data = [
                s.model_dump()
                for s in self.search_by_content(
                    keyword,
                    simulation_task_id=simulation_task_id,
                    simulation_task_batch=simulation_task_batch,
                )
            ]
        else:
            data = [
                s.model_dump()
                for s in self.list_all(
                    simulation_task_id=simulation_task_id,
                    simulation_task_batch=simulation_task_batch,
                )
            ]
        return json.dumps(data, ensure_ascii=False, indent=2)

    # ------------------------------------------------------------------
    # 从方案元空间复制 (用户要求的方法)
    # ------------------------------------------------------------------
    def from_smeta(
        self,
        smeta_solution_id: str,
        simulation_task_id: str,
        simulation_task_batch: str,
        modifier: str = "system",
    ) -> Optional[Solution]:
        """从方案元空间 smeta_solutions 表复制方案到仿真虚空间。"""
        cur = self.cursor
        cur.execute(f"SELECT * FROM smeta_solutions WHERE id = ?", [smeta_solution_id])
        row = cur.fetchone()
        if not row:
            logger.warning("smeta_solution not found: %s", smeta_solution_id)
            return None
        rowd = dict(row)

        base = SolutionBaseInfo(
            id=_gen_id(),
            solution_name=rowd["solution_name"],
            major_version=int(rowd["major_version"]),
            minor_version=int(rowd["minor_version"]),
            status=rowd.get("status") or SolutionStatus.DRAFT.value,
            category=rowd.get("category"),
            summary=rowd.get("summary"),
        )
        key = SolutionKeyInfo(
            purpose=_jloads(rowd.get("key_purpose")),
            objectives=_jloads(rowd.get("key_objectives")),
            measures=_jloads(rowd.get("key_measures")),
            organizations=_jloads(rowd.get("key_organizations")),
            personnel=_jloads(rowd.get("key_personnel")),
            work_mechanism=rowd.get("key_work_mechanism"),
            work_content=rowd.get("key_work_content"),
            constraints=_jloads(rowd.get("key_constraints")),
            risk_list=_jloads(rowd.get("key_risk_list")),
            issue_list=_jloads(rowd.get("key_issue_list")),
            notes=rowd.get("key_notes"),
        )
        doc = SolutionDocInfo(
            main_docs=_jloads(rowd.get("doc_main_docs")),
            attachments=_jloads(rowd.get("doc_attachments")),
            references=_jloads(rowd.get("doc_references")),
        )
        sol = Solution(
            base=base,
            key=key,
            doc=doc,
            simulation_task_id=simulation_task_id,
            simulation_task_batch=simulation_task_batch,
        )

        cur.execute(
            f"SELECT revision_no, modifier, modified_at, change_summary "
            f"FROM smeta_solution_revision WHERE solution_id = ? ORDER BY revision_no ASC",
            [smeta_solution_id],
        )
        sol.revisions = [
            RevisionRecord(
                revision_no=int(d["revision_no"]),
                modifier=d["modifier"],
                modified_at=d["modified_at"],
                change_summary=d["change_summary"],
            )
            for d in (dict(r) for r in cur.fetchall())
        ]
        sol.add_revision(
            modifier,
            f"从方案元空间方案 {smeta_solution_id} 复制而来 "
            f"(仿真任务 {simulation_task_id}/{simulation_task_batch})",
        )
        return self.add(sol)

    # ------------------------------------------------------------------
    # 内部
    # ------------------------------------------------------------------
    def _upsert_main(self, sol: Solution) -> None:
        cur = self.cursor
        row = self._solution_to_row(sol)
        columns = list(row.keys())
        placeholders = ", ".join(["?"] * len(columns))
        updates = ", ".join(
            c + " = excluded." + c
            for c in columns
            if c not in (
                "id",
                "simulation_task_id",
                "simulation_task_batch",
            )
        )
        cur.execute(
            f"INSERT INTO {self.TABLE} ({', '.join(columns)}) VALUES ({placeholders}) "
            f"ON CONFLICT(id, simulation_task_id, simulation_task_batch) DO UPDATE SET {updates}",
            list(row.values()),
        )

    def _insert_revisions(self, sol: Solution) -> None:
        cur = self.cursor
        cur.execute(
            f"DELETE FROM {self.REV_TABLE} "
            f"WHERE solution_id = ? AND simulation_task_id = ? AND simulation_task_batch = ?",
            [sol.base.id, sol.simulation_task_id, sol.simulation_task_batch],
        )
        for r in sol.revisions:
            cur.execute(
                f"INSERT INTO {self.REV_TABLE} "
                f"(solution_id, simulation_task_id, simulation_task_batch, "
                f"revision_no, modifier, modified_at, change_summary) "
                f"VALUES (?, ?, ?, ?, ?, ?, ?)",
                [
                    sol.base.id,
                    sol.simulation_task_id,
                    sol.simulation_task_batch,
                    r.revision_no,
                    r.modifier,
                    r.modified_at,
                    r.change_summary,
                ],
            )

    def _load_revisions(self, sol: Solution) -> None:
        cur = self.cursor
        cur.execute(
            f"SELECT revision_no, modifier, modified_at, change_summary "
            f"FROM {self.REV_TABLE} "
            f"WHERE solution_id = ? AND simulation_task_id = ? AND simulation_task_batch = ? "
            f"ORDER BY revision_no ASC",
            [sol.base.id, sol.simulation_task_id, sol.simulation_task_batch],
        )
        sol.revisions = [
            RevisionRecord(
                revision_no=int(d["revision_no"]),
                modifier=d["modifier"],
                modified_at=d["modified_at"],
                change_summary=d["change_summary"],
            )
            for d in (dict(r) for r in cur.fetchall())
        ]

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
            "simulation_task_id": sol.simulation_task_id,
            "simulation_task_batch": sol.simulation_task_batch,
            "created_at": sol.created_at,
            "updated_at": sol.updated_at,
        }

    def _row_to_solution(
        self,
        row: Dict[str, Any],
        from_smeta: bool = False,
    ) -> Solution:
        base = SolutionBaseInfo(
            id="" if from_smeta else row["id"],
            solution_name=row["solution_name"],
            major_version=int(row["major_version"]),
            minor_version=int(row["minor_version"]),
            status=row.get("status") or SolutionStatus.DRAFT.value,
            category=row.get("category"),
            summary=row.get("summary"),
        )
        key = SolutionKeyInfo(
            purpose=_jloads(row.get("key_purpose"), default=[]),
            objectives=_jloads(row.get("key_objectives"), default=[]),
            measures=_jloads(row.get("key_measures"), default=[]),
            organizations=_jloads(row.get("key_organizations"), default=[]),
            personnel=_jloads(row.get("key_personnel"), default=[]),
            work_mechanism=row.get("key_work_mechanism"),
            work_content=row.get("key_work_content"),
            constraints=_jloads(row.get("key_constraints"), default=[]),
            risk_list=_jloads(row.get("key_risk_list"), default=[]),
            issue_list=_jloads(row.get("key_issue_list"), default=[]),
            notes=row.get("key_notes"),
        )
        doc = SolutionDocInfo(
            main_docs=_jloads(row.get("doc_main_docs"), default=[]),
            attachments=_jloads(row.get("doc_attachments"), default=[]),
            references=_jloads(row.get("doc_references"), default=[]),
        )
        sol = Solution(
            base=base,
            key=key,
            doc=doc,
            simulation_task_id="" if from_smeta else (row.get("simulation_task_id") or ""),
            simulation_task_batch="" if from_smeta else (row.get("simulation_task_batch") or ""),
            created_at=row.get("created_at") or _now_iso(),
            updated_at=row.get("updated_at") or _now_iso(),
        )
        return sol


