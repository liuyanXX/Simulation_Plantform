"""方案评价对象模块

定义方案评价对象，存储方案信息、评价维度、使用的Agent和评价结果。
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bo.solution import Solution


class EvaluationStatus(str, Enum):
    """评价状态枚举"""
    PENDING = "pending"           # 待评估
    IN_PROGRESS = "in_progress"   # 评估中
    COMPLETED = "completed"       # 已完成
    FAILED = "failed"             # 评估失败


class DimensionEvaluation(BaseModel):
    """单维度评价结果"""
    dimension: str = Field(description="评价维度")
    agent_id: str = Field(description="执行评价的Agent ID")
    agent_name: Optional[str] = Field(default=None, description="Agent名称")
    score: float = Field(ge=0, le=100, description="评价得分(0-100)")
    level: str = Field(description="评价等级")
    summary: str = Field(description="评价摘要")
    details: Optional[Dict[str, Any]] = Field(default=None, description="详细评价信息")
    recommendations: List[str] = Field(default_factory=list, description="改进建议")
    confidence: float = Field(default=0.8, ge=0, le=1, description="置信度")
    evaluated_at: datetime = Field(default_factory=datetime.now, description="评估时间")
    status: EvaluationStatus = Field(default=EvaluationStatus.PENDING, description="评价状态")
    error_message: Optional[str] = Field(default=None, description="错误信息")


class SolutionEvaluation(BaseModel):
    """
    方案评价对象
    
    存储方案信息、评价维度信息、使用的评价Agent ID、针对各维度的评价结果。
    一个方案可以有多个评价维度，针对每一个维度使用一个评价Agent。
    """
    
    # 基本信息
    evaluation_id: str = Field(description="评价ID")
    solution_id: str = Field(description="方案ID")
    solution_name: str = Field(description="方案名称")
    solution_version: str = Field(default="1.0", description="方案版本")
    
    # 方案内容摘要
    solution_purpose: Optional[str] = Field(default=None, description="方案目的")
    solution_objectives: List[str] = Field(default_factory=list, description="方案目标")
    solution_initiatives: List[str] = Field(default_factory=list, description="方案举措")
    solution_content: Optional[str] = Field(default=None, description="方案内容摘要")
    
    # 评价配置
    evaluation_dimensions: List[str] = Field(default_factory=list, description="评价维度列表")
    dimension_agents: Dict[str, str] = Field(default_factory=dict, description="维度-Agent映射{维度: AgentID}")
    
    # 评价结果
    dimension_evaluations: List[DimensionEvaluation] = Field(default_factory=list, description="各维度评价结果")
    overall_score: float = Field(default=0, ge=0, le=100, description="综合得分")
    overall_level: str = Field(default="pending", description="综合等级")
    overall_summary: Optional[str] = Field(default=None, description="综合评价摘要")
    
    # 元信息
    status: EvaluationStatus = Field(default=EvaluationStatus.PENDING, description="评价状态")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    completed_at: Optional[datetime] = Field(default=None, description="完成时间")
    evaluator: Optional[str] = Field(default=None, description="评价人")
    
    # 扩展信息
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="元数据")
    tags: List[str] = Field(default_factory=list, description="标签")
    
    @classmethod
    def from_solution(cls, solution: Solution, evaluation_id: str, 
                     dimensions: Optional[List[str]] = None) -> "SolutionEvaluation":
        """
        从方案对象创建评价对象
        
        :param solution: 方案对象
        :param evaluation_id: 评价ID
        :param dimensions: 评价维度列表
        :return: 方案评价对象
        """
        return cls(
            evaluation_id=evaluation_id,
            solution_id=solution.solution_id,
            solution_name=solution.name,
            solution_version=solution.version,
            solution_purpose=solution.purpose,
            solution_objectives=solution.objectives,
            solution_initiatives=solution.initiatives,
            solution_content=solution.work_content,
            evaluation_dimensions=dimensions or [],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    def add_dimension_evaluation(self, dimension_evaluation: DimensionEvaluation) -> None:
        """
        添加维度评价结果
        
        :param dimension_evaluation: 维度评价结果
        """
        # 检查是否已存在该维度的评价
        existing_idx = None
        for idx, de in enumerate(self.dimension_evaluations):
            if de.dimension == dimension_evaluation.dimension:
                existing_idx = idx
                break
        
        if existing_idx is not None:
            self.dimension_evaluations[existing_idx] = dimension_evaluation
        else:
            self.dimension_evaluations.append(dimension_evaluation)
        
        self.updated_at = datetime.now()
        self._calculate_overall_score()
    
    def set_dimension_agent(self, dimension: str, agent_id: str) -> None:
        """
        设置维度对应的Agent
        
        :param dimension: 评价维度
        :param agent_id: Agent ID
        """
        self.dimension_agents[dimension] = agent_id
        if dimension not in self.evaluation_dimensions:
            self.evaluation_dimensions.append(dimension)
        self.updated_at = datetime.now()
    
    def get_dimension_evaluation(self, dimension: str) -> Optional[DimensionEvaluation]:
        """
        获取指定维度的评价结果
        
        :param dimension: 评价维度
        :return: 维度评价结果
        """
        for de in self.dimension_evaluations:
            if de.dimension == dimension:
                return de
        return None
    
    def get_agent_evaluations(self, agent_id: str) -> List[DimensionEvaluation]:
        """
        获取指定Agent的所有评价结果
        
        :param agent_id: Agent ID
        :return: 评价结果列表
        """
        return [de for de in self.dimension_evaluations if de.agent_id == agent_id]
    
    def _calculate_overall_score(self) -> None:
        """计算综合得分"""
        if not self.dimension_evaluations:
            self.overall_score = 0
            self.overall_level = "pending"
            return
        
        # 计算加权平均分
        total_score = 0
        total_confidence = 0
        completed_count = 0
        
        for de in self.dimension_evaluations:
            if de.status == EvaluationStatus.COMPLETED:
                total_score += de.score * de.confidence
                total_confidence += de.confidence
                completed_count += 1
        
        if total_confidence > 0:
            self.overall_score = round(total_score / total_confidence, 2)
        elif completed_count > 0:
            self.overall_score = round(sum(de.score for de in self.dimension_evaluations 
                                          if de.status == EvaluationStatus.COMPLETED) / completed_count, 2)
        
        # 确定综合等级
        self.overall_level = self._score_to_level(self.overall_score)
    
    def _score_to_level(self, score: float) -> str:
        """将分数转换为等级"""
        if score >= 90:
            return "excellent"
        elif score >= 75:
            return "good"
        elif score >= 60:
            return "average"
        elif score >= 40:
            return "poor"
        else:
            return "critical"
    
    def mark_in_progress(self) -> None:
        """标记为评估中"""
        self.status = EvaluationStatus.IN_PROGRESS
        self.updated_at = datetime.now()
    
    def mark_completed(self) -> None:
        """标记为已完成"""
        self.status = EvaluationStatus.COMPLETED
        self.completed_at = datetime.now()
        self.updated_at = datetime.now()
        self._calculate_overall_score()
    
    def mark_failed(self, error_message: Optional[str] = None) -> None:
        """标记为失败"""
        self.status = EvaluationStatus.FAILED
        self.updated_at = datetime.now()
        if error_message:
            for de in self.dimension_evaluations:
                if de.status == EvaluationStatus.PENDING:
                    de.status = EvaluationStatus.FAILED
                    de.error_message = error_message
    
    def get_summary(self) -> Dict[str, Any]:
        """
        获取评价摘要
        
        :return: 评价摘要字典
        """
        return {
            "evaluation_id": self.evaluation_id,
            "solution_id": self.solution_id,
            "solution_name": self.solution_name,
            "status": self.status.value,
            "overall_score": self.overall_score,
            "overall_level": self.overall_level,
            "dimensions_count": len(self.evaluation_dimensions),
            "completed_dimensions": len([de for de in self.dimension_evaluations 
                                        if de.status == EvaluationStatus.COMPLETED]),
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }
    
    def get_detailed_report(self) -> Dict[str, Any]:
        """
        获取详细评价报告
        
        :return: 详细报告字典
        """
        return {
            "evaluation_id": self.evaluation_id,
            "solution": {
                "solution_id": self.solution_id,
                "name": self.solution_name,
                "version": self.solution_version,
                "purpose": self.solution_purpose,
                "objectives": self.solution_objectives
            },
            "overall": {
                "score": self.overall_score,
                "level": self.overall_level,
                "summary": self.overall_summary
            },
            "dimensions": [
                {
                    "dimension": de.dimension,
                    "agent_id": de.agent_id,
                    "score": de.score,
                    "level": de.level,
                    "summary": de.summary,
                    "recommendations": de.recommendations,
                    "confidence": de.confidence,
                    "status": de.status.value
                }
                for de in self.dimension_evaluations
            ],
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }
