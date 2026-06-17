"""评价Agent父类模块

定义评价Agent的基类，实现共性属性和方法。
使用agno库实现Agent功能。
"""
import os
from datetime import datetime
from typing import Optional, List, Dict, Any, Type
from enum import Enum
from pydantic import BaseModel, Field

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# agno库导入
try:
    from agno.agent import Agent
    from agno.models.openai import OpenAIChat
    from agno.models.ollama import Ollama
    from agno.knowledge.base import BaseKnowledge
    AGNO_AVAILABLE = True
except ImportError:
    AGNO_AVAILABLE = False
    Agent = object
    BaseKnowledge = object


class AgentType(str, Enum):
    """Agent类型枚举"""
    FEASIBILITY = "feasibility"           # 可行性评估Agent
    RISK = "risk"                         # 风险评估Agent
    RESOURCE = "resource"                 # 资源评估Agent
    BENEFIT = "benefit"                   # 效益评估Agent
    COMPLIANCE = "compliance"             # 合规性评估Agent
    STRATEGY = "strategy"                 # 战略对齐评估Agent
    GENERAL = "general"                   # 通用评估Agent
    CUSTOM = "custom"                     # 自定义评估Agent


class AgentStatus(str, Enum):
    """Agent状态枚举"""
    IDLE = "idle"                         # 空闲
    BUSY = "busy"                         # 忙碌
    ERROR = "error"                       # 错误
    OFFLINE = "offline"                   # 离线


class AgentConfig(BaseModel):
    """Agent配置"""
    agent_id: str = Field(description="Agent唯一标识")
    name: str = Field(description="Agent名称")
    agent_type: AgentType = Field(description="Agent类型")
    description: Optional[str] = Field(default=None, description="Agent描述")
    model_name: str = Field(default="gpt-4o", description="使用的模型名称")
    model_provider: str = Field(default="openai", description="模型提供商(openai/ollama)")
    base_url: Optional[str] = Field(default=None, description="模型API基础URL")
    api_key: Optional[str] = Field(default=None, description="API密钥")
    temperature: float = Field(default=0.3, ge=0, le=2, description="温度参数")
    max_tokens: int = Field(default=4000, description="最大token数")
    knowledge_base_path: Optional[str] = Field(default=None, description="知识库路径")
    system_prompt: Optional[str] = Field(default=None, description="系统提示词")
    tools: List[str] = Field(default_factory=list, description="可用工具列表")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="元数据")


class EvaluationContext(BaseModel):
    """评估上下文"""
    solution_id: str = Field(description="方案ID")
    solution_name: str = Field(description="方案名称")
    solution_content: str = Field(description="方案内容")
    evaluation_dimension: str = Field(description="评估维度")
    additional_info: Optional[Dict[str, Any]] = Field(default=None, description="附加信息")


class EvaluationOutput(BaseModel):
    """评估输出"""
    agent_id: str = Field(description="执行评估的Agent ID")
    solution_id: str = Field(description="方案ID")
    dimension: str = Field(description="评估维度")
    score: float = Field(ge=0, le=100, description="评估得分(0-100)")
    level: str = Field(description="评估等级")
    summary: str = Field(description="评估摘要")
    details: Optional[Dict[str, Any]] = Field(default=None, description="详细评估信息")
    recommendations: List[str] = Field(default_factory=list, description="改进建议")
    confidence: float = Field(default=0.8, ge=0, le=1, description="置信度")
    evaluated_at: datetime = Field(default_factory=datetime.now, description="评估时间")


