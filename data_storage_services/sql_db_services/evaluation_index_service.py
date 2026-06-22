"""评价指标服务类

提供评价指标对象的数据库CRUD操作服务。
"""

import json
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from .base_service import SQLDatabaseService
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from knowledge_management.models import EvaluationIndex, IndexType, IndexLevel


class EvaluationIndexService(SQLDatabaseService[EvaluationIndex]):
    """
    评价指标服务类
    
    提供评价指标对象的数据库CRUD操作服务。
    """
    
    def _get_table_name(self) -> str:
        return "evaluation_indices"
    
    def _get_id_field(self) -> str:
        return "index_id"
    
    def _get_id_value(self, obj: EvaluationIndex) -> str:
        return obj.index_id
    
    def _to_db_dict(self, obj: EvaluationIndex) -> Dict[str, Any]:
        """将评价指标对象转换为数据库字典"""
        return {
            "index_id": obj.index_id,
            "name": obj.name,
            "description": obj.description,
            "evaluation_method": obj.evaluation_method,
            "agent_ids": json.dumps(obj.agent_ids, ensure_ascii=False) if obj.agent_ids else "[]",
            "index_type": obj.index_type.value if isinstance(obj.index_type, IndexType) else obj.index_type,
            "index_level": obj.index_level.value if isinstance(obj.index_level, IndexLevel) else obj.index_level,
            "parent_id": obj.parent_id,
            "weight": obj.weight,
            "score_range": str(obj.score_range) if obj.score_range else "(0, 100)",
            "created_at": obj.created_at.isoformat() if isinstance(obj.created_at, datetime) else obj.created_at,
            "updated_at": obj.updated_at.isoformat() if isinstance(obj.updated_at, datetime) else obj.updated_at,
            "is_active": 1 if obj.is_active else 0
        }
    
    def _from_db_dict(self, data: Dict[str, Any]) -> EvaluationIndex:
        """将数据库字典转换为评价指标对象"""
        def parse_json(value, default=None):
            if value is None:
                return default or []
            if isinstance(value, str):
                try:
                    return json.loads(value)
                except:
                    return value
            return value
        
        def parse_datetime(value):
            if value is None:
                return None
            if isinstance(value, str):
                return datetime.fromisoformat(value.replace('Z', '+00:00'))
            return value
        
        def parse_score_range(value):
            if value is None:
                return (0, 100)
            if isinstance(value, str):
                try:
                    # 解析 "(0, 100)" 格式
                    value = value.strip("()")
                    parts = value.split(",")
                    return (float(parts[0].strip()), float(parts[1].strip()))
                except:
                    return (0, 100)
            return value
        
        return EvaluationIndex(
            index_id=data["index_id"],
            name=data["name"],
            description=data["description"],
            evaluation_method=data["evaluation_method"],
            agent_ids=parse_json(data.get("agent_ids"), []),
            index_type=IndexType(data["index_type"]) if data.get("index_type") else IndexType.OTHER,
            index_level=IndexLevel(data["index_level"]) if data.get("index_level") else IndexLevel.LEVEL_1,
            parent_id=data.get("parent_id"),
            weight=data.get("weight", 1.0),
            score_range=parse_score_range(data.get("score_range")),
            created_at=parse_datetime(data.get("created_at")) or datetime.now(),
            updated_at=parse_datetime(data.get("updated_at")) or datetime.now(),
            is_active=bool(data.get("is_active", 1))
        )
    
    def get_by_type(self, index_type: IndexType) -> List[EvaluationIndex]:
        """
        按类型查询指标
        
        :param index_type: 指标类型
        :return: 指标列表
        """
        return self.read_all(where={"index_type": index_type.value})
    
    def get_by_level(self, index_level: IndexLevel) -> List[EvaluationIndex]:
        """
        按层级查询指标
        
        :param index_level: 指标层级
        :return: 指标列表
        """
        return self.read_all(where={"index_level": index_level.value})
    
    def get_by_parent(self, parent_id: str) -> List[EvaluationIndex]:
        """
        按父指标查询子指标
        
        :param parent_id: 父指标ID
        :return: 子指标列表
        """
        return self.read_all(where={"parent_id": parent_id})
    
    def get_root_indices(self) -> List[EvaluationIndex]:
        """
        获取根指标（无父指标的指标）
        
        :return: 根指标列表
        """
        return self.read_all(where={"parent_id": None})
    
    def get_active_indices(self) -> List[EvaluationIndex]:
        """
        获取所有启用的指标
        
        :return: 启用的指标列表
        """
        return self.read_all(where={"is_active": 1})
    
    def get_by_agent(self, agent_id: str) -> List[EvaluationIndex]:
        """
        按评价Agent查询指标
        
        :param agent_id: Agent ID
        :return: 指标列表
        """
        all_indices = self.read_all(where={"is_active": 1})
        return [idx for idx in all_indices if agent_id in idx.agent_ids]
    
    def get_index_tree(self, root_id: str = None) -> Dict[str, Any]:
        """
        获取指标树结构
        
        :param root_id: 根指标ID，None表示获取所有根指标
        :return: 指标树字典
        """
        def build_tree(index: EvaluationIndex) -> Dict[str, Any]:
            children = self.get_by_parent(index.index_id)
            return {
                "index_id": index.index_id,
                "name": index.name,
                "index_type": index.index_type.value,
                "index_level": index.index_level.value,
                "weight": index.weight,
                "children": [build_tree(child) for child in children]
            }
        
        if root_id:
            root = self.read(root_id)
            if root:
                return build_tree(root)
            return {}
        else:
            roots = self.get_root_indices()
            return [build_tree(root) for root in roots]


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 测试评价指标服务
    service = EvaluationIndexService()
    
    # 创建测试指标
    index = EvaluationIndex(
        index_id="IDX_COMP_001",
        name="完整性指标",
        description="评估方案的完整性",
        evaluation_method="检查方案是否包含所有必要元素",
        agent_ids=["AGENT_001"],
        index_type=IndexType.COMPLETENESS,
        index_level=IndexLevel.LEVEL_1,
        weight=1.0
    )
    
    # 保存
    service.create(index)
    print(f"创建指标: {index.index_id}")
    
    # 读取
    loaded = service.read("IDX_COMP_001")
    print(f"读取指标: {loaded}")
    
    # 删除
    service.delete("IDX_COMP_001")
    print("删除指标成功")
    
    service.disconnect()
