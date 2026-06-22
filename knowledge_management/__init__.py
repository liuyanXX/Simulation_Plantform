"""知识管理模块

提供评价指标管理和知识管理服务，支持对评价指标和知识的增、删、改、查等操作。

核心组件：
- EvaluationIndexManager: 评价指标管理服务
- KnowledgeManager: 知识管理服务
- EvaluationIndex: 评价指标模型
- Knowledge: 知识模型

目录结构：
- knowledge_management/: 模块根目录
  - evaluation_indices/: 评价指标存储目录
  - knowledge_base/: 知识库存储目录
  - data/: 数据存储目录
"""

from .models import (
    EvaluationIndex,
    Knowledge,
    IndexType,
    IndexLevel,
    IndexQueryParams,
    KnowledgeQueryParams
)
from .index_manager import (
    EvaluationIndexManager,
    get_index_manager
)
from .knowledge_manager import (
    KnowledgeManager,
    get_knowledge_manager
)

__all__ = [
    # 模型
    'EvaluationIndex',
    'Knowledge',
    'IndexType',
    'IndexLevel',
    'IndexQueryParams',
    'KnowledgeQueryParams',
    
    # 管理器
    'EvaluationIndexManager',
    'KnowledgeManager',
    'get_index_manager',
    'get_knowledge_manager'
]