class BaseEvaluationAgent:
    """
    评价Agent父类
    
    实现评价Agent的共性属性和方法：
    - 共性属性：ID、名称、类型、状态、配置等
    - 共性方法：调用本地大模型、调用知识库、执行评估等
    """
    
    def __init__(self, config: AgentConfig):
        """
        初始化评价Agent
        
        :param config: Agent配置
        """
        self._config = config
        self._agent_id = config.agent_id
        self._name = config.name
        self._agent_type = config.agent_type
        self._status = AgentStatus.IDLE
        self._created_at = datetime.now()
        self._last_used_at: Optional[datetime] = None
        self._usage_count = 0
        self._error_count = 0
        self._knowledge_base: Optional[BaseKnowledge] = None
        self._agent: Optional[Any] = None
        
        # 初始化Agent
        self._initialize_agent()
    
    def _initialize_agent(self) -> None:
        """初始化agno Agent实例"""
        if not AGNO_AVAILABLE:
            self._status = AgentStatus.ERROR
            return
        
        try:
            # 根据模型提供商创建模型实例
            if self._config.model_provider == "ollama":
                model = Ollama(
                    id=self._config.model_name,
                    host=self._config.base_url or "http://localhost:11434"
                )
            else:
                # 默认使用OpenAI
                model_kwargs = {"id": self._config.model_name}
                if self._config.base_url:
                    model_kwargs["base_url"] = self._config.base_url
                if self._config.api_key:
                    model_kwargs["api_key"] = self._config.api_key
                model = OpenAIChat(**model_kwargs)
            
            # 创建Agent实例
            agent_kwargs = {
                "name": self._name,
                "model": model,
                "markdown": True,
            }
            
            if self._config.system_prompt:
                agent_kwargs["instructions"] = [self._config.system_prompt]
            
            if self._config.knowledge_base_path and os.path.exists(self._config.knowledge_base_path):
                # 如果有知识库，可以在这里初始化
                pass
            
            self._agent = Agent(**agent_kwargs)
            self._status = AgentStatus.IDLE
            
        except Exception as e:
            self._status = AgentStatus.ERROR
            print(f"Agent初始化失败: {e}")
    
    @property
    def agent_id(self) -> str:
        """获取Agent ID"""
        return self._agent_id
    
    @property
    def name(self) -> str:
        """获取Agent名称"""
        return self._name
    
    @property
    def agent_type(self) -> AgentType:
        """获取Agent类型"""
        return self._agent_type
    
    @property
    def status(self) -> AgentStatus:
        """获取Agent状态"""
        return self._status
    
    @property
    def config(self) -> AgentConfig:
        """获取Agent配置"""
        return self._config
    
    @property
    def is_available(self) -> bool:
        """检查Agent是否可用"""
        return self._status == AgentStatus.IDLE and self._agent is not None
    
    def call_llm(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        调用大语言模型
        
        :param prompt: 用户提示词
        :param system_prompt: 系统提示词（可选）
        :return: 模型响应
        """
        if not self._agent:
            raise RuntimeError(f"Agent {self._agent_id} 未初始化")
        
        self._status = AgentStatus.BUSY
        try:
            # 使用agno Agent进行调用
            if system_prompt:
                # 临时设置系统提示词
                original_instructions = getattr(self._agent, 'instructions', None)
                self._agent.instructions = [system_prompt]
            
            response = self._agent.run(prompt)
            
            if system_prompt and original_instructions:
                self._agent.instructions = original_instructions
            
            self._last_used_at = datetime.now()
            self._usage_count += 1
            self._status = AgentStatus.IDLE
            
            # 提取响应内容
            if hasattr(response, 'content'):
                return response.content
            return str(response)
            
        except Exception as e:
            self._status = AgentStatus.ERROR
            self._error_count += 1
            raise RuntimeError(f"调用大模型失败: {e}")
    
    def call_knowledge_base(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        调用知识库检索
        
        :param query: 查询文本
        :param top_k: 返回结果数量
        :return: 检索结果列表
        """
        if not self._knowledge_base:
            return []
        
        try:
            # 使用agno知识库进行检索
            if hasattr(self._knowledge_base, 'search'):
                results = self._knowledge_base.search(query, top_k=top_k)
                return results if results else []
            return []
        except Exception as e:
            print(f"知识库检索失败: {e}")
            return []
    
    def evaluate(self, context: EvaluationContext) -> EvaluationOutput:
        """
        执行评估（子类需要重写此方法）
        
        :param context: 评估上下文
        :return: 评估输出
        """
        raise NotImplementedError("子类必须实现 evaluate 方法")
    
    def get_info(self) -> Dict[str, Any]:
        """
        获取Agent信息
        
        :return: Agent信息字典
        """
        return {
            "agent_id": self._agent_id,
            "name": self._name,
            "agent_type": self._agent_type.value,
            "status": self._status.value,
            "created_at": self._created_at.isoformat(),
            "last_used_at": self._last_used_at.isoformat() if self._last_used_at else None,
            "usage_count": self._usage_count,
            "error_count": self._error_count,
            "model_name": self._config.model_name,
            "model_provider": self._config.model_provider,
            "is_available": self.is_available
        }
    
    def reset(self) -> None:
        """重置Agent状态"""
        self._status = AgentStatus.IDLE
        self._error_count = 0
    
    def shutdown(self) -> None:
        """关闭Agent"""
        self._status = AgentStatus.OFFLINE
        self._agent = None


class FeasibilityEvaluationAgent(BaseEvaluationAgent):
    """可行性评估Agent"""
    
    SYSTEM_PROMPT = """你是一位资深的可行性评估专家，擅长从技术、操作、财务和时间四个维度评估方案的可行性。

评估原则：
1. 客观公正：基于方案内容进行客观分析
2. 多维度：综合考虑技术可行性、操作可行性、财务可行性和时间可行性
3. 数据支撑：评估结论要有合理依据

输出要求：
必须输出JSON格式，包含以下字段：
{
  "score": 综合得分(0-100),
  "level": "excellent|good|average|poor|critical",
  "technical_feasibility": 技术可行性得分(0-100),
  "operational_feasibility": 操作可行性得分(0-100),
  "financial_feasibility": 财务可行性得分(0-100),
  "timeline_feasibility": 时间可行性得分(0-100),
  "summary": "评估摘要",
  "recommendations": ["建议1", "建议2", ...]
}
"""
    
    def __init__(self, config: AgentConfig):
        config.agent_type = AgentType.FEASIBILITY
        if not config.system_prompt:
            config.system_prompt = self.SYSTEM_PROMPT
        super().__init__(config)
    
    def evaluate(self, context: EvaluationContext) -> EvaluationOutput:
        """执行可行性评估"""
        prompt = f"""请对以下方案进行可行性评估：

方案ID: {context.solution_id}
方案名称: {context.solution_name}
方案内容: {context.solution_content}

请输出JSON格式的评估结果。"""
        
        response = self.call_llm(prompt)
        
        # 解析响应
        import json
        try:
            # 提取JSON
            start_idx = response.find('{')
            end_idx = response.rfind('}')
            if start_idx != -1 and end_idx != -1:
                data = json.loads(response[start_idx:end_idx+1])
            else:
                data = json.loads(response)
            
            return EvaluationOutput(
                agent_id=self._agent_id,
                solution_id=context.solution_id,
                dimension="feasibility",
                score=data.get('score', 50),
                level=data.get('level', 'average'),
                summary=data.get('summary', ''),
                details={
                    "technical_feasibility": data.get('technical_feasibility'),
                    "operational_feasibility": data.get('operational_feasibility'),
                    "financial_feasibility": data.get('financial_feasibility'),
                    "timeline_feasibility": data.get('timeline_feasibility')
                },
                recommendations=data.get('recommendations', [])
            )
        except Exception as e:
            return EvaluationOutput(
                agent_id=self._agent_id,
                solution_id=context.solution_id,
                dimension="feasibility",
                score=50,
                level="average",
                summary=f"评估解析失败: {str(e)}",
                recommendations=["建议重新评估"]
            )


class RiskEvaluationAgent(BaseEvaluationAgent):
    """风险评估Agent"""
    
    SYSTEM_PROMPT = """你是一位资深的风险评估专家，擅长识别和评估方案中的潜在风险。

评估原则：
1. 全面识别：识别技术风险、管理风险、财务风险、外部风险等
2. 量化评估：对风险进行量化评分
3. 提出对策：针对识别的风险提出缓解措施

输出要求：
必须输出JSON格式，包含以下字段：
{
  "score": 风险评估得分(0-100，分数越高表示风险越低),
  "level": "excellent|good|average|poor|critical",
  "risks": [
    {"name": "风险名称", "probability": "高/中/低", "impact": "高/中/低", "description": "风险描述"}
  ],
  "summary": "评估摘要",
  "mitigation_strategies": ["缓解策略1", "缓解策略2", ...]
}
"""
    
    def __init__(self, config: AgentConfig):
        config.agent_type = AgentType.RISK
        if not config.system_prompt:
            config.system_prompt = self.SYSTEM_PROMPT
        super().__init__(config)
    
    def evaluate(self, context: EvaluationContext) -> EvaluationOutput:
        """执行风险评估"""
        prompt = f"""请对以下方案进行风险评估：

方案ID: {context.solution_id}
方案名称: {context.solution_name}
方案内容: {context.solution_content}

请输出JSON格式的评估结果。"""
        
        response = self.call_llm(prompt)
        
        import json
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
                dimension="risk",
                score=data.get('score', 50),
                level=data.get('level', 'average'),
                summary=data.get('summary', ''),
                details={"risks": data.get('risks', [])},
                recommendations=data.get('mitigation_strategies', [])
            )
        except Exception as e:
            return EvaluationOutput(
                agent_id=self._agent_id,
                solution_id=context.solution_id,
                dimension="risk",
                score=50,
                level="average",
                summary=f"评估解析失败: {str(e)}",
                recommendations=["建议重新评估"]
            )
