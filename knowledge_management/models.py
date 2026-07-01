"""知识管理模块 - 数据模型

定义知识的PyDantic模型，确保数据完整性和类型安全。
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime
import re


class Knowledge(BaseModel):
    """
    知识模型
    
    知识是指由用户提供的文本，由标题、摘要和内容组成。
    """
    
    knowledge_id: str = Field(..., description="知识唯一ID")
    title: str = Field(..., description="知识标题")
    summary: str = Field(..., description="知识摘要")
    content: str = Field(..., description="知识内容")
    index_ids: List[str] = Field(default_factory=list, description="关联的指标ID列表")
    tags: List[str] = Field(default_factory=list, description="知识标签")
    category: str = Field("decomposition", description="知识分类")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    is_active: bool = Field(True, description="是否启用")
    
    @validator('knowledge_id')
    def validate_knowledge_id(cls, v):
        if not re.match(r'^KNOW_\w{2,}_\d{3,}$', v):
            raise ValueError("知识ID格式必须为 KNOW_类型_数字，如 KNOW_EVAL_001")
        return v


class KnowledgeQueryParams(BaseModel):
    """知识查询参数"""
    
    knowledge_id: Optional[str] = None
    title: Optional[str] = None
    index_id: Optional[str] = None
    tag: Optional[str] = None
    category: Optional[str] = None
    is_active: Optional[bool] = True
