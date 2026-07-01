"""知识空间 · 指标管理库持久化服务 (KmIndicatorService)

对应表:
  - km_indicator_category   指标分类分级目录 (树形)
  - km_indicator_info       通用指标主表
  - km_indicator_attach     指标配套附件标准表

逗号分隔字符串字段 (scene_tag / tag_list) 在 DB 中以 varchar 存储;
Service 层透明地在 List[str] 与逗号分隔字符串之间转换。
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from data_storage_services.SQLite.sqlite_operator import SQLiteOperator
from bo.km.indicator import (
    Indicator,
    IndicatorAttach,
    IndicatorCategory,
)


logger = logging.getLogger("KmIndicatorService")


def _join_tags(tags: Optional[List[str]]) -> str:
    if not tags:
        return ""
    return ",".join(str(t).strip() for t in tags if str(t).strip())


def _split_tags(raw: Any) -> List[str]:
    if raw is None or raw == "":
        return []
    if isinstance(raw, list):
        return [str(t).strip() for t in raw if str(t).strip()]
    return [t.strip() for t in str(raw).split(",") if t.strip()]


class KmIndicatorService:
    """指标管理库持久化服务 (分类 / 指标 / 附件)。"""

    CATEGORY_TABLE = "km_indicator_category"
    INDICATOR_TABLE = "km_indicator_info"
    ATTACH_TABLE = "km_indicator_attach"

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

    def __enter__(self) -> "KmIndicatorService":
        return self

    def __exit__(self, *args: Any) -> None:
        self._op.disconnect()

    @property
    def cursor(self):
        return self._op.cursor

    @property
    def connection(self):
        return self._op.connection

    # ==================================================================
    # 指标分类分级目录
    # ==================================================================
    def add_category(self, category: IndicatorCategory) -> IndicatorCategory:
        cur = self.cursor
        cur.execute(
            f"SELECT 1 FROM {self.CATEGORY_TABLE} WHERE category_code = ?",
            [category.category_code],
        )
        if cur.fetchone() is not None:
            raise ValueError(f"分类编码已存在: {category.category_code}")
        cur.execute(
            f"INSERT INTO {self.CATEGORY_TABLE} "
            f"(parent_id, category_name, category_code, level, sort, scene_tag, remark, status, create_time, update_time) "
            f"VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                category.parent_id,
                category.category_name,
                category.category_code,
                category.level,
                category.sort,
                _join_tags(category.scene_tag),
                category.remark,
                category.status,
                category.create_time,
                category.update_time,
            ],
        )
        self.connection.commit()
        category.category_id = cur.lastrowid
        return category

    def update_category(self, category: IndicatorCategory) -> IndicatorCategory:
        if category.category_id is None:
            raise ValueError("update_category 需要 category_id")
        from bo.km.indicator import _now_iso

        category.update_time = _now_iso()
        cur = self.cursor
        cur.execute(
            f"UPDATE {self.CATEGORY_TABLE} SET "
            f"parent_id = ?, category_name = ?, category_code = ?, level = ?, sort = ?, "
            f"scene_tag = ?, remark = ?, status = ?, update_time = ? "
            f"WHERE category_id = ?",
            [
                category.parent_id,
                category.category_name,
                category.category_code,
                category.level,
                category.sort,
                _join_tags(category.scene_tag),
                category.remark,
                category.status,
                category.update_time,
                category.category_id,
            ],
        )
        self.connection.commit()
        return category

    def delete_category(self, category_id: int) -> bool:
        """删除分类。存在子分类或挂载指标时禁止删除。"""
        cur = self.cursor
        cur.execute(
            f"SELECT COUNT(*) AS cnt FROM {self.CATEGORY_TABLE} WHERE parent_id = ?",
            [category_id],
        )
        if int(dict(cur.fetchone())["cnt"]) > 0:
            raise ValueError("存在子分类, 无法删除")
        cur.execute(
            f"SELECT COUNT(*) AS cnt FROM {self.INDICATOR_TABLE} WHERE category_id = ?",
            [category_id],
        )
        if int(dict(cur.fetchone())["cnt"]) > 0:
            raise ValueError("分类下存在指标, 无法删除")
        cur.execute(f"DELETE FROM {self.CATEGORY_TABLE} WHERE category_id = ?", [category_id])
        self.connection.commit()
        return cur.rowcount > 0

    def get_category(self, category_id: int) -> Optional[IndicatorCategory]:
        cur = self.cursor
        cur.execute(f"SELECT * FROM {self.CATEGORY_TABLE} WHERE category_id = ?", [category_id])
        row = cur.fetchone()
        return self._row_to_category(dict(row)) if row else None

    def list_categories(
        self,
        *,
        parent_id: Optional[int] = None,
        status: Optional[int] = None,
    ) -> List[IndicatorCategory]:
        clauses: List[str] = []
        params: List[Any] = []
        if parent_id is not None:
            clauses.append("parent_id = ?")
            params.append(parent_id)
        if status is not None:
            clauses.append("status = ?")
            params.append(status)
        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        cur = self.cursor
        cur.execute(
            f"SELECT * FROM {self.CATEGORY_TABLE} {where} ORDER BY level ASC, sort ASC, category_id ASC",
            params,
        )
        return [self._row_to_category(dict(r)) for r in cur.fetchall()]

    def build_category_tree(self, status: Optional[int] = None) -> List[Dict[str, Any]]:
        """构建完整分类树 (返回嵌套 dict, children 字段承载子节点)。"""
        cats = self.list_categories(status=status)
        nodes: Dict[int, Dict[str, Any]] = {}
        for c in cats:
            d = c.model_dump()
            d["children"] = []
            nodes[c.category_id] = d
        roots: List[Dict[str, Any]] = []
        for cid, node in nodes.items():
            pid = node.get("parent_id", 0)
            if pid and pid in nodes:
                nodes[pid]["children"].append(node)
            else:
                roots.append(node)
        return roots

    # ==================================================================
    # 通用指标
    # ==================================================================
    def add_indicator(self, indicator: Indicator) -> Indicator:
        cur = self.cursor
        cur.execute(
            f"SELECT 1 FROM {self.INDICATOR_TABLE} WHERE indicator_code = ?",
            [indicator.indicator_code],
        )
        if cur.fetchone() is not None:
            raise ValueError(f"指标编码已存在: {indicator.indicator_code}")
        cur.execute(
            f"INSERT INTO {self.INDICATOR_TABLE} "
            f"(category_id, indicator_name, indicator_code, indicator_desc, data_type, unit, "
            f"standard_value, min_threshold, max_threshold, positive_flag, default_score_rule_id, "
            f"tag_list, version, status, create_user, create_time, update_time) "
            f"VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                indicator.category_id,
                indicator.indicator_name,
                indicator.indicator_code,
                indicator.indicator_desc,
                indicator.data_type,
                indicator.unit,
                indicator.standard_value,
                indicator.min_threshold,
                indicator.max_threshold,
                indicator.positive_flag,
                indicator.default_score_rule_id,
                _join_tags(indicator.tag_list),
                indicator.version,
                indicator.status,
                indicator.create_user,
                indicator.create_time,
                indicator.update_time,
            ],
        )
        self.connection.commit()
        indicator.indicator_id = cur.lastrowid
        return indicator

    def update_indicator(self, indicator: Indicator) -> Indicator:
        if indicator.indicator_id is None:
            raise ValueError("update_indicator 需要 indicator_id")
        from bo.km.indicator import _now_iso

        indicator.update_time = _now_iso()
        cur = self.cursor
        cur.execute(
            f"UPDATE {self.INDICATOR_TABLE} SET "
            f"category_id = ?, indicator_name = ?, indicator_code = ?, indicator_desc = ?, "
            f"data_type = ?, unit = ?, standard_value = ?, min_threshold = ?, max_threshold = ?, "
            f"positive_flag = ?, default_score_rule_id = ?, tag_list = ?, version = ?, status = ?, "
            f"create_user = ?, update_time = ? "
            f"WHERE indicator_id = ?",
            [
                indicator.category_id,
                indicator.indicator_name,
                indicator.indicator_code,
                indicator.indicator_desc,
                indicator.data_type,
                indicator.unit,
                indicator.standard_value,
                indicator.min_threshold,
                indicator.max_threshold,
                indicator.positive_flag,
                indicator.default_score_rule_id,
                _join_tags(indicator.tag_list),
                indicator.version,
                indicator.status,
                indicator.create_user,
                indicator.update_time,
                indicator.indicator_id,
            ],
        )
        self.connection.commit()
        return indicator

    def delete_indicator(self, indicator_id: int) -> bool:
        """删除指标, 同时清理其配套附件。"""
        cur = self.cursor
        cur.execute(f"DELETE FROM {self.ATTACH_TABLE} WHERE indicator_id = ?", [indicator_id])
        cur.execute(f"DELETE FROM {self.INDICATOR_TABLE} WHERE indicator_id = ?", [indicator_id])
        self.connection.commit()
        return cur.rowcount > 0

    def get_indicator(self, indicator_id: int) -> Optional[Indicator]:
        cur = self.cursor
        cur.execute(f"SELECT * FROM {self.INDICATOR_TABLE} WHERE indicator_id = ?", [indicator_id])
        row = cur.fetchone()
        return self._row_to_indicator(dict(row)) if row else None

    def get_indicator_by_code(self, indicator_code: str) -> Optional[Indicator]:
        cur = self.cursor
        cur.execute(f"SELECT * FROM {self.INDICATOR_TABLE} WHERE indicator_code = ?", [indicator_code])
        row = cur.fetchone()
        return self._row_to_indicator(dict(row)) if row else None

    def list_indicators(
        self,
        *,
        category_id: Optional[int] = None,
        status: Optional[int] = None,
        data_type: Optional[int] = None,
        keyword: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Indicator]:
        clauses: List[str] = []
        params: List[Any] = []
        if category_id is not None:
            clauses.append("category_id = ?")
            params.append(category_id)
        if status is not None:
            clauses.append("status = ?")
            params.append(status)
        if data_type is not None:
            clauses.append("data_type = ?")
            params.append(data_type)
        if keyword:
            like = f"%{keyword}%"
            clauses.append("(indicator_name LIKE ? OR indicator_code LIKE ? OR indicator_desc LIKE ? OR tag_list LIKE ?)")
            params.extend([like, like, like, like])
        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        cur = self.cursor
        cur.execute(
            f"SELECT * FROM {self.INDICATOR_TABLE} {where} ORDER BY update_time DESC LIMIT ? OFFSET ?",
            params + [limit, offset],
        )
        return [self._row_to_indicator(dict(r)) for r in cur.fetchall()]

    def count_indicators(
        self,
        *,
        category_id: Optional[int] = None,
        status: Optional[int] = None,
        data_type: Optional[int] = None,
        keyword: Optional[str] = None,
    ) -> int:
        clauses: List[str] = []
        params: List[Any] = []
        if category_id is not None:
            clauses.append("category_id = ?")
            params.append(category_id)
        if status is not None:
            clauses.append("status = ?")
            params.append(status)
        if data_type is not None:
            clauses.append("data_type = ?")
            params.append(data_type)
        if keyword:
            like = f"%{keyword}%"
            clauses.append("(indicator_name LIKE ? OR indicator_code LIKE ? OR indicator_desc LIKE ? OR tag_list LIKE ?)")
            params.extend([like, like, like, like])
        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        cur = self.cursor
        cur.execute(f"SELECT COUNT(*) AS cnt FROM {self.INDICATOR_TABLE} {where}", params)
        row = cur.fetchone()
        return int(dict(row)["cnt"]) if row else 0

    # ==================================================================
    # 指标配套附件
    # ==================================================================
    def add_attach(self, attach: IndicatorAttach) -> IndicatorAttach:
        cur = self.cursor
        cur.execute(
            f"INSERT INTO {self.ATTACH_TABLE} "
            f"(indicator_id, file_name, file_url, attach_type, create_time) "
            f"VALUES (?, ?, ?, ?, ?)",
            [
                attach.indicator_id,
                attach.file_name,
                attach.file_url,
                attach.attach_type,
                attach.create_time,
            ],
        )
        self.connection.commit()
        attach.attach_id = cur.lastrowid
        return attach

    def delete_attach(self, attach_id: int) -> bool:
        cur = self.cursor
        cur.execute(f"DELETE FROM {self.ATTACH_TABLE} WHERE attach_id = ?", [attach_id])
        self.connection.commit()
        return cur.rowcount > 0

    def list_attaches(self, indicator_id: int) -> List[IndicatorAttach]:
        cur = self.cursor
        cur.execute(
            f"SELECT * FROM {self.ATTACH_TABLE} WHERE indicator_id = ? ORDER BY attach_id ASC",
            [indicator_id],
        )
        return [self._row_to_attach(dict(r)) for r in cur.fetchall()]

    # ==================================================================
    # 行 -> 业务对象
    # ==================================================================
    def _row_to_category(self, row: Dict[str, Any]) -> IndicatorCategory:
        return IndicatorCategory(
            category_id=row["category_id"],
            parent_id=int(row.get("parent_id") or 0),
            category_name=row["category_name"],
            category_code=row["category_code"],
            level=int(row.get("level") or 1),
            sort=int(row.get("sort") or 0),
            scene_tag=_split_tags(row.get("scene_tag")),
            remark=row.get("remark"),
            status=int(row.get("status") if row.get("status") is not None else 1),
            create_time=row["create_time"],
            update_time=row["update_time"],
        )

    def _row_to_indicator(self, row: Dict[str, Any]) -> Indicator:
        return Indicator(
            indicator_id=row["indicator_id"],
            category_id=int(row["category_id"]),
            indicator_name=row["indicator_name"],
            indicator_code=row["indicator_code"],
            indicator_desc=row.get("indicator_desc"),
            data_type=int(row.get("data_type") or 1),
            unit=row.get("unit"),
            standard_value=row.get("standard_value"),
            min_threshold=row.get("min_threshold"),
            max_threshold=row.get("max_threshold"),
            positive_flag=int(row.get("positive_flag") if row.get("positive_flag") is not None else 1),
            default_score_rule_id=row.get("default_score_rule_id"),
            tag_list=_split_tags(row.get("tag_list")),
            version=int(row.get("version") or 1),
            status=int(row.get("status") if row.get("status") is not None else 1),
            create_user=row.get("create_user"),
            create_time=row["create_time"],
            update_time=row["update_time"],
        )

    def _row_to_attach(self, row: Dict[str, Any]) -> IndicatorAttach:
        return IndicatorAttach(
            attach_id=row["attach_id"],
            indicator_id=int(row["indicator_id"]),
            file_name=row["file_name"],
            file_url=row["file_url"],
            attach_type=int(row.get("attach_type") or 1),
            create_time=row["create_time"],
        )
