"""大语言模型客户端模块

提供统一的大模型调用接口，支持不同的大模型实现。
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
import json


class LLMRequest(BaseModel):
    """大模型请求对象"""
    prompt: str = Field(description="提示词")
    system_prompt: Optional[str] = Field(default=None, description="系统提示词")
    temperature: float = Field(default=0.7, description="温度参数")
    max_tokens: Optional[int] = Field(default=None, description="最大token数")
    context: Optional[List[Dict[str, str]]] = Field(default=None, description="上下文对话")


class LLMResponse(BaseModel):
    """大模型响应对象"""
    content: str = Field(description="响应内容")
    usage: Optional[Dict[str, Any]] = Field(default=None, description="token使用量")
    model: Optional[str] = Field(default=None, description="使用的模型")
    finish_reason: Optional[str] = Field(default=None, description="完成原因")


class LLMClient(ABC):
    """
    大语言模型客户端抽象基类
    
    定义统一的大模型调用接口，具体实现类需要继承此类并实现 call 方法。
    
    示例用法：
        class OpenAIClient(LLMClient):
            def call(self, request: LLMRequest) -> LLMResponse:
                # 实现OpenAI API调用
                pass
    """
    
    @abstractmethod
    def call(self, request: LLMRequest) -> LLMResponse:
        """
        调用大模型
        
        :param request: 大模型请求对象
        :return: 大模型响应对象
        """
        pass
    
    def call_with_retry(self, request: LLMRequest, max_retries: int = 3) -> LLMResponse:
        """
        带重试机制的大模型调用
        
        :param request: 大模型请求对象
        :param max_retries: 最大重试次数
        :return: 大模型响应对象
        :raises Exception: 如果所有重试都失败
        """
        last_error = None
        for attempt in range(max_retries):
            try:
                return self.call(request)
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    continue
        raise last_error


class MockLLMClient(LLMClient):
    """
    模拟大模型客户端
    
    用于测试和开发环境，不调用真实的大模型API。
    根据提示词内容返回预设的模拟响应。
    """
    
    def __init__(self, mock_responses: Optional[Dict[str, str]] = None):
        self._mock_responses = mock_responses or {}
    
    def call(self, request: LLMRequest) -> LLMResponse:
        """
        模拟大模型调用
        
        :param request: 大模型请求对象
        :return: 模拟的大模型响应
        """
        # 根据提示词关键词返回模拟响应
        full_text = request.prompt.lower()
        if request.system_prompt:
            full_text += " " + request.system_prompt.lower()
        
        # 优先匹配更具体的场景
        if "拆解" in full_text or "decompose" in full_text or "任务执行流程" in full_text:
            return self._mock_decompose_response()
        elif "理解" in full_text or "understand" in full_text or "提取结构化" in full_text:
            return self._mock_understand_response()
        else:
            return LLMResponse(
                content="模拟响应：已收到请求，但未匹配到特定场景。",
                model="mock",
                finish_reason="stop"
            )
    
    def _mock_understand_response(self) -> LLMResponse:
        """模拟方案理解响应"""
        mock_data = {
            "solution_id": "SOL_MOCK_001",
            "name": "数字化转型实施方案",
            "version": "1.0",
            "status": "draft",
            "priority": "high",
            "purpose": "推动企业数字化转型，提升运营效率",
            "objectives": [
                "实现业务流程数字化",
                "建立数据驱动决策体系",
                "提升客户体验"
            ],
            "initiatives": [
                "引入云计算平台",
                "建设大数据分析系统"
            ],
            "working_mechanism": "项目制管理，跨部门协作",
            "organization": ["研发部", "运营部"],
            "personnel": ["张三", "李四"],
            "roles": ["项目经理", "技术负责人"],
            "work_content": "完成数字化转型的规划、实施和推广",
            "constraints": ["预算限制", "时间紧迫"],
            "risks": ["技术选型风险", "项目进度风险"],
            "issues": ["系统集成复杂度高"],
            "other_notes": "需要高层领导支持"
        }
        return LLMResponse(
            content=json.dumps(mock_data, ensure_ascii=False, indent=2),
            model="mock",
            finish_reason="stop"
        )
    
    def _mock_decompose_response(self) -> LLMResponse:
        """模拟方案拆解响应"""
        mock_data = {
            "tasks": [
                {
                    "task_id": "START001",
                    "task_name": "流程开始",
                    "task_type": "start",
                    "content": "数字化转型流程启动",
                    "execute_role": "SYSTEM",
                    "resource_consumption": 0.0,
                    "priority": "low",
                    "output_target_role": "PM",
                    "task_destinations": ["T001"]
                },
                {
                    "task_id": "T001",
                    "task_name": "需求分析",
                    "task_type": "normal",
                    "content": "分析业务需求，确定数字化转型的具体目标",
                    "execute_role": "PM",
                    "resource_consumption": 2.0,
                    "priority": "high",
                    "output_target_role": "DEV",
                    "task_destinations": ["T002"]
                },
                {
                    "task_id": "T002",
                    "task_name": "系统开发",
                    "task_type": "normal",
                    "content": "开发数字化平台系统",
                    "execute_role": "DEV",
                    "resource_consumption": 5.0,
                    "priority": "high",
                    "output_target_role": "TEST",
                    "task_destinations": ["T003"]
                },
                {
                    "task_id": "T003",
                    "task_name": "系统测试",
                    "task_type": "normal",
                    "content": "对开发的系统进行测试",
                    "execute_role": "TEST",
                    "resource_consumption": 2.0,
                    "priority": "high",
                    "output_target_role": "",
                    "task_destinations": ["END001"]
                },
                {
                    "task_id": "END001",
                    "task_name": "流程结束",
                    "task_type": "end",
                    "content": "数字化转型流程完成",
                    "execute_role": "SYSTEM",
                    "resource_consumption": 0.0,
                    "priority": "low",
                    "output_target_role": "",
                    "task_destinations": []
                }
            ],
            "graph_id": "GRAPH001",
            "graph_name": "数字化转型任务图谱"
        }
        return LLMResponse(
            content=json.dumps(mock_data, ensure_ascii=False, indent=2),
            model="mock",
            finish_reason="stop"
        )
    
    def _mock_task_graph_response(self) -> LLMResponse:
        """模拟任务图谱响应"""
        return self._mock_decompose_response()