"""大语言模型客户端模块

提供统一的大模型调用接口，支持不同的大模型实现。
遵循工厂模式，通过配置文件动态创建具体的大模型客户端。

使用Pydantic进行数据模型定义和验证。
"""

import json
import logging
import os
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Type
from pydantic import BaseModel, Field, field_validator
import httpx

# 模块日志记录器
logger = logging.getLogger(__name__)


# =============================================================================
# 数据模型定义
# =============================================================================

class LLMRequest(BaseModel):
    """大模型请求对象
    
    使用Pydantic进行数据验证和约束。
    
    :param prompt: 提示词
    :param system_prompt: 系统提示词（可选）
    :param temperature: 温度参数，控制随机性（0.0-2.0）
    :param max_tokens: 最大token数（可选）
    :param context: 上下文对话列表（可选）
    """
    prompt: str = Field(description="提示词")
    system_prompt: Optional[str] = Field(default=None, description="系统提示词")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="温度参数")
    max_tokens: Optional[int] = Field(default=None, ge=1, description="最大token数")
    context: Optional[List[Dict[str, str]]] = Field(default=None, description="上下文对话")
    
    @field_validator('prompt')
    @classmethod
    def prompt_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("提示词不能为空")
        return v.strip()


class LLMResponse(BaseModel):
    """大模型响应对象
    
    使用Pydantic进行数据验证和约束。
    
    :param content: 响应内容
    :param usage: token使用量信息
    :param model: 使用的模型名称
    :param finish_reason: 完成原因
    """
    content: str = Field(description="响应内容")
    usage: Optional[Dict[str, Any]] = Field(default=None, description="token使用量")
    model: Optional[str] = Field(default=None, description="使用的模型")
    finish_reason: Optional[str] = Field(default=None, description="完成原因")


class OllamaConfig(BaseModel):
    """Ollama配置模型
    
    :param base_url: Ollama服务地址
    :param model: 模型名称
    :param timeout: 超时时间（秒）
    :param stream: 是否使用流式输出
    """
    base_url: str = Field(default="http://localhost:11434", description="Ollama服务地址")
    model: str = Field(default="deepseek-r1:latest", description="模型名称")
    timeout: int = Field(default=120, ge=1, description="超时时间（秒）")
    stream: bool = Field(default=False, description="是否使用流式输出")


class OpenAIConfig(BaseModel):
    """OpenAI配置模型
    
    :param api_key: API密钥
    :param base_url: API地址
    :param model: 模型名称
    :param timeout: 超时时间（秒）
    """
    api_key: str = Field(default="", description="API密钥")
    base_url: str = Field(default="https://api.openai.com/v1", description="API地址")
    model: str = Field(default="gpt-4", description="模型名称")
    timeout: int = Field(default=60, ge=1, description="超时时间（秒）")


class MockConfig(BaseModel):
    """模拟客户端配置模型
    
    :param enabled: 是否启用模拟模式
    :param responses: 自定义模拟响应
    """
    enabled: bool = Field(default=True, description="是否启用模拟模式")
    responses: Dict[str, str] = Field(default_factory=dict, description="自定义模拟响应")


class LLMConfig(BaseModel):
    """LLM配置主模型
    
    :param client_type: 客户端类型（ollama/openai/mock）
    :param ollama: Ollama配置
    :param openai: OpenAI配置
    :param mock: 模拟客户端配置
    """
    client_type: str = Field(default="mock", description="客户端类型")
    ollama: OllamaConfig = Field(default_factory=OllamaConfig, description="Ollama配置")
    openai: OpenAIConfig = Field(default_factory=OpenAIConfig, description="OpenAI配置")
    mock: MockConfig = Field(default_factory=MockConfig, description="模拟客户端配置")


# =============================================================================
# 抽象基类
# =============================================================================

