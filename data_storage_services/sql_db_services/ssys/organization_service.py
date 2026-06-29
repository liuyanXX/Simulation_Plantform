"""系统空间 · 组织对象持久化服务 (SsysOrganizationService)

直接调用 SQLiteOperator (execute) 进行 ssys_organization 表的增、删、改、查。

查询支持:
  - 按ID查本身            get_by_id(oid)
  - 按组织编码查本身      get_by_code(code)
  - 按名称模糊查          search_by_name(keyword)
  - 查全量               list_all(...)
  - 查顶级组织(无父)     list_roots()
  - 查下级组织           list_children(parent_id)
  - 查上级组织(链)       list_ancestors(oid) / get_parent(oid)
"""
from __future__ import annotations
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from data_storage_services.SQLite.sqlite_operator import SQLiteOperator
from bo.ssys.organization import Organization, OrganizationTreeNode


logger = logging.getLogger("SsysOrganizationService")


def _now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


class SsysOrganizationService:
    """系统空间 · Organization 持久化服务。"""

    TABLE = "ssys_organization"

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

    def __enter__(self) -> "SsysOrganizationService":
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
    def add(self, org: Organization) -> Organization:
        org.touch_created()
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

    def get_by_code(self, code: str) -> Optional[Organization]:
        self._op.cursor.execute(
            f"SELECT * FROM {self.TABLE} WHERE org_code = ?", [code]
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
        parent_id: Optional[int] = None,
        status: Optional[str] = None,
        org_type: Optional[str] = None,
        keyword: Optional[str] = None,
        page: int = 1,
        page_size: int = 100,
    ) -> List[Organization]:
        clauses: List[str] = []
        params: List[Any] = []
        if parent_id is None:
            clauses.append("parent_id IS NULL")
        elif parent_id == -1:
            pass
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
            f"SELECT * FROM {self.TABLE} {where} ORDER BY sort_order ASC, id ASC LIMIT ? OFFSET ?",
            params + [page_size, offset],
        )
        return [self._from_row(dict(r)) for r in self._op.cursor.fetchall()]

    def list_roots(self) -> List[Organization]:
        return self.list_all(parent_id=None)

    def list_children(self, parent_id: int) -> List[Organization]:
        return self.list_all(parent_id=parent_id)

    def get_parent(self, oid: int) -> Optional[Organization]:
        org = self.get_by_id(oid)
        if org is None or org.parent_id is None:
            return None
        return self.get_by_id(org.parent_id)

    def list_ancestors(self, oid: int) -> List[Organization]:
        ancestors: List[Organization] = []
        current = self.get_by_id(oid)
        while current is not None and current.parent_id is not None:
            current = self.get_by_id(current.parent_id)
            if current is not None:
                ancestors.append(current)
        return ancestors

    def search_by_name(self, keyword: str) -> List[Organization]:
        return self.list_all(keyword=keyword)

    def count(
        self,
        parent_id: Optional[int] = None,
        status: Optional[str] = None,
        org_type: Optional[str] = None,
        keyword: Optional[str] = None,
    ) -> int:
        clauses: List[str] = []
        params: List[Any] = []
        if parent_id is None:
            clauses.append("parent_id IS NULL")
        elif parent_id == -1:
            pass
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

    def export_to_json(self, filepath: str) -> None:
        self._op.cursor.execute(f"SELECT * FROM {self.TABLE} ORDER BY id ASC")
        rows = [dict(r) for r in self._op.cursor.fetchall()]
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=2)

    def import_from_json(self, filepath: str) -> int:
        with open(filepath, "r", encoding="utf-8") as f:
            rows = json.load(f)
        n = 0
        for r in rows:
            r.pop("id", None)
            try:
                self._op.cursor.execute(
                    f"INSERT INTO {self.TABLE} ({', '.join(r.keys())}) VALUES ({', '.join(['?']*len(r))})",
                    list(r.values()),
                )
                n += 1
            except Exception as ex:
                logger.warning("import row skip: %s", ex)
        self._op.connection.commit()
        return n

    # ---------- 构建组织树 ----------
    def _fetch_descendants(
        self,
        root_id: int,
    ) -> List[Dict[str, Any]]:
        """以 root_id 为根, 分层向下拉取整棵子树的扁平节点行(含根)。"""
        rows: List[Dict[str, Any]] = []
        self._op.cursor.execute(
            "SELECT * FROM ssys_organization WHERE id = ?", [int(root_id)]
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
                f"SELECT * FROM ssys_organization "
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

    def _fetch_all_rows(self) -> List[Dict[str, Any]]:
        self._op.cursor.execute(
            "SELECT * FROM ssys_organization ORDER BY parent_id ASC, sort_order ASC, id ASC"
        )
        return [dict(r) for r in self._op.cursor.fetchall()]

    def _rows_to_subtree(
        self,
        rows: List[Dict[str, Any]],
        root_id: int,
    ) -> Optional[OrganizationTreeNode]:
        """把扁平行列表组装成以 root_id 为根的一棵子树。"""
        by_id: Dict[int, OrganizationTreeNode] = {}
        for r in rows:
            node = OrganizationTreeNode.from_org(
                Organization(**self._from_row(r).__dict__)
            )
            by_id[node.id] = node

        children_map: Dict[int, List[int]] = {}
        for node in by_id.values():
            if node.parent_id is None:
                continue
            if node.parent_id in by_id:
                children_map.setdefault(node.parent_id, []).append(node.id)

        def attach(nid: int) -> None:
            node = by_id.get(nid)
            if node is None:
                return
            child_ids = children_map.get(nid, [])
            child_ids.sort(
                key=lambda cid: (
                    by_id[cid].sort_order if cid in by_id else 0,
                    cid,
                )
            )
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
        children_map.setdefault(int(root_id), []).sort(
            key=lambda cid: (by_id[cid].sort_order, cid)
        )
        attach(int(root_id))
        return root_node

    def build_organization_tree(
        self,
        root_id: int,
    ) -> Optional[OrganizationTreeNode]:
        """以某个组织对象为根节点, 构建出一棵完整的组织树。"""
        root = self.get_by_id(root_id)
        if root is None:
            return None
        rows = self._fetch_descendants(root_id=root_id)
        return self._rows_to_subtree(rows, root_id)

    def build_full_tree(self) -> List[OrganizationTreeNode]:
        """构建整库所有顶级组织各自的完整子树。"""
        rows = self._fetch_all_rows()
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
            child_ids.sort(
                key=lambda cid: (
                    by_id[cid].sort_order if cid in by_id else 0,
                    cid,
                )
            )
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
