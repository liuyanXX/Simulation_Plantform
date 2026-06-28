"""拆分行为数据存储服务

基于 SQLDatabaseService，实现对 decomposition_behaviors 表的 CRUD。
"""
import json
from datetime import datetime
from typing import Optional, List, Dict, Any

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from bo.decomposition_behavior import (
    DecompositionBehavior,
    DecompositionStrategy,
    DecompositionBehaviorStatus,
)
from data_storage_services.sql_db_services.base_service import SQLDatabaseService


class DecompositionBehaviorService(SQLDatabaseService[DecompositionBehavior]):
    """拆分行为存储服务"""

    def __init__(self, db_type: str = "sqlite", db_config: Optional[Dict[str, Any]] = None):
        super().__init__(db_type=db_type, db_config=db_config)

    def _get_table_name(self) -> str:
        return "decomposition_behaviors"

    def _get_id_field(self) -> str:
        return "behavior_id"

    def _get_id_value(self, obj: DecompositionBehavior) -> str:
        return obj.behavior_id

    def _to_db_dict(self, obj: DecompositionBehavior) -> Dict[str, Any]:
        def j(v):
            return json.dumps(v, ensure_ascii=False) if v else None

        strategy = obj.strategy.value if isinstance(obj.strategy, DecompositionStrategy) else (obj.strategy or "auto")
        status = obj.status.value if isinstance(obj.status, DecompositionBehaviorStatus) else (obj.status or "completed")

        return {
            "behavior_id": obj.behavior_id,
            "solution_id": obj.solution_id,
            "solution_name": obj.solution_name,
            "strategy": strategy,
            "status": status,
            "organizations": j(obj.organizations),
            "personnel": j(obj.personnel),
            "roles": j(obj.roles),
            "task_manifest_id": obj.task_manifest_id,
            "tasks_graph_id": obj.tasks_graph_id,
            "flow_groups": j(obj.flow_groups),
            "tasks": j(obj.tasks),
            "process_log": obj.process_log,
            "result_summary": obj.result_summary,
            "created_by": obj.created_by,
            "created_at": obj.created_at.isoformat() if isinstance(obj.created_at, datetime) else obj.created_at,
            "updated_at": obj.updated_at.isoformat() if isinstance(obj.updated_at, datetime) else obj.updated_at,
        }

    def _from_db_dict(self, data: Dict[str, Any]) -> DecompositionBehavior:
        def j(v, default=None):
            if v is None:
                return default
            if isinstance(v, str):
                try:
                    return json.loads(v)
                except Exception:
                    return default
            return v

        def dt(v):
            if v is None:
                return datetime.now()
            if isinstance(v, datetime):
                return v
            try:
                return datetime.fromisoformat(v.replace("Z", "+00:00"))
            except Exception:
                return datetime.now()

        return DecompositionBehavior(
            behavior_id=data["behavior_id"],
            solution_id=data["solution_id"],
            solution_name=data.get("solution_name"),
            strategy=DecompositionStrategy(data.get("strategy", "auto")),
            status=DecompositionBehaviorStatus(data.get("status", "completed")),
            organizations=j(data.get("organizations")),
            personnel=j(data.get("personnel")),
            roles=j(data.get("roles")),
            task_manifest_id=data.get("task_manifest_id"),
            tasks_graph_id=data.get("tasks_graph_id"),
            flow_groups=j(data.get("flow_groups")),
            tasks=j(data.get("tasks")),
            process_log=data.get("process_log"),
            result_summary=data.get("result_summary"),
            created_by=data.get("created_by"),
            created_at=dt(data.get("created_at")),
            updated_at=dt(data.get("updated_at")),
        )

    # ------------- 业务辅助 -------------

    def list_by_solution(self, solution_id: str) -> List[DecompositionBehavior]:
        try:
            return self.read_all(where={"solution_id": solution_id})
        finally:
            self.disconnect()

    def list_recent(self, limit: int = 50) -> List[DecompositionBehavior]:
        """按更新时间倒序返回最近的拆分行为"""
        try:
            return self.read_all(order_by="updated_at DESC", limit=limit)
        finally:
            self.disconnect()
