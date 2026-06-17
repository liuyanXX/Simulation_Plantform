"""方案评估与分析服务模块

包含以下核心组件：
- BaseEvaluationAgent: 评价Agent父类
- SolutionEvaluation: 方案评价对象
- AgentRegistry: Agent服务注册表
- CompletenessEvaluationAgent: 完整性评价Agent
- RationalityEvaluationAgent: 合理性评价Agent
- SimulationAnalysisAgent: 仿真结果分析Agent
- ServiceGateway: 服务网关
- EvaluationProxy: 评价代理

提供方案的全面评估和深度分析能力。
"""

from .base_evaluation_agent import (
    BaseEvaluationAgent,
    FeasibilityEvaluationAgent,
    RiskEvaluationAgent,
    AgentConfig,
    AgentType,
    AgentStatus,
    EvaluationContext,
    EvaluationOutput
)
from .solution_evaluation import (
    SolutionEvaluation,
    DimensionEvaluation,
    EvaluationStatus
)
from .agent_registry import (
    AgentRegistry,
    AgentRegistration,
    get_registry,
    register_agent,
    get_agent,
    select_agent
)
from .completeness_evaluation_agent import CompletenessEvaluationAgent
from .rationality_evaluation_agent import RationalityEvaluationAgent
from .simulation_analysis_agent import SimulationAnalysisAgent
from .service_gateway import ServiceGateway
from .evaluation_proxy import EvaluationProxy

__all__ = [
    # Agent
    'BaseEvaluationAgent',
    'FeasibilityEvaluationAgent',
    'RiskEvaluationAgent',
    'CompletenessEvaluationAgent',
    'RationalityEvaluationAgent',
    'SimulationAnalysisAgent',
    'AgentConfig',
    'AgentType',
    'AgentStatus',
    'EvaluationContext',
    'EvaluationOutput',
    
    # 方案评价对象
    'SolutionEvaluation',
    'DimensionEvaluation',
    'EvaluationStatus',
    
    # Agent注册表
    'AgentRegistry',
    'AgentRegistration',
    'get_registry',
    'register_agent',
    'get_agent',
    'select_agent',
    
    # 服务网关和评价代理
    'ServiceGateway',
    'EvaluationProxy'
]
