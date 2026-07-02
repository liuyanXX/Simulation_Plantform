"""系统空间 · 智能员工注册持久化服务 (AIWorkerRegistryService)

直接通过 SQLiteOperator 对 ssys_ai_worker_registry 表做增、删、改、查。
查找支持:
  - 按ID查本身               get_by_id(rid)
  - 按类型标识查本身          get_by_type(worker_type)
  - 查全量                    list_all(...)
  - 计数                      count(...)

同时提供供各模块直接调用的服务函数(见文件末尾):
  - get_worker_registration(worker_type)      获取单个注册信息
  - list_worker_registrations(only_active)     获取全部注册信息
  - get_worker_class_path(worker_type)         获取全路径类名
  - get_worker_max_count(worker_type)          获取最大数量
  - resolve_worker_class(worker_type)          按全路径动态加载并返回类对象
"""
from __future__ import annotations
import importlib
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Type

from data_storage_services.SQLite.sqlite_operator import SQLiteOperator
from bo.ssys.ai_worker_registration import AIWorkerRegistration


logger = logging.getLogger("AIWorkerRegistryService")


def _now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


class AIWorkerRegistryService:
    """系统空间 · 智能员工注册持久化服务。"""

    TABLE = "ssys_ai_worker_registry"

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

    def __enter__(self) -> "AIWorkerRegistryService":
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
    def add(self, reg: AIWorkerRegistration) -> AIWorkerRegistration:
        if self.get_by_type(reg.worker_type) is not None:
            raise ValueError(f"智能员工类型 '{reg.worker_type}' 已注册")
        if not reg.created_at:
            reg.created_at = _now_iso()
        reg.updated_at = _now_iso()
        data = reg.model_dump()
        data.pop("id", None)
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?"] * len(data))
        self._op.cursor.execute(
            f"INSERT INTO {self.TABLE} ({columns}) VALUES ({placeholders})",
            list(data.values()),
        )
        self._op.connection.commit()
        reg.id = self._op.cursor.lastrowid
        return self.get_by_id(reg.id)

    def get_by_id(self, rid: int) -> Optional[AIWorkerRegistration]:
        self._op.cursor.execute(
            f"SELECT * FROM {self.TABLE} WHERE id = ?", [int(rid)]
        )
        row = self._op.cursor.fetchone()
        return self._from_row(dict(row)) if row else None

    def get_by_type(self, worker_type: str) -> Optional[AIWorkerRegistration]:
        self._op.cursor.execute(
            f"SELECT * FROM {self.TABLE} WHERE worker_type = ?", [worker_type]
        )
        row = self._op.cursor.fetchone()
        return self._from_row(dict(row)) if row else None

    def update(self, reg: AIWorkerRegistration) -> Optional[AIWorkerRegistration]:
        if reg.id is None:
            return None
        # 校验类型唯一性(排除自身)
        existing = self.get_by_type(reg.worker_type)
        if existing is not None and existing.id != reg.id:
            raise ValueError(f"智能员工类型 '{reg.worker_type}' 已被其它记录占用")
        reg.updated_at = _now_iso()
        fields: List[str] = []
        values: List[Any] = []
        for k, v in reg.model_dump().items():
            if k == "id":
                continue
            fields.append(f"{k} = ?")
            values.append(v)
        values.append(reg.id)
        self._op.cursor.execute(
            f"UPDATE {self.TABLE} SET {', '.join(fields)} WHERE id = ?",
            values,
        )
        self._op.connection.commit()
        return self.get_by_id(reg.id)

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
    ) -> List[AIWorkerRegistration]:
        clauses: List[str] = []
        params: List[Any] = []
        if status:
            clauses.append("status = ?")
            params.append(status)
        if keyword:
            clauses.append("(worker_type LIKE ? OR worker_name LIKE ? OR class_path LIKE ? OR description LIKE ?)")
            params += [f"%{keyword}%"] * 4
        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        offset = max(0, (page - 1)) * page_size
        self._op.cursor.execute(
            f"SELECT * FROM {self.TABLE} {where} ORDER BY id ASC LIMIT ? OFFSET ?",
            params + [page_size, offset],
        )
        return [self._from_row(dict(r)) for r in self._op.cursor.fetchall()]

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
            clauses.append("(worker_type LIKE ? OR worker_name LIKE ? OR class_path LIKE ? OR description LIKE ?)")
            params += [f"%{keyword}%"] * 4
        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        self._op.cursor.execute(
            f"SELECT COUNT(*) AS cnt FROM {self.TABLE} {where}", params
        )
        row = self._op.cursor.fetchone()
        return int(dict(row)["cnt"]) if row else 0

    # ---------- 辅助 ----------
    def _from_row(self, row: Dict[str, Any]) -> AIWorkerRegistration:
        return AIWorkerRegistration(**row)


# ======================================================================
# 供各模块直接调用的服务函数(封装连接生命周期, 调用方无需关心持久化细节)
# ======================================================================
def get_worker_registration(worker_type: str) -> Optional[AIWorkerRegistration]:
    """按类型标识获取单个智能员工注册信息。

    :param worker_type: 智能员工类型标识
    :return: AIWorkerRegistration 或 None
    """
    svc = AIWorkerRegistryService()
    try:
        return svc.get_by_type(worker_type)
    finally:
        svc.disconnect()


def list_worker_registrations(only_active: bool = False) -> List[AIWorkerRegistration]:
    """获取全部智能员工注册信息。

    :param only_active: 为 True 时仅返回启用(active)状态的注册项
    :return: AIWorkerRegistration 列表
    """
    svc = AIWorkerRegistryService()
    try:
        return svc.list_all(status="active" if only_active else None, page=1, page_size=1000)
    finally:
        svc.disconnect()


def get_worker_class_path(worker_type: str) -> Optional[str]:
    """获取指定类型智能员工的全路径类名。

    :param worker_type: 智能员工类型标识
    :return: 全路径类名字符串, 未注册返回 None
    """
    reg = get_worker_registration(worker_type)
    return reg.class_path if reg else None


def get_worker_max_count(worker_type: str) -> Optional[int]:
    """获取指定类型智能员工的最大数量(0 表示不限制)。

    :param worker_type: 智能员工类型标识
    :return: 最大数量, 未注册返回 None
    """
    reg = get_worker_registration(worker_type)
    return reg.max_count if reg else None


def resolve_worker_class(worker_type: str) -> Optional[Type]:
    """按注册的全路径类名动态加载并返回类对象。

    供仿真等模块根据注册信息动态实例化智能员工。

    :param worker_type: 智能员工类型标识
    :return: 类对象, 未注册或加载失败返回 None
    """
    reg = get_worker_registration(worker_type)
    if reg is None or not reg.class_path:
        return None
    try:
        module_path, _, class_name = reg.class_path.rpartition(".")
        if not module_path:
            return None
        module = importlib.import_module(module_path)
        return getattr(module, class_name, None)
    except Exception as e:  # noqa: BLE001
        logger.error(f"加载智能员工类失败 {reg.class_path}: {e}")
        return None
