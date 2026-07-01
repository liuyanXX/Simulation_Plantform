"""知识管理模块

提供知识管理服务，支持对知识的增、删、改、查等操作。

核心组件：
- KnowledgeManager: 知识管理服务
- Knowledge: 知识模型

目录结构：
- knowledge_management/: 模块根目录
  - knowledge_base/: 知识库存储目录
  - data/: 数据存储目录
"""

from .models import (
    Knowledge,
    KnowledgeQueryParams
)
from .knowledge_manager import (
    KnowledgeManager,
    get_knowledge_manager
)

__all__ = [
    # 模型
    'Knowledge',
    'KnowledgeQueryParams',

    # 管理器
    'KnowledgeManager',
    'get_knowledge_manager'
]
