"""知识服务类

提供知识对象的数据库CRUD操作服务。
"""

import json
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from .base_service import SQLDatabaseService
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from knowledge_management.models import Knowledge


class KnowledgeService(SQLDatabaseService[Knowledge]):
    """
    知识服务类
    
    提供知识对象的数据库CRUD操作服务。
    """
    
    def _get_table_name(self) -> str:
        return "knowledge"
    
    def _get_id_field(self) -> str:
        return "knowledge_id"
    
    def _get_id_value(self, obj: Knowledge) -> str:
        return obj.knowledge_id
    
    def _to_db_dict(self, obj: Knowledge) -> Dict[str, Any]:
        """将知识对象转换为数据库字典"""
        return {
            "knowledge_id": obj.knowledge_id,
            "title": obj.title,
            "summary": obj.summary,
            "content": obj.content,
            "index_ids": json.dumps(obj.index_ids, ensure_ascii=False) if obj.index_ids else None,
            "tags": json.dumps(obj.tags, ensure_ascii=False) if obj.tags else None,
            "category": obj.category,
            "created_at": obj.created_at.isoformat() if isinstance(obj.created_at, datetime) else obj.created_at,
            "updated_at": obj.updated_at.isoformat() if isinstance(obj.updated_at, datetime) else obj.updated_at,
            "is_active": 1 if obj.is_active else 0
        }
    
    def _from_db_dict(self, data: Dict[str, Any]) -> Knowledge:
        """将数据库字典转换为知识对象"""
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
        
        return Knowledge(
            knowledge_id=data["knowledge_id"],
            title=data["title"],
            summary=data["summary"],
            content=data["content"],
            index_ids=parse_json(data.get("index_ids"), []),
            tags=parse_json(data.get("tags"), []),
            category=data.get("category", "evaluation"),
            created_at=parse_datetime(data.get("created_at")) or datetime.now(),
            updated_at=parse_datetime(data.get("updated_at")) or datetime.now(),
            is_active=bool(data.get("is_active", 1))
        )
    
    def get_by_category(self, category: str) -> List[Knowledge]:
        """
        按分类查询知识
        
        :param category: 分类名称
        :return: 知识列表
        """
        return self.read_all(where={"category": category})
    
    def get_by_tag(self, tag: str) -> List[Knowledge]:
        """
        按标签查询知识
        
        :param tag: 标签名称
        :return: 知识列表
        """
        all_knowledge = self.read_all(where={"is_active": 1})
        return [k for k in all_knowledge if tag in k.tags]
    
    def get_by_index(self, index_id: str) -> List[Knowledge]:
        """
        按指标ID查询关联知识
        
        :param index_id: 指标ID
        :return: 知识列表
        """
        all_knowledge = self.read_all(where={"is_active": 1})
        return [k for k in all_knowledge if index_id in k.index_ids]
    
    def get_active_knowledge(self) -> List[Knowledge]:
        """
        获取所有启用的知识
        
        :return: 启用的知识列表
        """
        return self.read_all(where={"is_active": 1})
    
    def search_by_title(self, keyword: str) -> List[Knowledge]:
        """
        按标题模糊查询知识
        
        :param keyword: 关键词
        :return: 知识列表
        """
        all_knowledge = self.read_all(where={"is_active": 1})
        return [k for k in all_knowledge if keyword.lower() in k.title.lower()]
    
    def search_by_content(self, keyword: str) -> List[Knowledge]:
        """
        按内容模糊查询知识
        
        :param keyword: 关键词
        :return: 知识列表
        """
        all_knowledge = self.read_all(where={"is_active": 1})
        return [k for k in all_knowledge if keyword.lower() in k.content.lower()]


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 测试知识服务
    service = KnowledgeService()
    
    # 创建测试知识
    knowledge = Knowledge(
        knowledge_id="KNOW_EVAL_001",
        title="完整性评估知识",
        summary="关于如何评估方案完整性的知识",
        content="完整性评估需要检查方案是否包含所有必要元素...",
        index_ids=["IDX_COMP_001"],
        tags=["完整性", "评估"],
        category="evaluation"
    )
    
    # 保存
    service.create(knowledge)
    print(f"创建知识: {knowledge.knowledge_id}")
    
    # 读取
    loaded = service.read("KNOW_EVAL_001")
    print(f"读取知识: {loaded}")
    
    # 删除
    service.delete("KNOW_EVAL_001")
    print("删除知识成功")
    
    service.disconnect()
