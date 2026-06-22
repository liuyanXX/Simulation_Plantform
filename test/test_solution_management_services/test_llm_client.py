import os
import sys
import logging
import unittest
import json
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
logs_dir = os.path.join(project_root, 'logs')
os.makedirs(logs_dir, exist_ok=True)

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

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(logs_dir, 'test_llm_client.log'), encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TestLLMRequest(unittest.TestCase):
    """测试LLMRequest模型"""

    def test_01_create_request(self):
        """测试创建请求对象"""
        logger.info("测试01: 创建LLMRequest")
        
        request = LLMRequest(
            prompt="测试提示词",
            system_prompt="系统提示词",
            temperature=0.5,
            max_tokens=1000
        )
        
        self.assertEqual(request.prompt, "测试提示词")
        self.assertEqual(request.system_prompt, "系统提示词")
        self.assertEqual(request.temperature, 0.5)
        self.assertEqual(request.max_tokens, 1000)
        
        logger.info(f"  ✓ 创建成功: {request.prompt}")

    def test_02_request_defaults(self):
        """测试默认值"""
        logger.info("测试02: LLMRequest默认值")
        
        request = LLMRequest(prompt="仅提示词")
        
        self.assertEqual(request.system_prompt, None)
        self.assertEqual(request.temperature, 0.7)
        self.assertEqual(request.max_tokens, None)
        self.assertEqual(request.context, None)
        
        logger.info("  ✓ 默认值正确")


class TestLLMResponse(unittest.TestCase):
    """测试LLMResponse模型"""

    def test_01_create_response(self):
        """测试创建响应对象"""
        logger.info("测试01: 创建LLMResponse")
        
        usage = {"prompt_tokens": 100, "completion_tokens": 200, "total_tokens": 300}
        response = LLMResponse(
            content="测试响应内容",
            usage=usage,
            model="test-model",
            finish_reason="stop"
        )
        
        self.assertEqual(response.content, "测试响应内容")
        self.assertEqual(response.usage, usage)
        self.assertEqual(response.model, "test-model")
        self.assertEqual(response.finish_reason, "stop")
        
        logger.info("  ✓ 创建成功")

    def test_02_response_defaults(self):
        """测试默认值"""
        logger.info("测试02: LLMResponse默认值")
        
        response = LLMResponse(content="仅内容")
        
        self.assertEqual(response.usage, None)
        self.assertEqual(response.model, None)
        self.assertEqual(response.finish_reason, None)
        
        logger.info("  ✓ 默认值正确")


class TestMockLLMClient(unittest.TestCase):
    """测试MockLLMClient"""

    @classmethod
    def setUpClass(cls):
        """设置测试类"""
        logger.info("=" * 60)
        logger.info("开始测试MockLLMClient")
        logger.info("=" * 60)
        cls.client = MockLLMClient()

    def test_01_call_understand(self):
        """测试理解场景调用"""
        logger.info("测试01: 理解场景模拟响应")
        
        request = LLMRequest(prompt="请理解这个方案文档，提取结构化信息")
        response = self.client.call(request)
        
        self.assertIsNotNone(response.content)
        self.assertEqual(response.model, "mock")
        self.assertEqual(response.finish_reason, "stop")
        
        try:
            data = json.loads(response.content)
            self.assertIn("solution_id", data)
            self.assertIn("name", data)
            self.assertIn("objectives", data)
            logger.info(f"  ✓ 响应包含结构化方案数据: {data.get('name')}")
        except json.JSONDecodeError:
            logger.error("  ✗ 响应不是有效JSON")
            self.fail("响应不是有效JSON")

    def test_02_call_decompose(self):
        """测试拆解场景调用"""
        logger.info("测试02: 拆解场景模拟响应")
        
        request = LLMRequest(prompt="请将这个方案拆解为任务执行流程")
        response = self.client.call(request)
        
        self.assertIsNotNone(response.content)
        self.assertEqual(response.model, "mock")
        
        try:
            data = json.loads(response.content)
            self.assertIn("tasks", data)
            self.assertIn("graph_id", data)
            self.assertTrue(len(data.get("tasks", [])) > 0)
            logger.info(f"  ✓ 响应包含任务数据: {len(data.get('tasks', []))}个任务")
        except json.JSONDecodeError:
            logger.error("  ✗ 响应不是有效JSON")
            self.fail("响应不是有效JSON")

    def test_03_call_default(self):
        """测试默认场景调用"""
        logger.info("测试03: 默认场景模拟响应")
        
        request = LLMRequest(prompt="这是一个普通请求")
        response = self.client.call(request)
        
        self.assertIsNotNone(response.content)
        self.assertIn("模拟响应", response.content)
        logger.info("  ✓ 默认响应正常")

    def test_04_call_with_retry(self):
        """测试带重试机制的调用"""
        logger.info("测试04: 带重试机制的调用")
        
        request = LLMRequest(prompt="测试重试")
        response = self.client.call_with_retry(request, max_retries=3)
        
        self.assertIsNotNone(response)
        logger.info("  ✓ 重试机制正常")

    def test_05_call_with_system_prompt(self):
        """测试带系统提示词的调用"""
        logger.info("测试05: 带系统提示词的调用")
        
        request = LLMRequest(
            prompt="分析文档",
            system_prompt="你是一个专业的文档分析专家"
        )
        response = self.client.call(request)
        
        self.assertIsNotNone(response.content)
        logger.info("  ✓ 系统提示词生效")


if __name__ == '__main__':
    os.makedirs('logs', exist_ok=True)
    unittest.main(verbosity=2)