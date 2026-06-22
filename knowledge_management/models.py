"""知识管理模块 - 数据模型

定义评价指标和知识的PyDantic模型，确保数据完整性和类型安全。
"""

from pydantic import BaseModel, Field, validator
from enum import Enum
from typing import List, Optional
from datetime import datetime
import re


class IndexType(str, Enum):
    """指标类型"""
    COMPLETENESS = "completeness"
    RATIONALITY = "rationality"
    FEASIBILITY = "feasibility"
    RISK = "risk"
    EFFICIENCY = "efficiency"
    COMPLIANCE = "compliance"
    STRATEGY = "strategy"
    RESOURCE = "resource"
    BENEFIT = "benefit"
    OTHER = "other"


class IndexLevel(str, Enum):
    """指标层级"""
    LEVEL_1 = "level_1"
    LEVEL_2 = "level_2"
    LEVEL_3 = "level_3"
    LEVEL_4 = "level_4"


class EvaluationIndex(BaseModel):
    """
    评价指标模型
    
    评价指标是针对被评价方案设定的多层级、多维度的指标体系。
    """
    
    index_id: str = Field(..., description="指标唯一ID")
    name: str = Field(..., description="指标名称")
    description: str = Field(..., description="指标说明")
    evaluation_method: str = Field(..., description="评价方法说明")
    agent_ids: List[str] = Field(..., description="评价Agent的ID列表")
    index_type: IndexType = Field(..., description="指标类型")
    index_level: IndexLevel = Field(..., description="指标层级")
    parent_id: Optional[str] = Field(None, description="父指标ID")
    weight: Optional[float] = Field(1.0, description="指标权重")
    score_range: tuple = Field((0, 100), description="评分范围")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    is_active: bool = Field(True, description="是否启用")
    
    @validator('index_id')
    def validate_index_id(cls, v):
        if not re.match(r'^IDX_\w{2,}_\d{3,}$', v):
            raise ValueError("指标ID格式必须为 IDX_类型_数字，如 IDX_COMP_001")
        return v
    
    @validator('weight')
    def validate_weight(cls, v):
        if v <= 0 or v > 100:
            raise ValueError("权重必须大于0且小于等于100")
        return v
    
    @validator('score_range')
    def validate_score_range(cls, v):
        if v[0] >= v[1]:
            raise ValueError("评分范围最小值必须小于最大值")
        return v


class Knowledge(BaseModel):
    """
    知识模型
    
    知识是指由用户提供的文本，由标题、摘要和内容组成。
    """
    
    knowledge_id: str = Field(..., description="知识唯一ID")
    title: str = Field(..., description="知识标题")
    summary: str = Field(..., description="知识摘要")
    content: str = Field(..., description="知识内容")
    index_ids: List[str] = Field(default_factory=list, description="关联的评价指标ID列表")
    tags: List[str] = Field(default_factory=list, description="知识标签")
    category: str = Field("evaluation", description="知识分类")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    is_active: bool = Field(True, description="是否启用")
    
    @validator('knowledge_id')
    def validate_knowledge_id(cls, v):
        if not re.match(r'^KNOW_\w{2,}_\d{3,}$', v):
            raise ValueError("知识ID格式必须为 KNOW_类型_数字，如 KNOW_EVAL_001")
        return v


class IndexQueryParams(BaseModel):
    """评价指标查询参数"""
    
    index_id: Optional[str] = None
    name: Optional[str] = None
    index_type: Optional[IndexType] = None
    index_level: Optional[IndexLevel] = None
    parent_id: Optional[str] = None
    agent_id: Optional[str] = None
    is_active: Optional[bool] = True


class KnowledgeQueryParams(BaseModel):
    """知识查询参数"""
    
    knowledge_id: Optional[str] = None
    title: Optional[str] = None
    index_id: Optional[str] = None
    tag: Optional[str] = None
    category: Optional[str] = None
    is_active: Optional[bool] = True
