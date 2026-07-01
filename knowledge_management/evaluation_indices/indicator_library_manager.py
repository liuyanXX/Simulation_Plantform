"""知识空间 · 指标管理库业务管理逻辑

IndicatorLibraryManager 面向业务层, 封装指标分类树 / 通用指标 / 配套附件的
增删改查与校验规则, 底层通过 KmIndicatorService 操作 km_ 数据表。

设计要点:
  - 业务层负责编排与校验 (编码唯一性由 Service 层兜底, 这里补充友好提示与关系校验)。
  - 每次调用按需创建 Service (短连接), 与项目现有 router 使用风格保持一致。
  - 底层通过 KmIndicatorService 操作 km_ 数据表, 独立于其它模块。
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from data_storage_services.sql_db_services.km.indicator_service import KmIndicatorService
from bo.km.indicator import (
    Indicator,
    IndicatorAttach,
    IndicatorCategory,
    new_category,
    new_indicator,
)

logger = logging.getLogger("IndicatorLibraryManager")


class IndicatorLibraryManager:
    """指标管理库业务管理器。"""

    def __init__(
        self,
        db_path: Optional[str] = None,
        db_name: Optional[str] = None,
    ) -> None:
        self._db_path = db_path
        self._db_name = db_name

    def _svc(self) -> KmIndicatorService:
        return KmIndicatorService(db_path=self._db_path, db_name=self._db_name)

    # ==================================================================
    # 分类分级目录
    # ==================================================================
    def create_category(
        self,
        category_name: str,
        category_code: str,
        parent_id: int = 0,
        level: Optional[int] = None,
        sort: int = 0,
        scene_tag: Optional[List[str]] = None,
        remark: Optional[str] = None,
        status: int = 1,
    ) -> IndicatorCategory:
        svc = self._svc()
        try:
            # 父分类校验 + 自动推导层级
            resolved_level = level
            if parent_id and parent_id != 0:
                parent = svc.get_category(parent_id)
                if parent is None:
                    raise ValueError(f"父分类不存在: {parent_id}")
                if resolved_level is None:
                    resolved_level = int(parent.level) + 1
            elif resolved_level is None:
                resolved_level = 1
            category = new_category(
                category_name=category_name,
                category_code=category_code,
                parent_id=parent_id,
                level=resolved_level,
                sort=sort,
                scene_tag=scene_tag,
                remark=remark,
            )
            category.status = status
            return svc.add_category(category)
        finally:
            svc._op.disconnect()

    def update_category(self, category_id: int, **fields: Any) -> IndicatorCategory:
        svc = self._svc()
        try:
            existing = svc.get_category(category_id)
            if existing is None:
                raise ValueError(f"分类不存在: {category_id}")
            for key, value in fields.items():
                if value is not None and hasattr(existing, key):
                    setattr(existing, key, value)
            return svc.update_category(existing)
        finally:
            svc._op.disconnect()

    def delete_category(self, category_id: int) -> bool:
        svc = self._svc()
        try:
            return svc.delete_category(category_id)
        finally:
            svc._op.disconnect()

    def get_category(self, category_id: int) -> Optional[IndicatorCategory]:
        svc = self._svc()
        try:
            return svc.get_category(category_id)
        finally:
            svc._op.disconnect()

    def list_categories(
        self,
        parent_id: Optional[int] = None,
        status: Optional[int] = None,
    ) -> List[IndicatorCategory]:
        svc = self._svc()
        try:
            return svc.list_categories(parent_id=parent_id, status=status)
        finally:
            svc._op.disconnect()

    def get_category_tree(self, status: Optional[int] = None) -> List[Dict[str, Any]]:
        svc = self._svc()
        try:
            return svc.build_category_tree(status=status)
        finally:
            svc._op.disconnect()

    # ==================================================================
    # 通用指标
    # ==================================================================
    def create_indicator(
        self,
        category_id: int,
        indicator_name: str,
        indicator_code: str,
        **fields: Any,
    ) -> Indicator:
        svc = self._svc()
        try:
            if svc.get_category(category_id) is None:
                raise ValueError(f"归属分类不存在: {category_id}")
            indicator = new_indicator(
                category_id=category_id,
                indicator_name=indicator_name,
                indicator_code=indicator_code,
                data_type=fields.get("data_type", 1),
                indicator_desc=fields.get("indicator_desc"),
                unit=fields.get("unit"),
            )
            for key in (
                "standard_value", "min_threshold", "max_threshold", "positive_flag",
                "default_score_rule_id", "tag_list", "version", "status", "create_user",
            ):
                if key in fields and fields[key] is not None:
                    setattr(indicator, key, fields[key])
            return svc.add_indicator(indicator)
        finally:
            svc._op.disconnect()

    def update_indicator(self, indicator_id: int, **fields: Any) -> Indicator:
        svc = self._svc()
        try:
            existing = svc.get_indicator(indicator_id)
            if existing is None:
                raise ValueError(f"指标不存在: {indicator_id}")
            if fields.get("category_id") is not None and svc.get_category(fields["category_id"]) is None:
                raise ValueError(f"归属分类不存在: {fields['category_id']}")
            for key, value in fields.items():
                if value is not None and hasattr(existing, key):
                    setattr(existing, key, value)
            return svc.update_indicator(existing)
        finally:
            svc._op.disconnect()

    def delete_indicator(self, indicator_id: int) -> bool:
        svc = self._svc()
        try:
            return svc.delete_indicator(indicator_id)
        finally:
            svc._op.disconnect()

    def get_indicator(self, indicator_id: int) -> Optional[Indicator]:
        svc = self._svc()
        try:
            return svc.get_indicator(indicator_id)
        finally:
            svc._op.disconnect()

    def list_indicators(
        self,
        category_id: Optional[int] = None,
        status: Optional[int] = None,
        data_type: Optional[int] = None,
        keyword: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
    ) -> Dict[str, Any]:
        svc = self._svc()
        try:
            offset = (max(1, page) - 1) * page_size
            items = svc.list_indicators(
                category_id=category_id,
                status=status,
                data_type=data_type,
                keyword=keyword,
                limit=page_size,
                offset=offset,
            )
            total = svc.count_indicators(
                category_id=category_id,
                status=status,
                data_type=data_type,
                keyword=keyword,
            )
            return {"list": items, "total": total, "page": page, "page_size": page_size}
        finally:
            svc._op.disconnect()

    # ==================================================================
    # 配套附件
    # ==================================================================
    def add_attach(
        self,
        indicator_id: int,
        file_name: str,
        file_url: str,
        attach_type: int = 1,
    ) -> IndicatorAttach:
        svc = self._svc()
        try:
            if svc.get_indicator(indicator_id) is None:
                raise ValueError(f"指标不存在: {indicator_id}")
            attach = IndicatorAttach(
                indicator_id=indicator_id,
                file_name=file_name,
                file_url=file_url,
                attach_type=attach_type,
            )
            return svc.add_attach(attach)
        finally:
            svc._op.disconnect()

    def delete_attach(self, attach_id: int) -> bool:
        svc = self._svc()
        try:
            return svc.delete_attach(attach_id)
        finally:
            svc._op.disconnect()

    def list_attaches(self, indicator_id: int) -> List[IndicatorAttach]:
        svc = self._svc()
        try:
            return svc.list_attaches(indicator_id)
        finally:
            svc._op.disconnect()


_library_manager: Optional[IndicatorLibraryManager] = None


def get_indicator_library_manager() -> IndicatorLibraryManager:
    """获取指标管理库业务管理器单例。"""
    global _library_manager
    if _library_manager is None:
        _library_manager = IndicatorLibraryManager()
    return _library_manager
