"""仿真结果分析Agent模块

实现仿真结果分析Agent，继承自BaseEvaluationAgent。
使用ollama本地大模型进行效率和完备性评价，并从知识库获取相关知识。
"""
import os
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .base_evaluation_agent import (
    BaseEvaluationAgent,
    AgentConfig,
    AgentType,
    EvaluationContext,
    EvaluationOutput
)
from .solution_evaluation import (
    SolutionEvaluation,
    DimensionEvaluation,
    EvaluationStatus
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SIMULATION_ANALYSIS_SYSTEM_PROMPT = """你是一位资深的仿真结果分析专家，擅长分析仿真运行日志，评估方案的效率和完备性。

仿真分析原则：
1. 效率评估：分析仿真运行效率，包括执行时间、资源消耗等
2. 完备性评估：分析仿真覆盖范围，是否覆盖所有关键场景
3. 结果分析：分析仿真结果是否达到预期目标
4. 问题识别：识别仿真过程中出现的问题和异常
5. 优化建议：提供仿真优化建议

效率和完备性评估指标：
1. 执行效率：仿真执行时间是否合理
2. 资源效率：资源消耗是否合理
3. 覆盖完备性：是否覆盖所有关键场景
4. 结果完备性：仿真结果是否完整
5. 数据准确性：仿真数据是否准确
6. 系统稳定性：仿真过程是否稳定

输出要求：
必须输出JSON格式，包含以下字段：
{
  "score": 综合得分(0-100),
  "level": "excellent|good|average|poor|critical",
  "efficiency_metrics": {
    "execution_efficiency": 执行效率得分(0-100),
    "resource_efficiency": 资源效率得分(0-100),
    "average_execution_time": 平均执行时间,
    "peak_resource_usage": 峰值资源使用
  },
  "completeness_metrics": {
    "coverage_completeness": 覆盖完备性得分(0-100),
    "result_completeness": 结果完备性得分(0-100),
    "data_accuracy": 数据准确性得分(0-100),
    "system_stability": 系统稳定性得分(0-100)
  },
  "identified_issues": ["问题1", "问题2", ...],
  "summary": "评估摘要",
  "recommendations": ["建议1", "建议2", ...]
}
"""


class SimulationAnalysisAgent(BaseEvaluationAgent):
    """仿真结果分析Agent"""
    
    def __init__(self, config: AgentConfig, knowledge_base_path: Optional[str] = None):
        """
        初始化仿真结果分析Agent
        
        :param config: Agent配置
        :param knowledge_base_path: 知识库路径
        """
        config.agent_type = AgentType.CUSTOM
        if not config.system_prompt:
            config.system_prompt = SIMULATION_ANALYSIS_SYSTEM_PROMPT
        super().__init__(config)
        
        self._knowledge_base_path = knowledge_base_path
        self._knowledge_data: Dict[str, Any] = {}
        
        # 加载知识库数据
        if knowledge_base_path and os.path.exists(knowledge_base_path):
            self._load_knowledge_base()
    
    def _load_knowledge_base(self) -> None:
        """加载知识库数据"""
        try:
            knowledge_file = os.path.join(self._knowledge_base_path, "simulation_knowledge.json")
            if os.path.exists(knowledge_file):
                with open(knowledge_file, 'r', encoding='utf-8') as f:
                    self._knowledge_data = json.load(f)
                logger.info(f"仿真结果分析Agent知识库加载成功: {len(self._knowledge_data)} 条记录")
        except Exception as e:
            logger.error(f"加载知识库失败: {e}")
    
    def _get_knowledge(self, query: str) -> str:
        """
        从知识库获取相关知识
        
        :param query: 查询文本
        :return: 相关知识
        """
        if not self._knowledge_data:
            return ""
        
        # 简单的关键词匹配
        relevant_knowledge = []
        for key, value in self._knowledge_data.items():
            if query.lower() in key.lower() or query.lower() in str(value).lower():
                relevant_knowledge.append(f"{key}: {value}")
        
        return "\n".join(relevant_knowledge) if relevant_knowledge else ""
    
    def evaluate(self, context: EvaluationContext, simulation_log: Optional[str] = None) -> EvaluationOutput:
        """
        执行仿真结果分析
        
        :param context: 评估上下文
        :param simulation_log: 仿真运行日志
        :return: 评估输出
        """
        # 从知识库获取相关知识
        knowledge = self._get_knowledge("效率和完备性指标")
        
        # 构建提示词
        simulation_info = f"\n仿真日志：\n{simulation_log}" if simulation_log else ""
        prompt = f"""请对以下方案进行仿真结果分析：

方案ID: {context.solution_id}
方案名称: {context.solution_name}
方案内容: {context.solution_content}
{simulation_info}

相关知识：
{knowledge}

请输出JSON格式的评估结果。"""
        
        response = self.call_llm(prompt)
        
        # 解析响应
        try:
            start_idx = response.find('{')
            end_idx = response.rfind('}')
            if start_idx != -1 and end_idx != -1:
                data = json.loads(response[start_idx:end_idx+1])
            else:
                data = json.loads(response)
            
            return EvaluationOutput(
                agent_id=self._agent_id,
                solution_id=context.solution_id,
                dimension="simulation",
                score=data.get('score', 50),
                level=data.get('level', 'average'),
                summary=data.get('summary', ''),
                details={
                    "efficiency_metrics": data.get('efficiency_metrics', {}),
                    "completeness_metrics": data.get('completeness_metrics', {}),
                    "identified_issues": data.get('identified_issues', [])
                },
                recommendations=data.get('recommendations', [])
            )
        except Exception as e:
            logger.error(f"解析仿真分析响应失败: {e}")
            return EvaluationOutput(
                agent_id=self._agent_id,
                solution_id=context.solution_id,
                dimension="simulation",
                score=50,
                level="average",
                summary=f"评估解析失败: {str(e)}",
                recommendations=["建议重新评估"]
            )
    
    def evaluate_solution(self, solution_evaluation: SolutionEvaluation, 
                         simulation_log: Optional[str] = None) -> SolutionEvaluation:
        """
        分析方案仿真结果
        
        :param solution_evaluation: 方案评价对象
        :param simulation_log: 仿真运行日志
        :return: 更新后的方案评价对象
        """
        logger.info(f"开始分析方案仿真结果: {solution_evaluation.solution_id}")
        
        # 标记为评估中
        solution_evaluation.mark_in_progress()
        
        try:
            # 构建评估上下文
            context = EvaluationContext(
                solution_id=solution_evaluation.solution_id,
                solution_name=solution_evaluation.solution_name,
                solution_content=solution_evaluation.solution_content or "",
                evaluation_dimension="simulation",
                additional_info={
                    "objectives": solution_evaluation.solution_objectives,
                    "initiatives": solution_evaluation.solution_initiatives,
                    "simulation_log": simulation_log
                }
            )
            
            # 执行评估
            output = self.evaluate(context, simulation_log)
            
            # 创建维度评价结果
            dimension_evaluation = DimensionEvaluation(
                dimension="simulation",
                agent_id=self._agent_id,
                agent_name=self._name,
                score=output.score,
                level=output.level,
                summary=output.summary,
                details=output.details,
                recommendations=output.recommendations,
                confidence=output.confidence,
                evaluated_at=datetime.now(),
                status=EvaluationStatus.COMPLETED
            )
            
            # 添加到方案评价对象
            solution_evaluation.add_dimension_evaluation(dimension_evaluation)
            
            logger.info(f"仿真结果分析完成: {solution_evaluation.solution_id}, 得分: {output.score}")
            
        except Exception as e:
            logger.error(f"仿真结果分析失败: {e}")
            solution_evaluation.mark_failed(str(e))
        
        return solution_evaluation