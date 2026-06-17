"""服务网关模块

负责接收并解析方案评价对象，按照评价维度启动对应的评价Agent，
将评价内容转发给评价Agent，并将Agent评价结果反馈给评价代理。
"""
import os
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .solution_evaluation import SolutionEvaluation, EvaluationStatus
from .agent_registry import AgentRegistry, AgentType
from .base_evaluation_agent import BaseEvaluationAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ServiceGateway:
    """
    服务网关
    
    职责：
    1. 接收并解析方案评价对象
    2. 按照评价维度使用的Agent类型启动对应的评价Agent
    3. 将评价内容转发给评价Agent
    4. 将Agent评价结果反馈给评价代理
    """
    
    def __init__(self, registry: Optional[AgentRegistry] = None):
        """
        初始化服务网关
        
        :param registry: Agent注册表，默认使用全局注册表
        """
        self._registry = registry
        self._logger = logger
        
        # 维度到Agent类型的映射
        self._dimension_agent_mapping = {
            "completeness": AgentType.CUSTOM,
            "rationality": AgentType.CUSTOM,
            "simulation": AgentType.CUSTOM,
            "feasibility": AgentType.FEASIBILITY,
            "risk": AgentType.RISK,
            "resource": AgentType.RESOURCE,
            "benefit": AgentType.BENEFIT,
            "compliance": AgentType.COMPLIANCE,
            "strategy": AgentType.STRATEGY
        }
    
    def _get_registry(self) -> AgentRegistry:
        """获取Agent注册表"""
        if self._registry is None:
            from .agent_registry import get_registry
            self._registry = get_registry()
        return self._registry
    
    def route_to_agent(self, solution_evaluation: SolutionEvaluation, 
                      dimension: str, **kwargs) -> SolutionEvaluation:
        """
        将评价请求路由到对应的Agent
        
        :param solution_evaluation: 方案评价对象
        :param dimension: 评价维度
        :param kwargs: 额外参数（如simulation_log）
        :return: 更新后的方案评价对象
        """
        self._logger.info(f"路由评价请求: {solution_evaluation.solution_id}, 维度: {dimension}")
        
        # 获取Agent类型
        agent_type = self._dimension_agent_mapping.get(dimension, AgentType.GENERAL)
        
        # 从注册表选择Agent
        registry = self._get_registry()
        agent = registry.select_agent(agent_type, strategy="round_robin")
        
        if not agent:
            self._logger.error(f"未找到可用的Agent: {agent_type}")
            solution_evaluation.mark_failed(f"未找到可用的{dimension}评价Agent")
            return solution_evaluation
        
        try:
            # 根据维度调用不同的Agent方法
            if hasattr(agent, 'evaluate_solution'):
                # 新的Agent接口
                if dimension == "simulation" and "simulation_log" in kwargs:
                    solution_evaluation = agent.evaluate_solution(
                        solution_evaluation, 
                        simulation_log=kwargs.get("simulation_log")
                    )
                else:
                    solution_evaluation = agent.evaluate_solution(solution_evaluation)
            else:
                # 旧的Agent接口（兼容性）
                from .base_evaluation_agent import EvaluationContext
                context = EvaluationContext(
                    solution_id=solution_evaluation.solution_id,
                    solution_name=solution_evaluation.solution_name,
                    solution_content=solution_evaluation.solution_content or "",
                    evaluation_dimension=dimension,
                    additional_info=kwargs
                )
                output = agent.evaluate(context)
                
                # 创建维度评价结果
                from .solution_evaluation import DimensionEvaluation
                dimension_evaluation = DimensionEvaluation(
                    dimension=dimension,
                    agent_id=agent.agent_id,
                    agent_name=agent.name,
                    score=output.score,
                    level=output.level,
                    summary=output.summary,
                    details=output.details,
                    recommendations=output.recommendations,
                    confidence=output.confidence,
                    evaluated_at=datetime.now(),
                    status=EvaluationStatus.COMPLETED
                )
                
                solution_evaluation.add_dimension_evaluation(dimension_evaluation)
            
            self._logger.info(f"评价完成: {solution_evaluation.solution_id}, 维度: {dimension}")
            
        except Exception as e:
            self._logger.error(f"评价失败: {e}")
            solution_evaluation.mark_failed(str(e))
        
        return solution_evaluation
    
    def process_evaluation(self, solution_evaluation: SolutionEvaluation, 
                          simulation_log: Optional[str] = None) -> SolutionEvaluation:
        """
        处理方案评价请求
        
        :param solution_evaluation: 方案评价对象
        :param simulation_log: 仿真运行日志（可选）
        :return: 更新后的方案评价对象
        """
        self._logger.info(f"开始处理方案评价: {solution_evaluation.solution_id}")
        
        # 标记为评估中
        solution_evaluation.mark_in_progress()
        
        # 获取需要评估的维度
        dimensions = solution_evaluation.evaluation_dimensions
        
        if not dimensions:
            self._logger.warning(f"方案 {solution_evaluation.solution_id} 没有指定评估维度")
            solution_evaluation.mark_failed("没有指定评估维度")
            return solution_evaluation
        
        # 按维度逐个评估
        for dimension in dimensions:
            self._logger.info(f"开始评估维度: {dimension}")
            
            kwargs = {}
            if dimension == "simulation" and simulation_log:
                kwargs["simulation_log"] = simulation_log
            
            solution_evaluation = self.route_to_agent(solution_evaluation, dimension, **kwargs)
            
            # 如果某个维度评估失败，可以选择继续或停止
            if solution_evaluation.status == EvaluationStatus.FAILED:
                self._logger.warning(f"维度 {dimension} 评估失败，停止评估")
                break
        
        # 标记为已完成
        if solution_evaluation.status != EvaluationStatus.FAILED:
            solution_evaluation.mark_completed()
        
        self._logger.info(f"方案评价处理完成: {solution_evaluation.solution_id}")
        
        return solution_evaluation
    
    def get_available_agents(self) -> Dict[str, Any]:
        """
        获取可用的Agent信息
        
        :return: Agent信息字典
        """
        registry = self._get_registry()
        agents = registry.get_available_agents()
        
        return {
            "total": len(agents),
            "agents": [agent.get_info() for agent in agents]
        }
    
    def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        获取指定Agent的状态
        
        :param agent_id: Agent ID
        :return: Agent状态信息
        """
        registry = self._get_registry()
        return registry.check_health(agent_id)
    
    def register_dimension_agent_mapping(self, dimension: str, agent_type: AgentType) -> None:
        """
        注册维度到Agent类型的映射
        
        :param dimension: 评价维度
        :param agent_type: Agent类型
        """
        self._dimension_agent_mapping[dimension] = agent_type
        self._logger.info(f"注册维度映射: {dimension} -> {agent_type}")
    
    def get_dimension_agent_mapping(self) -> Dict[str, str]:
        """
        获取维度到Agent类型的映射
        
        :return: 映射字典
        """
        return {k: v.value for k, v in self._dimension_agent_mapping.items()}