class LLMClient(ABC):
    """
    大语言模型客户端抽象基类
    
    定义统一的大模型调用接口，具体实现类需要继承此类并实现 call 方法。
    遵循开闭原则，便于扩展新的模型提供商。
    
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
        
        默认实现：简单重试策略，每次重试间隔相同。
        子类可覆盖以实现更复杂的重试策略（如指数退避）。
        
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
                logger.warning(f"大模型调用失败（第{attempt + 1}次尝试）: {str(e)}")
                if attempt < max_retries - 1:
                    continue
        raise last_error
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"


# =============================================================================
# 具体实现类
# =============================================================================

class OllamaLLMClient(LLMClient):
    """
    Ollama大模型客户端
    
    连接到本地运行的Ollama服务，支持DeepSeek、Llama等多种开源模型。
    默认使用 deepseek-r1:latest 模型。
    
    :param base_url: Ollama服务地址
    :param model: 模型名称
    :param timeout: 请求超时时间（秒）
    :param stream: 是否使用流式输出
    """
    
    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "deepseek-r1:latest",
        timeout: int = 120,
        stream: bool = False
    ):
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.timeout = timeout
        self.stream = stream
        self._client: Optional[httpx.Client] = None
        logger.info(f"初始化OllamaLLMClient: base_url={self.base_url}, model={self.model}")
    
    def _get_client(self) -> httpx.Client:
        """获取HTTP客户端（延迟初始化）"""
        if self._client is None:
            self._client = httpx.Client(
                base_url=self.base_url,
                timeout=self.timeout,
                follow_redirects=True
            )
        return self._client
    
    def call(self, request: LLMRequest) -> LLMResponse:
        """
        调用Ollama大模型
        
        :param request: 大模型请求对象
        :return: 大模型响应对象
        :raises httpx.HTTPError: 请求失败时抛出
        """
        # 构建消息列表
        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.prompt})
        
        # 构建请求体
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": self.stream
        }
        
        if request.temperature is not None:
            payload["temperature"] = request.temperature
        if request.max_tokens is not None:
            payload["options"] = {"num_predict": request.max_tokens}
        
        logger.debug(f"Ollama请求: {json.dumps(payload, ensure_ascii=False, indent=2)}")
        
        try:
            client = self._get_client()
            response = client.post("/api/chat", json=payload)
            response.raise_for_status()
            
            result = response.json()
            logger.debug(f"Ollama响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
            # 提取响应内容
            content = ""
            if "message" in result and "content" in result["message"]:
                content = result["message"]["content"]
            
            return LLMResponse(
                content=content,
                usage=result.get("usage"),
                model=result.get("model", self.model),
                finish_reason=result.get("done_reason")
            )
        except httpx.HTTPError as e:
            logger.error(f"Ollama请求失败: {str(e)}")
            raise
    
    def disconnect(self) -> None:
        """关闭HTTP客户端连接"""
        if self._client is not None:
            self._client.close()
            self._client = None
            logger.debug("Ollama连接已关闭")
    
    def __del__(self):
        """析构时确保关闭连接"""
        self.disconnect()


class OpenAIClient(LLMClient):
    """
    OpenAI大模型客户端
    
    连接到OpenAI API或兼容的代理服务（如vLLM）。
    
    :param api_key: API密钥
    :param base_url: API地址
    :param model: 模型名称
    :param timeout: 请求超时时间（秒）
    """
    
    def __init__(
        self,
        api_key: str = "",
        base_url: str = "https://api.openai.com/v1",
        model: str = "gpt-4",
        timeout: int = 60
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.timeout = timeout
        self._client: Optional[httpx.Client] = None
        logger.info(f"初始化OpenAIClient: base_url={self.base_url}, model={self.model}")
    
    def _get_client(self) -> httpx.Client:
        """获取HTTP客户端（延迟初始化）"""
        if self._client is None:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            self._client = httpx.Client(
                base_url=self.base_url,
                timeout=self.timeout,
                headers=headers,
                follow_redirects=True
            )
        return self._client
    
    def call(self, request: LLMRequest) -> LLMResponse:
        """
        调用OpenAI大模型
        
        :param request: 大模型请求对象
        :return: 大模型响应对象
        :raises httpx.HTTPError: 请求失败时抛出
        """
        # 构建消息列表
        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.prompt})
        
        # 构建请求体
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": request.temperature
        }
        
        if request.max_tokens is not None:
            payload["max_tokens"] = request.max_tokens
        
        logger.debug(f"OpenAI请求: {json.dumps(payload, ensure_ascii=False, indent=2)}")
        
        try:
            client = self._get_client()
            response = client.post("/chat/completions", json=payload)
            response.raise_for_status()
            
            result = response.json()
            logger.debug(f"OpenAI响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
            # 提取响应内容
            content = ""
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0].get("message", {}).get("content", "")
            
            return LLMResponse(
                content=content,
                usage=result.get("usage"),
                model=result.get("model", self.model),
                finish_reason=result["choices"][0].get("finish_reason") if "choices" in result else None
            )
        except httpx.HTTPError as e:
            logger.error(f"OpenAI请求失败: {str(e)}")
            raise
    
    def disconnect(self) -> None:
        """关闭HTTP客户端连接"""
        if self._client is not None:
            self._client.close()
            self._client = None
            logger.debug("OpenAI连接已关闭")


class MockLLMClient(LLMClient):
    """
    模拟大模型客户端
    
    用于测试和开发环境，不调用真实的大模型API。
    根据提示词内容返回预设的模拟响应。
    
    :param responses: 自定义模拟响应字典
    """
    
    def __init__(self, responses: Optional[Dict[str, str]] = None):
        self._responses = responses or {}
        logger.info("初始化MockLLMClient（模拟模式）")
    
    def call(self, request: LLMRequest) -> LLMResponse:
        """
        模拟大模型调用
        
        根据提示词关键词匹配返回预设的模拟响应。
        
        :param request: 大模型请求对象
        :return: 模拟的大模型响应
        """
        # 根据提示词关键词返回模拟响应
        full_text = request.prompt.lower()
        if request.system_prompt:
            full_text += " " + request.system_prompt.lower()
        
        logger.debug(f"MockLLMClient处理请求: {request.prompt[:100]}...")
        
        # 优先匹配更具体的场景
        if "拆解" in full_text or "decompose" in full_text or "任务执行流程" in full_text:
            return self._mock_decompose_response()
        elif "理解" in full_text or "understand" in full_text or "提取结构化" in full_text:
            return self._mock_understand_response()
        elif "task_graph" in full_text or "任务图" in full_text:
            return self._mock_task_graph_response()
        else:
            # 尝试从自定义响应中匹配
            for key, response in self._responses.items():
                if key.lower() in full_text:
                    return LLMResponse(
                        content=response,
                        model="mock",
                        finish_reason="stop"
                    )
            
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


# =============================================================================
# 工厂类
# =============================================================================

class LLMClientFactory:
    """
    大模型客户端工厂类
    
    遵循工厂模式，根据配置动态创建具体的大模型客户端实例。
    支持单例模式，确保同一配置只创建一个客户端实例。
    
    配置通过 llm_config.json 文件读取。
    
    示例用法：
        # 获取默认配置的客户端
        client = LLMClientFactory.create_client()
        
        # 获取Ollama客户端
        client = LLMClientFactory.create_client(client_type="ollama")
        
        # 强制创建新实例
        client = LLMClientFactory.create_client(force_new=True)
    """
    
    _config: Optional[LLMConfig] = None
    _instance: Optional[LLMClient] = None
    _config_path: str = os.path.join(os.path.dirname(__file__), "llm_config.json")
    
    # 客户端类型注册表
    _registry: Dict[str, Type[LLMClient]] = {
        "ollama": OllamaLLMClient,
        "openai": OpenAIClient,
        "mock": MockLLMClient
    }
    
    @classmethod
    def register_client(cls, client_type: str, client_class: Type[LLMClient]) -> None:
        """
        注册新的客户端类型
        
        :param client_type: 客户端类型标识
        :param client_class: 客户端类
        """
        if not issubclass(client_class, LLMClient):
            raise TypeError(f"{client_class} 必须继承自 LLMClient")
        cls._registry[client_type] = client_class
        logger.info(f"注册客户端类型: {client_type} -> {client_class.__name__}")
    
    @classmethod
    def _load_config(cls) -> LLMConfig:
        """
        从配置文件加载配置
        
        :return: LLM配置对象
        """
        if cls._config is None:
            try:
                with open(cls._config_path, "r", encoding="utf-8") as f:
                    config_data = json.load(f)
                    cls._config = LLMConfig(**config_data.get("llm_client", {}))
                    logger.info(f"从配置文件加载LLM配置: {cls._config.client_type}")
            except FileNotFoundError:
                logger.warning(f"配置文件不存在，使用默认配置: {cls._config_path}")
                cls._config = LLMConfig()
            except json.JSONDecodeError as e:
                logger.error(f"配置文件解析失败: {str(e)}，使用默认配置")
                cls._config = LLMConfig()
            except Exception as e:
                logger.error(f"加载配置失败: {str(e)}，使用默认配置")
                cls._config = LLMConfig()
        return cls._config
    
    @classmethod
    def set_config(cls, config: LLMConfig) -> None:
        """
        设置LLM配置
        
        :param config: LLM配置对象
        """
        cls._config = config
        # 设置后清除单例，下次创建会使用新配置
        if cls._instance is not None:
            if hasattr(cls._instance, 'disconnect'):
                cls._instance.disconnect()
            cls._instance = None
        logger.info(f"LLM配置已更新: client_type={config.client_type}")
    
    @classmethod
    def set_config_path(cls, config_path: str) -> None:
        """
        设置配置文件路径
        
        :param config_path: 配置文件路径
        """
        cls._config_path = config_path
        cls._config = None  # 清除缓存的配置
        logger.info(f"配置文件路径已更新: {config_path}")
    
    @classmethod
    def get_config(cls) -> LLMConfig:
        """
        获取当前配置
        
        :return: LLM配置对象
        """
        return cls._load_config()
    
    @classmethod
    def create_client(
        cls,
        client_type: str = None,
        force_new: bool = False,
        **kwargs
    ) -> LLMClient:
        """
        创建大模型客户端实例
        
        :param client_type: 客户端类型（可选，默认从配置读取）
        :param force_new: 是否强制创建新实例（默认False，返回单例）
        :param kwargs: 额外的客户端参数，会覆盖配置中的默认值
        :return: 大模型客户端实例
        """
        config = cls._load_config()
        
        # 确定客户端类型
        if client_type is None:
            client_type = config.client_type
        
        # 获取客户端类
        if client_type not in cls._registry:
            available = list(cls._registry.keys())
            raise ValueError(f"未知的客户端类型: {client_type}，可用类型: {available}")
        
        client_class = cls._registry[client_type]
        
        # 单例模式：除非强制创建新实例
        if not force_new and cls._instance is not None:
            existing_type = type(cls._instance).__name__
            if existing_type == client_class.__name__:
                logger.debug("返回现有客户端实例")
                return cls._instance
        
        # 创建新实例
        logger.info(f"创建新客户端实例: {client_class.__name__}")
        
        if client_type == "ollama":
            instance = client_class(
                base_url=kwargs.get("base_url", config.ollama.base_url),
                model=kwargs.get("model", config.ollama.model),
                timeout=kwargs.get("timeout", config.ollama.timeout),
                stream=kwargs.get("stream", config.ollama.stream)
            )
        elif client_type == "openai":
            instance = client_class(
                api_key=kwargs.get("api_key", config.openai.api_key),
                base_url=kwargs.get("base_url", config.openai.base_url),
                model=kwargs.get("model", config.openai.model),
                timeout=kwargs.get("timeout", config.openai.timeout)
            )
        elif client_type == "mock":
            instance = client_class(
                responses=kwargs.get("responses", config.mock.responses)
            )
        else:
            instance = client_class()
        
        if not force_new:
            cls._instance = instance
        
        return instance
    
    @classmethod
    def get_instance(cls) -> Optional[LLMClient]:
        """
        获取当前实例（不创建新实例）
        
        :return: 当前实例，不存在则返回None
        """
        return cls._instance
    
    @classmethod
    def close(cls) -> None:
        """关闭并清理客户端实例"""
        if cls._instance is not None:
            if hasattr(cls._instance, 'disconnect'):
                cls._instance.disconnect()
            cls._instance = None
            logger.info("LLM客户端实例已关闭")
    
    @classmethod
    def reset(cls) -> None:
        """重置工厂状态（清除配置和实例）"""
        cls._config = None
        cls.close()
        logger.info("LLMClientFactory已重置")


# =============================================================================
# 模块导出
# =============================================================================

__all__ = [
    # 数据模型
    "LLMRequest",
    "LLMResponse",
    "OllamaConfig",
    "OpenAIConfig",
    "MockConfig",
    "LLMConfig",
    # 抽象基类
    "LLMClient",
    # 具体实现
    "OllamaLLMClient",
    "OpenAIClient",
    "MockLLMClient",
    # 工厂类
    "LLMClientFactory",
]
