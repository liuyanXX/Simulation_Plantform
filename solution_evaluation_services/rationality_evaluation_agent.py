"""合理性评价Agent模块

实现合理性评价Agent，继承自BaseEvaluationAgent。
使用ollama本地大模型进行合理性评价，并从知识库获取相关知识。
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

RATIONALITY_SYSTEM_PROMPT = """你是一位资深的方案合理性评估专家，擅长评估方案内容的合理性和可行性。

合理性评估原则：
1. 目标合理：方案目标是否与组织战略一致，是否现实可行
2. 措施合理：方案措施是否科学有效，是否符合实际情况
3. 资源合理：方案资源配置是否合理，是否存在浪费或不足
4. 时间合理：方案时间安排是否合理，是否过于紧张或宽松
5. 风险合理：方案风险评估是否充分，应对措施是否合理
6. 效益合理：方案预期效益是否合理，成本效益比是否可接受

合理性评估指标：
1. 战略一致性：方案是否与组织战略目标一致
2. 技术可行性：方案技术方案是否可行
3. 经济合理性：方案经济效益是否合理
4. 操作可行性：方案操作流程是否可行
5. 资源匹配度：方案资源配置是否匹配需求
6. 时间合理性：方案时间安排是否合理

输出要求：
必须输出JSON格式，包含以下字段：
{
  "score": 综合得分(0-100),
  "level": "excellent|good|average|poor|critical",
  "rationality_metrics": {
    "strategic_alignment": 战略一致性得分(0-100),
    "technical_feasibility": 技术可行性得分(0-100),
    "economic_rationality": 经济合理性得分(0-100),
    "operational_feasibility": 操作可行性得分(0-100),
    "resource_match": 资源匹配度得分(0-100),
    "time_rationality": 时间合理性得分(0-100)
  },
  "irrational_elements": ["不合理元素1", "不合理元素2", ...],
  "summary": "评估摘要",
  "recommendations": ["建议1", "建议2", ...]
}
"""


class RationalityEvaluationAgent(BaseEvaluationAgent):
    """合理性评价Agent"""
    
    def __init__(self, config: AgentConfig, knowledge_base_path: Optional[str] = None):
        """
        初始化合理性评价Agent
        
        :param config: Agent配置
        :param knowledge_base_path: 知识库路径
        """
        config.agent_type = AgentType.CUSTOM
        if not config.system_prompt:
            config.system_prompt = RATIONALITY_SYSTEM_PROMPT
        super().__init__(config)
        
        self._knowledge_base_path = knowledge_base_path
        self._knowledge_data: Dict[str, Any] = {}
        
        # 加载知识库数据
        if knowledge_base_path and os.path.exists(knowledge_base_path):
            self._load_knowledge_base()
    
    def _load_knowledge_base(self) -> None:
        """加载知识库数据"""
        try:
            knowledge_file = os.path.join(self._knowledge_base_path, "rationality_knowledge.json")
            if os.path.exists(knowledge_file):
                with open(knowledge_file, 'r', encoding='utf-8') as f:
                    self._knowledge_data = json.load(f)
                logger.info(f"合理性评价Agent知识库加载成功: {len(self._knowledge_data)} 条记录")
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
    
    def evaluate(self, context: EvaluationContext) -> EvaluationOutput:
        """
        执行合理性评价
        
        :param context: 评估上下文
        :return: 评估输出
        """
        # 从知识库获取相关知识
        knowledge = self._get_knowledge("合理性指标")
        
        # 构建提示词
        prompt = f"""请对以下方案进行合理性评估：

方案ID: {context.solution_id}
方案名称: {context.solution_name}
方案内容: {context.solution_content}

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
                dimension="rationality",
                score=data.get('score', 50),
                level=data.get('level', 'average'),
                summary=data.get('summary', ''),
                details={
                    "rationality_metrics": data.get('rationality_metrics', {}),
                    "irrational_elements": data.get('irrational_elements', [])
                },
                recommendations=data.get('recommendations', [])
            )
        except Exception as e:
            logger.error(f"解析合理性评估响应失败: {e}")
            return EvaluationOutput(
                agent_id=self._agent_id,
                solution_id=context.solution_id,
                dimension="rationality",
                score=50,
                level="average",
                summary=f"评估解析失败: {str(e)}",
                recommendations=["建议重新评估"]
            )
    
    def evaluate_solution(self, solution_evaluation: SolutionEvaluation) -> SolutionEvaluation:
        """
        评价方案合理性
        
        :param solution_evaluation: 方案评价对象
        :return: 更新后的方案评价对象
        """
        logger.info(f"开始评价方案合理性: {solution_evaluation.solution_id}")
        
        # 标记为评估中
        solution_evaluation.mark_in_progress()
        
        try:
            # 构建评估上下文
            context = EvaluationContext(
                solution_id=solution_evaluation.solution_id,
                solution_name=solution_evaluation.solution_name,
                solution_content=solution_evaluation.solution_content or "",
                evaluation_dimension="rationality",
                additional_info={
                    "objectives": solution_evaluation.solution_objectives,
                    "initiatives": solution_evaluation.solution_initiatives,
                    "purpose": solution_evaluation.solution_purpose
                }
            )
            
            # 执行评估
            output = self.evaluate(context)
            
            # 创建维度评价结果
            dimension_evaluation = DimensionEvaluation(
                dimension="rationality",
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
            
            logger.info(f"合理性评价完成: {solution_evaluation.solution_id}, 得分: {output.score}")
            
        except Exception as e:
            logger.error(f"合理性评价失败: {e}")
            solution_evaluation.mark_failed(str(e))
        
        return solution_evaluation