"""仿真虚空间 · 组织对象持久化服务 (SenvOrganizationService)

仿真虚空间 = 系统空间 + task_id(仿真任务ID) + batch_no(仿真任务批次号)。
所有操作均限定在同一个 (task_id, batch_no) 命名空间内。

额外提供批量复制接口:
  - load_from_ssys(root_id, task_id, batch_no, overwrite)
      从系统空间的某棵子树整棵复制进来
  - load_from_smeta(root_id, task_id, batch_no, overwrite)
      从方案元空间的某棵子树整棵复制进来
"""
from __future__ import annotations
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from data_storage_services.SQLite.sqlite_operator import SQLiteOperator
from data_storage_services.sql_db_services.ssys.organization_service import (
    SsysOrganizationService,
)
from data_storage_services.sql_db_services.smeta.organization_service import (
    SmetaOrganizationService,
)
from bo.senv.organization import Organization, OrganizationTreeNode


logger = logging.getLogger("SenvOrganizationService")


def _now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


class SenvOrganizationService:
    """仿真虚空间 · Organization 持久化服务。"""

    TABLE = "senv_organization"

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
        self._ssys_svc = None
        self._smeta_svc = None

    def __enter__(self) -> "SenvOrganizationService":
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
    def _insert_one(self, org: Organization) -> Optional[Organization]:
        """INSERT 一条记录; 唯一键冲突时吞掉 IntegrityError 返回 None."""
        org_dict = org.model_dump()
        org_dict.pop("id", None)
        columns = ", ".join(org_dict.keys())
        placeholders = ", ".join(["?"] * len(org_dict))
        try:
            self._op.cursor.execute(
                f"INSERT INTO {self.TABLE} ({columns}) VALUES ({placeholders})",
                list(org_dict.values()),
            )
            self._op.connection.commit()
        except Exception as ex:
            logger.debug("_insert_one skip: %s", ex)
            return None
        org.id = self._op.cursor.lastrowid
        return self.get_by_id(org.id)

    def add(self, org: Organization, strict: bool = False) -> Optional[Organization]:
        """插入一条记录。

        默认 strict=False: 若 (task_id, batch_no, org_code) 已存在, 返回已存在记录。
        strict=True: 强制 INSERT, 冲突时抛 IntegrityError。
        """
        if not org.created_at:
            org.created_at = _now_iso()
        org.updated_at = _now_iso()

        if not strict:
            existing = self.get_by_code(org.task_id, org.batch_no, org.org_code)
            if existing is not None:
                return existing
            return self._insert_one(org)

        org_dict = org.model_dump()
        org_dict.pop("id", None)
        columns = ", ".join(org_dict.keys())
        placeholders = ", ".join(["?"] * len(org_dict))
        self._op.cursor.execute(
            f"INSERT INTO {self.TABLE} ({columns}) VALUES ({placeholders})",
            list(org_dict.values()),
        )
        self._op.connection.commit()
        org.id = self._op.cursor.lastrowid
        return self.get_by_id(org.id)

    def get_by_id(self, oid: int) -> Optional[Organization]:
        self._op.cursor.execute(
            f"SELECT * FROM {self.TABLE} WHERE id = ?", [int(oid)]
        )
        row = self._op.cursor.fetchone()
        return self._from_row(dict(row)) if row else None

    def get_by_code(
        self, task_id: str, batch_no: str, org_code: str
    ) -> Optional[Organization]:
        self._op.cursor.execute(
            f"SELECT * FROM {self.TABLE} "
            f"WHERE task_id = ? AND batch_no = ? AND org_code = ?",
            [task_id, batch_no, org_code],
        )
        row = self._op.cursor.fetchone()
        return self._from_row(dict(row)) if row else None

    def update(self, org: Organization) -> Optional[Organization]:
        if org.id is None:
            return None
        org.updated_at = _now_iso()
        fields: List[str] = []
        values: List[Any] = []
        for k, v in org.model_dump().items():
            if k == "id":
                continue
            fields.append(f"{k} = ?")
            values.append(v)
        values.append(org.id)
        self._op.cursor.execute(
            f"UPDATE {self.TABLE} SET {', '.join(fields)} WHERE id = ?",
            values,
        )
        self._op.connection.commit()
        return self.get_by_id(org.id)

    def delete(self, oid: int, cascade: bool = True) -> bool:
        oid = int(oid)
        self._op.cursor.execute(
            f"SELECT id FROM {self.TABLE} WHERE parent_id = ?", [oid]
        )
        children = [dict(r)["id"] for r in self._op.cursor.fetchall()]
        if children and cascade:
            for cid in children:
                self.delete(cid, cascade=True)
        self._op.cursor.execute(f"DELETE FROM {self.TABLE} WHERE id = ?", [oid])
        self._op.connection.commit()
        return self._op.cursor.rowcount > 0

    def list_all(
        self,
        task_id: str,
        batch_no: str,
        parent_id: Optional[int] = None,
        status: Optional[str] = None,
        org_type: Optional[str] = None,
        keyword: Optional[str] = None,
        page: int = 1,
        page_size: int = 100,
    ) -> List[Organization]:
        clauses: List[str] = ["task_id = ?", "batch_no = ?"]
        params: List[Any] = [task_id, batch_no]
        if parent_id is None:
            clauses.append("parent_id IS NULL")
        else:
            clauses.append("parent_id = ?")
            params.append(int(parent_id))
        if status:
            clauses.append("status = ?")
            params.append(status)
        if org_type:
            clauses.append("org_type = ?")
            params.append(org_type)
        if keyword:
            clauses.append("(org_name LIKE ? OR org_code LIKE ?)")
            params += [f"%{keyword}%", f"%{keyword}%"]
        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        offset = max(0, (page - 1)) * page_size
        self._op.cursor.execute(
            f"SELECT * FROM {self.TABLE} {where} "
            f"ORDER BY sort_order ASC, id ASC LIMIT ? OFFSET ?",
            params + [page_size, offset],
        )
        return [self._from_row(dict(r)) for r in self._op.cursor.fetchall()]

    def list_roots(self, task_id: str, batch_no: str) -> List[Organization]:
        return self.list_all(task_id, batch_no, parent_id=None)

    def list_children(
        self, task_id: str, batch_no: str, parent_id: int
    ) -> List[Organization]:
        return self.list_all(task_id, batch_no, parent_id=parent_id)

    def get_parent(
        self, task_id: str, batch_no: str, oid: int
    ) -> Optional[Organization]:
        org = self.get_by_id(oid)
        if org is None or org.parent_id is None:
            return None
        return self.get_by_id(org.parent_id)

    def list_ancestors(
        self, task_id: str, batch_no: str, oid: int
    ) -> List[Organization]:
        ancestors: List[Organization] = []
        current = self.get_by_id(oid)
        while current is not None and current.parent_id is not None:
            current = self.get_by_id(current.parent_id)
            if current is not None:
                ancestors.append(current)
        return ancestors

    def search_by_name(
        self, task_id: str, batch_no: str, keyword: str
    ) -> List[Organization]:
        return self.list_all(task_id, batch_no, keyword=keyword)

    def count(
        self,
        task_id: str,
        batch_no: str,
        parent_id: Optional[int] = None,
        status: Optional[str] = None,
        org_type: Optional[str] = None,
        keyword: Optional[str] = None,
    ) -> int:
        clauses: List[str] = ["task_id = ?", "batch_no = ?"]
        params: List[Any] = [task_id, batch_no]
        if parent_id is None:
            clauses.append("parent_id IS NULL")
        else:
            clauses.append("parent_id = ?")
            params.append(int(parent_id))
        if status:
            clauses.append("status = ?")
            params.append(status)
        if org_type:
            clauses.append("org_type = ?")
            params.append(org_type)
        if keyword:
            clauses.append("(org_name LIKE ? OR org_code LIKE ?)")
            params += [f"%{keyword}%", f"%{keyword}%"]
        return self._run_count(" AND ".join(clauses), params)

    def _run_count(self, where_sql: str, params: List[Any]) -> int:
        sql = f"SELECT COUNT(*) AS cnt FROM {self.TABLE}"
        if where_sql:
            sql += f" WHERE {where_sql}"
        self._op.cursor.execute(sql, params)
        row = self._op.cursor.fetchone()
        return int(dict(row)["cnt"]) if row else 0

    def _from_row(self, row: Dict[str, Any]) -> Organization:
        org = Organization(**row)
        if org.parent_id is not None:
            p = self.get_by_id(org.parent_id)
            if p is not None:
                org.parent_name = p.org_name
        return org

    # ---------- 批量 / 导入导出 ----------
    def batch_add(self, orgs: List[Organization]) -> List[Organization]:
        return [self.add(o) for o in orgs]

    def export_to_json(
        self, task_id: str, batch_no: str, filepath: str
    ) -> None:
        self._op.cursor.execute(
            f"SELECT * FROM {self.TABLE} "
            f"WHERE task_id = ? AND batch_no = ? "
            f"ORDER BY id ASC",
            [task_id, batch_no],
        )
        rows = [dict(r) for r in self._op.cursor.fetchall()]
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=2)

    def import_from_json(
        self,
        task_id: str,
        batch_no: str,
        filepath: str,
        overwrite: bool = False,
    ) -> int:
        with open(filepath, "r", encoding="utf-8") as f:
            rows = json.load(f)
        if overwrite:
            self._op.cursor.execute(
                f"DELETE FROM {self.TABLE} "
                f"WHERE task_id = ? AND batch_no = ?",
                [task_id, batch_no],
            )
            self._op.connection.commit()
        n = 0
        for r in rows:
            r.pop("id", None)
            r["task_id"] = task_id
            r["batch_no"] = batch_no
            try:
                columns = ", ".join(r.keys())
                placeholders = ", ".join(["?"] * len(r))
                self._op.cursor.execute(
                    f"INSERT INTO {self.TABLE} ({columns}) VALUES ({placeholders})",
                    list(r.values()),
                )
                n += 1
            except Exception as ex:
                logger.warning("import row skip: %s", ex)
        self._op.connection.commit()
        return n

    # ---------- 方案空间专用: 从系统空间 / 方案元空间整棵复制 ----------
    def load_from_ssys(
        self,
        root_id: int,
        task_id: str,
        batch_no: str,
        overwrite: bool = False,
    ) -> int:
        """从系统空间的某棵子树整棵复制进仿真虚空间, 统一设置任务属性."""
        if self._ssys_svc is None:
            self._ssys_svc = SsysOrganizationService(operator=self._op)
        ssys_tree = self._ssys_svc.build_organization_tree(root_id)
        if ssys_tree is None:
            return 0
        if overwrite:
            self._op.cursor.execute(
                f"DELETE FROM {self.TABLE} "
                f"WHERE task_id = ? AND batch_no = ?",
                [task_id, batch_no],
            )
            self._op.connection.commit()
        counter = {"n": 0}
        self._copy_subtree_from_ssys(
            ssys_tree, task_id=task_id, batch_no=batch_no, counter=counter
        )
        return counter["n"]

    def load_from_smeta(
        self,
        root_id: int,
        task_id: str,
        batch_no: str,
        overwrite: bool = False,
    ) -> int:
        """从方案元空间的某棵子树整棵复制进仿真虚空间, 统一设置任务属性."""
        if self._smeta_svc is None:
            self._smeta_svc = SmetaOrganizationService(operator=self._op)
        smeta_tree = self._smeta_svc.build_organization_tree(root_id)
        if smeta_tree is None:
            return 0
        if overwrite:
            self._op.cursor.execute(
                f"DELETE FROM {self.TABLE} "
                f"WHERE task_id = ? AND batch_no = ?",
                [task_id, batch_no],
            )
            self._op.connection.commit()
        counter = {"n": 0}
        self._copy_subtree_from_smeta(
            smeta_tree, task_id=task_id, batch_no=batch_no, counter=counter
        )
        return counter["n"]

    def _copy_subtree_from_ssys(
        self,
        ssys_node,
        task_id: str,
        batch_no: str,
        parent_id: Optional[int] = None,
        counter: Optional[Dict[str, int]] = None,
    ) -> None:
        if counter is None:
            counter = {"n": 0}
        now = _now_iso()
        org = Organization(
            task_id=task_id,
            batch_no=batch_no,
            org_code=ssys_node.org_code,
            org_name=ssys_node.org_name,
            org_type=ssys_node.org_type,
            description=ssys_node.description,
            parent_id=parent_id,
            parent_name=None,
            sort_order=ssys_node.sort_order,
            status=ssys_node.status,
            extra_info=None,
            created_at=now,
            updated_at=now,
        )
        inserted = self._insert_one(org)
        if inserted is not None:
            counter["n"] += 1
            for ch in ssys_node.children:
                self._copy_subtree_from_ssys(
                    ch,
                    task_id=task_id,
                    batch_no=batch_no,
                    parent_id=inserted.id,
                    counter=counter,
                )

    def _copy_subtree_from_smeta(
        self,
        smeta_node,
        task_id: str,
        batch_no: str,
        parent_id: Optional[int] = None,
        counter: Optional[Dict[str, int]] = None,
    ) -> None:
        if counter is None:
            counter = {"n": 0}
        now = _now_iso()
        extra_info = None
        if smeta_node.extra_info:
            try:
                extra_info = json.dumps(smeta_node.extra_info, ensure_ascii=False)
            except Exception:
                extra_info = None
        org = Organization(
            task_id=task_id,
            batch_no=batch_no,
            org_code=smeta_node.org_code,
            org_name=smeta_node.org_name,
            org_type=smeta_node.org_type,
            description=smeta_node.description,
            parent_id=parent_id,
            parent_name=None,
            sort_order=smeta_node.sort_order,
            status=smeta_node.status,
            extra_info=extra_info,
            created_at=now,
            updated_at=now,
        )
        inserted = self._insert_one(org)
        if inserted is not None:
            counter["n"] += 1
            for ch in smeta_node.children:
                self._copy_subtree_from_smeta(
                    ch,
                    task_id=task_id,
                    batch_no=batch_no,
                    parent_id=inserted.id,
                    counter=counter,
                )

    # ---------- 构建组织树 ----------
    def _fetch_descendants(self, root_id: int) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        self._op.cursor.execute(
            f"SELECT * FROM {self.TABLE} WHERE id = ?", [int(root_id)]
        )
        root_rows = [dict(r) for r in self._op.cursor.fetchall()]
        if not root_rows:
            return []
        rows.extend(root_rows)
        seen_ids: set = {int(root_id)}
        frontier: set = {int(root_id)}
        depth = 0
        while frontier and depth < 128:
            depth += 1
            p_frontier = ",".join(["?"] * len(frontier))
            seen_placeholders = ",".join(["?"] * len(seen_ids))
            sql = (
                f"SELECT * FROM {self.TABLE} "
                f"WHERE parent_id IN ({p_frontier}) "
                f"AND id NOT IN ({seen_placeholders}) "
                f"ORDER BY sort_order ASC, id ASC"
            )
            self._op.cursor.execute(sql, list(frontier) + list(seen_ids))
            child_rows = [dict(r) for r in self._op.cursor.fetchall()]
            if not child_rows:
                break
            rows.extend(child_rows)
            seen_ids.update(int(r["id"]) for r in child_rows)
            frontier = {int(r["id"]) for r in child_rows}
        return rows

    def _fetch_all_rows(
        self, task_id: str, batch_no: str
    ) -> List[Dict[str, Any]]:
        self._op.cursor.execute(
            f"SELECT * FROM {self.TABLE} "
            f"WHERE task_id = ? AND batch_no = ? "
            f"ORDER BY parent_id ASC, sort_order ASC, id ASC",
            [task_id, batch_no],
        )
        return [dict(r) for r in self._op.cursor.fetchall()]

    def _rows_to_subtree(
        self,
        rows: List[Dict[str, Any]],
        root_id: int,
    ) -> Optional[OrganizationTreeNode]:
        by_id: Dict[int, OrganizationTreeNode] = {}
        for r in rows:
            org = self._from_row(r)
            if org is None or org.id is None:
                continue
            node = OrganizationTreeNode.from_org(org)
            by_id[node.id] = node

        children_map: Dict[int, List[int]] = {}
        for node in by_id.values():
            if node.parent_id is not None and node.parent_id in by_id:
                children_map.setdefault(node.parent_id, []).append(node.id)

        def attach(nid: int) -> None:
            node = by_id.get(nid)
            if node is None:
                return
            child_ids = children_map.get(nid, [])
            child_ids.sort(key=lambda cid: (by_id[cid].sort_order, cid))
            node.children = []
            for cid in child_ids:
                child = by_id.get(cid)
                if child is None:
                    continue
                node.children.append(child)
                attach(cid)

        root_node = by_id.get(int(root_id))
        if root_node is None:
            return None
        attach(int(root_node.id))
        return root_node

    def build_organization_tree(
        self,
        root_id: int,
    ) -> Optional[OrganizationTreeNode]:
        root = self.get_by_id(root_id)
        if root is None:
            return None
        rows = self._fetch_descendants(root_id=root_id)
        return self._rows_to_subtree(rows, root_id)

    def build_full_tree(
        self, task_id: str, batch_no: str
    ) -> List[OrganizationTreeNode]:
        rows = self._fetch_all_rows(task_id, batch_no)
        if not rows:
            return []
        by_id: Dict[int, OrganizationTreeNode] = {}
        for r in rows:
            org = self._from_row(r)
            if org is None:
                continue
            node = OrganizationTreeNode.from_org(org)
            by_id[node.id] = node
        children_map: Dict[int, List[int]] = {}
        roots: List[OrganizationTreeNode] = []
        for node in by_id.values():
            if node.parent_id is None or node.parent_id not in by_id:
                roots.append(node)
            else:
                children_map.setdefault(node.parent_id, []).append(node.id)

        def attach(nid: int) -> None:
            node = by_id.get(nid)
            if node is None:
                return
            child_ids = children_map.get(nid, [])
            child_ids.sort(key=lambda cid: (by_id[cid].sort_order, cid))
            node.children = []
            for cid in child_ids:
                child = by_id.get(cid)
                if child is None:
                    continue
                node.children.append(child)
                attach(cid)

        for r in roots:
            attach(r.id)
        roots.sort(key=lambda n: (n.sort_order, n.id))
        return roots

    def build_tree_as_dict(self, root_id: int) -> Optional[Dict[str, Any]]:
        tree = self.build_organization_tree(root_id)
        return tree.to_dict() if tree else None

    def build_tree_as_json(self, root_id: int, indent: int = 2) -> Optional[str]:
        tree = self.build_organization_tree(root_id)
        return tree.to_json(indent=indent) if tree else None
