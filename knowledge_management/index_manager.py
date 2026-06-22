"""评价指标管理服务

提供对评价指标的增、删、改、查等基础服务。
评价指标是针对被评价方案设定的多层级、多维度的指标体系。
"""

import json
import os
import logging
from typing import List, Optional
from datetime import datetime

from .models import (
    EvaluationIndex, IndexType, IndexLevel,
    IndexQueryParams
)

logger = logging.getLogger(__name__)


class EvaluationIndexManager:
    """
    评价指标管理服务
    
    管理评价指标库，提供增、删、改、查等基础服务。
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """初始化评价指标管理器"""
        self._storage_path = storage_path or os.path.join(
            os.path.dirname(__file__), 'evaluation_indices', 'indices.json'
        )
        self._indices: List[EvaluationIndex] = []
        
        # 确保存储目录存在
        os.makedirs(os.path.dirname(self._storage_path), exist_ok=True)
        
        # 加载指标库
        self._load_indices()
        
        # 如果指标库为空，初始化预置指标
        if not self._indices:
            self._initialize_default_indices()
            self._save_indices()
    
    def _load_indices(self):
        """从文件加载评价指标"""
        try:
            if os.path.exists(self._storage_path):
                with open(self._storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._indices = [EvaluationIndex(**item) for item in data]
                logger.info(f"成功加载 {len(self._indices)} 个评价指标")
            else:
                logger.info("评价指标库文件不存在，将创建新的指标库")
        except Exception as e:
            logger.error(f"加载评价指标失败: {e}")
            self._indices = []
    
    def _save_indices(self):
        """保存评价指标到文件"""
        try:
            with open(self._storage_path, 'w', encoding='utf-8') as f:
                data = [index.dict() for index in self._indices]
                json.dump(data, f, ensure_ascii=False, indent=2, 
                          default=self._datetime_to_str)
            logger.info(f"成功保存 {len(self._indices)} 个评价指标")
        except Exception as e:
            logger.error(f"保存评价指标失败: {e}")
    
    def _datetime_to_str(self, obj):
        """datetime转字符串"""
        if isinstance(obj, datetime):
            return obj.isoformat()
        return str(obj)
    
    def _initialize_default_indices(self):
        """初始化预置评价指标"""
        logger.info("初始化预置评价指标")

        # 不再预置评价指标，返回空列表
        default_indices = []

        self._indices = default_indices
        logger.info(f"已初始化 {len(default_indices)} 个预置评价指标")
    
    def add_index(self, index: EvaluationIndex) -> EvaluationIndex:
        """添加评价指标"""
        # 检查ID是否已存在
        if any(existing.index_id == index.index_id for existing in self._indices):
            raise ValueError(f"评价指标ID已存在: {index.index_id}")
        
        # 检查父指标是否存在（如果有父指标）
        if index.parent_id and not any(existing.index_id == index.parent_id for existing in self._indices):
            raise ValueError(f"父指标不存在: {index.parent_id}")
        
        index.created_at = datetime.now()
        index.updated_at = datetime.now()
        self._indices.append(index)
        self._save_indices()
        
        logger.info(f"添加评价指标: {index.index_id} - {index.name}")
        return index
    
    def update_index(self, index_id: str, **kwargs) -> EvaluationIndex:
        """更新评价指标"""
        for index in self._indices:
            if index.index_id == index_id:
                # 更新字段
                for key, value in kwargs.items():
                    if hasattr(index, key):
                        setattr(index, key, value)
                
                index.updated_at = datetime.now()
                self._save_indices()
                
                logger.info(f"更新评价指标: {index_id}")
                return index
        
        raise ValueError(f"评价指标不存在: {index_id}")
    
    def delete_index(self, index_id: str) -> bool:
        """删除评价指标"""
        # 检查是否有子指标依赖
        if any(index.parent_id == index_id for index in self._indices):
            raise ValueError(f"评价指标有子指标依赖，无法删除: {index_id}")
        
        original_count = len(self._indices)
        self._indices = [index for index in self._indices if index.index_id != index_id]
        
        if len(self._indices) < original_count:
            self._save_indices()
            logger.info(f"删除评价指标: {index_id}")
            return True
        
        raise ValueError(f"评价指标不存在: {index_id}")
    
    def get_index(self, index_id: str) -> Optional[EvaluationIndex]:
        """根据ID获取评价指标"""
        for index in self._indices:
            if index.index_id == index_id:
                return index
        return None
    
    def query_indices(self, params: IndexQueryParams) -> List[EvaluationIndex]:
        """查询评价指标"""
        results = self._indices
        
        if params.is_active is not None:
            results = [index for index in results if index.is_active == params.is_active]
        
        if params.index_id:
            results = [index for index in results if params.index_id in index.index_id]
        
        if params.name:
            results = [index for index in results if params.name in index.name]
        
        if params.index_type:
            results = [index for index in results if index.index_type == params.index_type]
        
        if params.index_level:
            results = [index for index in results if index.index_level == params.index_level]
        
        if params.parent_id:
            results = [index for index in results if index.parent_id == params.parent_id]
        
        if params.agent_id:
            results = [index for index in results if params.agent_id in index.agent_ids]
        
        return results
    
    def list_indices(self) -> List[EvaluationIndex]:
        """获取所有评价指标"""
        return self._indices
    
    def get_indices_by_agent(self, agent_id: str) -> List[EvaluationIndex]:
        """获取指定Agent负责评价的指标"""
        return [index for index in self._indices if agent_id in index.agent_ids]
    
    def get_child_indices(self, parent_id: str) -> List[EvaluationIndex]:
        """获取子指标列表"""
        return [index for index in self._indices if index.parent_id == parent_id]


# 全局评价指标管理器实例
_index_manager = None


def get_index_manager(storage_path: Optional[str] = None) -> EvaluationIndexManager:
    """获取评价指标管理器单例"""
    global _index_manager
    if _index_manager is None:
        _index_manager = EvaluationIndexManager(storage_path)
    return _index_manager
