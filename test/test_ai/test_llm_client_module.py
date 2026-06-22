"""智能模型连接模块测试

测试LLMClient模块的各个组件：
- 数据模型测试
- 抽象基类测试
- Mock客户端测试
- Ollama客户端测试
- OpenAI客户端测试
- 工厂类测试
"""

import os
import sys
import logging
import unittest
import json
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ai_modules.basic.llm_client import (
    LLMClient,
    LLMRequest,
    LLMResponse,
    MockLLMClient,
    OllamaLLMClient,
    OpenAIClient,
    LLMClientFactory,
    LLMConfig,
    OllamaConfig,
    OpenAIConfig,
    MockConfig
)

# 配置日志
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
logs_dir = os.path.join(project_root, 'logs')
os.makedirs(logs_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(logs_dir, 'test_llm_client_module.log'), encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# =============================================================================
# 数据模型测试
# =============================================================================

class TestLLMRequest(unittest.TestCase):
    """测试LLMRequest数据模型"""
    
    def test_create_valid_request(self):
        """测试创建有效的请求"""
        request = LLMRequest(prompt="测试提示词")
        self.assertEqual(request.prompt, "测试提示词")
        self.assertIsNone(request.system_prompt)
        self.assertEqual(request.temperature, 0.7)
        self.assertIsNone(request.max_tokens)
        self.assertIsNone(request.context)
        logger.info("创建有效请求测试通过")
    
    def test_request_with_all_fields(self):
        """测试创建包含所有字段的请求"""
        request = LLMRequest(
            prompt="测试提示词",
            system_prompt="系统提示词",
            temperature=0.5,
            max_tokens=1000,
            context=[{"role": "user", "content": "你好"}]
        )
        self.assertEqual(request.prompt, "测试提示词")
        self.assertEqual(request.system_prompt, "系统提示词")
        self.assertEqual(request.temperature, 0.5)
        self.assertEqual(request.max_tokens, 1000)
        self.assertEqual(len(request.context), 1)
        logger.info("包含所有字段的请求测试通过")
    
    def test_prompt_validation(self):
        """测试提示词验证"""
        with self.assertRaises(ValueError):
            LLMRequest(prompt="")
        with self.assertRaises(ValueError):
            LLMRequest(prompt="   ")
        logger.info("提示词验证测试通过")
    
    def test_temperature_constraints(self):
        """测试温度参数约束"""
        # 有效范围
        request = LLMRequest(prompt="test", temperature=0.0)
        self.assertEqual(request.temperature, 0.0)
        
        request = LLMRequest(prompt="test", temperature=2.0)
        self.assertEqual(request.temperature, 2.0)
        
        # 无效范围
        with self.assertRaises(Exception):
            LLMRequest(prompt="test", temperature=-0.1)
        
        with self.assertRaises(Exception):
            LLMRequest(prompt="test", temperature=2.1)
        logger.info("温度参数约束测试通过")


class TestLLMResponse(unittest.TestCase):
    """测试LLMResponse数据模型"""
    
    def test_create_response(self):
        """测试创建响应"""
        response = LLMResponse(
            content="测试响应内容",
            model="gpt-4",
            finish_reason="stop"
        )
        self.assertEqual(response.content, "测试响应内容")
        self.assertEqual(response.model, "gpt-4")
        self.assertEqual(response.finish_reason, "stop")
        self.assertIsNone(response.usage)
        logger.info("创建响应测试通过")
    
    def test_response_with_usage(self):
        """测试包含使用量的响应"""
        response = LLMResponse(
            content="测试响应",
            usage={"prompt_tokens": 10, "completion_tokens": 20}
        )
        self.assertIsNotNone(response.usage)
        self.assertEqual(response.usage["prompt_tokens"], 10)
        logger.info("包含使用量的响应测试通过")


class TestConfigModels(unittest.TestCase):
    """测试配置模型"""
    
    def test_ollama_config_defaults(self):
        """测试Ollama配置默认值"""
        config = OllamaConfig()
        self.assertEqual(config.base_url, "http://localhost:11434")
        self.assertEqual(config.model, "deepseek-r1:latest")
        self.assertEqual(config.timeout, 120)
        self.assertFalse(config.stream)
        logger.info("Ollama配置默认值测试通过")
    
    def test_ollama_config_custom(self):
        """测试Ollama自定义配置"""
        config = OllamaConfig(
            base_url="http://192.168.1.100:11434",
            model="llama2:latest",
            timeout=60,
            stream=True
        )
        self.assertEqual(config.base_url, "http://192.168.1.100:11434")
        self.assertEqual(config.model, "llama2:latest")
        self.assertEqual(config.timeout, 60)
        self.assertTrue(config.stream)
        logger.info("Ollama自定义配置测试通过")
    
    def test_openai_config(self):
        """测试OpenAI配置"""
        config = OpenAIConfig(
            api_key="test-key-123",
            base_url="https://api.test.com/v1",
            model="gpt-3.5-turbo",
            timeout=30
        )
        self.assertEqual(config.api_key, "test-key-123")
        self.assertEqual(config.model, "gpt-3.5-turbo")
        logger.info("OpenAI配置测试通过")
    
    def test_mock_config(self):
        """测试Mock配置"""
        config = MockConfig(
            enabled=True,
            responses={"key": "value"}
        )
        self.assertTrue(config.enabled)
        self.assertEqual(config.responses["key"], "value")
        logger.info("Mock配置测试通过")
    
    def test_llm_config(self):
        """测试主配置模型"""
        config = LLMConfig(
            client_type="ollama",
            ollama=OllamaConfig(model="qwen:latest"),
            openai=OpenAIConfig(model="gpt-4")
        )
        self.assertEqual(config.client_type, "ollama")
        self.assertEqual(config.ollama.model, "qwen:latest")
        self.assertEqual(config.openai.model, "gpt-4")
        logger.info("主配置模型测试通过")


# =============================================================================
# 客户端实现测试
# =============================================================================

class TestMockLLMClient(unittest.TestCase):
    """测试MockLLMClient"""
    
    def setUp(self):
        """设置测试"""
        self.client = MockLLMClient()
    
    def test_call_understand_prompt(self):
        """测试理解提示词"""
        request = LLMRequest(
            prompt="理解这个方案",
            system_prompt="你是一个方案分析助手"
        )
        response = self.client.call(request)
        self.assertIsInstance(response, LLMResponse)
        self.assertEqual(response.model, "mock")
        self.assertIn("solution_id", response.content)
        logger.info("理解提示词测试通过")
    
    def test_call_decompose_prompt(self):
        """测试拆解提示词"""
        request = LLMRequest(prompt="拆解这个方案到任务")
        response = self.client.call(request)
        self.assertIsInstance(response, LLMResponse)
        self.assertIn("tasks", response.content)
        self.assertIn("graph_id", response.content)
        logger.info("拆解提示词测试通过")
    
    def test_call_unknown_prompt(self):
        """测试未知提示词"""
        request = LLMRequest(prompt="这是一个随机的请求")
        response = self.client.call(request)
        self.assertIsInstance(response, LLMResponse)
        self.assertIn("模拟响应", response.content)
        logger.info("未知提示词测试通过")
    
    def test_custom_responses(self):
        """测试自定义模拟响应"""
        custom_responses = {
            "特定关键词": "这是自定义响应内容"
        }
        client = MockLLMClient(responses=custom_responses)
        request = LLMRequest(prompt="这个请求包含特定关键词")
        response = client.call(request)
        self.assertEqual(response.content, "这是自定义响应内容")
        logger.info("自定义模拟响应测试通过")
    
    def test_call_with_retry(self):
        """测试带重试的调用"""
        request = LLMRequest(prompt="测试")
        response = self.client.call_with_retry(request, max_retries=2)
        self.assertIsInstance(response, LLMResponse)
        logger.info("带重试的调用测试通过")


class TestOllamaLLMClient(unittest.TestCase):
    """测试OllamaLLMClient"""
    
    def test_init_with_defaults(self):
        """测试默认初始化"""
        client = OllamaLLMClient()
        self.assertEqual(client.base_url, "http://localhost:11434")
        self.assertEqual(client.model, "deepseek-r1:latest")
        self.assertEqual(client.timeout, 120)
        self.assertFalse(client.stream)
        logger.info("Ollama默认初始化测试通过")
    
    def test_init_with_custom(self):
        """测试自定义初始化"""
        client = OllamaLLMClient(
            base_url="http://192.168.1.100:11434",
            model="llama2:latest",
            timeout=60,
            stream=True
        )
        self.assertEqual(client.base_url, "http://192.168.1.100:11434")
        self.assertEqual(client.model, "llama2:latest")
        self.assertEqual(client.timeout, 60)
        self.assertTrue(client.stream)
        logger.info("Ollama自定义初始化测试通过")
    
    def test_disconnect(self):
        """测试断开连接"""
        client = OllamaLLMClient()
        client.disconnect()
        self.assertIsNone(client._client)
        logger.info("断开连接测试通过")
    
    def test_call_without_server(self):
        """测试连接失败情况（无Ollama服务）"""
        client = OllamaLLMClient(base_url="http://localhost:19999", timeout=2)
        request = LLMRequest(prompt="测试")
        with self.assertRaises(Exception):
            client.call(request)
        logger.info("连接失败测试通过（预期异常）")


class TestOpenAIClient(unittest.TestCase):
    """测试OpenAIClient"""
    
    def test_init_with_defaults(self):
        """测试默认初始化"""
        client = OpenAIClient()
        self.assertEqual(client.base_url, "https://api.openai.com/v1")
        self.assertEqual(client.model, "gpt-4")
        self.assertEqual(client.timeout, 60)
        logger.info("OpenAI默认初始化测试通过")
    
    def test_init_with_custom(self):
        """测试自定义初始化"""
        client = OpenAIClient(
            api_key="test-key",
            base_url="https://api.test.com/v1",
            model="gpt-3.5-turbo",
            timeout=30
        )
        self.assertEqual(client.api_key, "test-key")
        self.assertEqual(client.base_url, "https://api.test.com/v1")
        self.assertEqual(client.model, "gpt-3.5-turbo")
        self.assertEqual(client.timeout, 30)
        logger.info("OpenAI自定义初始化测试通过")


# =============================================================================
# 工厂类测试
# =============================================================================

class TestLLMClientFactory(unittest.TestCase):
    """测试LLMClientFactory"""
    
    def setUp(self):
        """设置测试"""
        LLMClientFactory.reset()
    
    def tearDown(self):
        """清理"""
        LLMClientFactory.reset()
    
    def test_create_mock_client(self):
        """测试创建Mock客户端"""
        client = LLMClientFactory.create_client(client_type="mock")
        self.assertIsInstance(client, MockLLMClient)
        self.assertIsInstance(LLMClientFactory.get_instance(), MockLLMClient)
        logger.info("创建Mock客户端测试通过")
    
    def test_create_ollama_client(self):
        """测试创建Ollama客户端"""
        client = LLMClientFactory.create_client(client_type="ollama")
        self.assertIsInstance(client, OllamaLLMClient)
        logger.info("创建Ollama客户端测试通过")
    
    def test_create_openai_client(self):
        """测试创建OpenAI客户端"""
        client = LLMClientFactory.create_client(client_type="openai")
        self.assertIsInstance(client, OpenAIClient)
        logger.info("创建OpenAI客户端测试通过")
    
    def test_singleton_pattern(self):
        """测试单例模式"""
        client1 = LLMClientFactory.create_client(client_type="mock")
        client2 = LLMClientFactory.create_client(client_type="mock")
        self.assertIs(client1, client2)
        logger.info("单例模式测试通过")
    
    def test_force_new_instance(self):
        """测试强制创建新实例"""
        client1 = LLMClientFactory.create_client(client_type="mock")
        client2 = LLMClientFactory.create_client(client_type="mock", force_new=True)
        self.assertIsNot(client1, client2)
        logger.info("强制创建新实例测试通过")
    
    def test_unknown_client_type(self):
        """测试未知客户端类型"""
        with self.assertRaises(ValueError):
            LLMClientFactory.create_client(client_type="unknown")
        logger.info("未知客户端类型测试通过（预期异常）")
    
    def test_register_client(self):
        """测试注册新客户端类型"""
        class CustomClient(LLMClient):
            def call(self, request: LLMRequest) -> LLMResponse:
                return LLMResponse(content="custom")
        
        LLMClientFactory.register_client("custom", CustomClient)
        client = LLMClientFactory.create_client(client_type="custom")
        self.assertIsInstance(client, CustomClient)
        logger.info("注册新客户端类型测试通过")
    
    def test_close_and_reset(self):
        """测试关闭和重置"""
        client = LLMClientFactory.create_client(client_type="mock")
        LLMClientFactory.close()
        self.assertIsNone(LLMClientFactory.get_instance())
        
        client = LLMClientFactory.create_client(client_type="ollama")
        LLMClientFactory.reset()
        self.assertIsNone(LLMClientFactory.get_instance())
        logger.info("关闭和重置测试通过")
    
    def test_config_loading(self):
        """测试配置加载"""
        config = LLMClientFactory.get_config()
        self.assertIsInstance(config, LLMConfig)
        self.assertIn(config.client_type, ["ollama", "openai", "mock"])
        logger.info("配置加载测试通过")
    
    def test_set_config(self):
        """测试设置配置"""
        new_config = LLMConfig(client_type="ollama")
        LLMClientFactory.set_config(new_config)
        config = LLMClientFactory.get_config()
        self.assertEqual(config.client_type, "ollama")
        logger.info("设置配置测试通过")


# =============================================================================
# 集成测试
# =============================================================================

class TestLLMClientIntegration(unittest.TestCase):
    """LLM客户端集成测试"""
    
    def setUp(self):
        """设置测试"""
        LLMClientFactory.reset()
    
    def tearDown(self):
        """清理"""
        LLMClientFactory.close()
    
    def test_config_and_factory_workflow(self):
        """测试配置和工厂工作流"""
        # 1. 获取当前配置
        config = LLMClientFactory.get_config()
        logger.info(f"当前配置类型: {config.client_type}")
        
        # 2. 创建客户端
        client = LLMClientFactory.create_client()
        self.assertIsInstance(client, LLMClient)
        logger.info(f"创建客户端: {type(client).__name__}")
        
        # 3. 使用客户端
        request = LLMRequest(prompt="测试提示词")
        response = client.call(request)
        self.assertIsInstance(response, LLMResponse)
        logger.info(f"收到响应: {response.model}")
        
        # 4. 切换到其他类型
        if isinstance(client, MockLLMClient):
            ollama_client = LLMClientFactory.create_client(
                client_type="ollama",
                force_new=True
            )
            self.assertIsInstance(ollama_client, OllamaLLMClient)
            logger.info("切换到Ollama客户端成功")
        
        logger.info("配置和工厂工作流测试通过")
    
    def test_multiple_client_types(self):
        """测试多种客户端类型切换"""
        # 创建所有类型的客户端
        mock_client = LLMClientFactory.create_client(client_type="mock", force_new=True)
        ollama_client = LLMClientFactory.create_client(client_type="ollama", force_new=True)
        openai_client = LLMClientFactory.create_client(client_type="openai", force_new=True)
        
        self.assertIsInstance(mock_client, MockLLMClient)
        self.assertIsInstance(ollama_client, OllamaLLMClient)
        self.assertIsInstance(openai_client, OpenAIClient)
        
        logger.info("多种客户端类型切换测试通过")
    
    def test_custom_parameters_override(self):
        """测试自定义参数覆盖"""
        client = LLMClientFactory.create_client(
            client_type="ollama",
            model="qwen:latest",
            timeout=300
        )
        self.assertEqual(client.model, "qwen:latest")
        self.assertEqual(client.timeout, 300)
        logger.info("自定义参数覆盖测试通过")


# =============================================================================
# 测试套件
# =============================================================================

def get_test_suite():
    """获取测试套件"""
    suite = unittest.TestSuite()
    
    # 数据模型测试
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestLLMRequest))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestLLMResponse))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestConfigModels))
    
    # 客户端实现测试
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestMockLLMClient))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestOllamaLLMClient))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestOpenAIClient))
    
    # 工厂类测试
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestLLMClientFactory))
    
    # 集成测试
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestLLMClientIntegration))
    
    return suite


if __name__ == "__main__":
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(get_test_suite())
    
    # 输出测试摘要
    print("\n" + "=" * 80)
    print("测试摘要")
    print("=" * 80)
    print(f"运行测试: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    print("=" * 80)
