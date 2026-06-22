"""测试BaseEvaluationAgent模块"""
import unittest
import logging
import os
import sys
from datetime import datetime
from typing import Dict, Any

# 配置日志
log_file = os.path.join("logs", "test_base_evaluation_agent.log")
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestBaseEvaluationAgent(unittest.TestCase):
    """测试BaseEvaluationAgent类"""

    @classmethod
    def setUpClass(cls):
        """设置测试类"""
        logger.info("=" * 60)
        logger.info("开始测试BaseEvaluationAgent")
        logger.info("=" * 60)

        from solution_evaluation_services import (
            BaseEvaluationAgent,
            AgentConfig,
            AgentType,
            AgentStatus
        )

        cls.AgentConfig = AgentConfig
        cls.AgentType = AgentType
        cls.AgentStatus = AgentStatus

        # 创建测试配置
        cls.test_config = AgentConfig(
            agent_id="TEST_AGENT_001",
            name="测试Agent",
            agent_type=AgentType.GENERAL,
            description="用于测试的Agent",
            model_name="test-model",
            model_provider="openai"
        )

        # 创建测试Agent
        cls.agent = BaseEvaluationAgent(cls.test_config)

    @classmethod
    def tearDownClass(cls):
        """清理测试类"""
        logger.info("=" * 60)
        logger.info("BaseEvaluationAgent测试完成")
        logger.info("=" * 60)

    def test_01_agent_properties(self):
        """测试Agent属性"""
        logger.info("测试01: Agent属性")
        
        # 测试agent_id属性
        self.assertEqual(self.agent.agent_id, "TEST_AGENT_001")
        logger.info(f"  agent_id: {self.agent.agent_id}")
        
        # 测试name属性
        self.assertEqual(self.agent.name, "测试Agent")
        logger.info(f"  name: {self.agent.name}")
        
        # 测试agent_type属性
        self.assertEqual(self.agent.agent_type, self.AgentType.GENERAL)
        logger.info(f"  agent_type: {self.agent.agent_type}")
        
        # 测试status属性
        logger.info(f"  status: {self.agent.status}")

    def test_02_agent_availability(self):
        """测试Agent可用性检查"""
        logger.info("测试02: Agent可用性检查")
        
        # 检查is_available属性
        is_available = self.agent.is_available
        logger.info(f"  is_available: {is_available}")
        
        # Agent状态应该是IDLE或ERROR（取决于agno是否可用）
        self.assertIn(self.agent.status, [self.AgentStatus.IDLE, self.AgentStatus.ERROR])
        logger.info(f"  status: {self.agent.status}")

    def test_03_get_info(self):
        """测试获取Agent信息"""
        logger.info("测试03: 获取Agent信息")
        
        info = self.agent.get_info()
        
        # 验证信息结构
        self.assertIn("agent_id", info)
        self.assertIn("name", info)
        self.assertIn("agent_type", info)
        self.assertIn("status", info)
        self.assertIn("created_at", info)
        self.assertIn("usage_count", info)
        self.assertIn("error_count", info)
        
        logger.info(f"  Agent信息: {info}")

    def test_04_reset_agent(self):
        """测试重置Agent状态"""
        logger.info("测试04: 重置Agent状态")
        
        # 重置Agent
        self.agent.reset()
        
        # 状态应该是IDLE
        self.assertEqual(self.agent.status, self.AgentStatus.IDLE)
        logger.info(f"  重置后状态: {self.agent.status}")

    def test_05_shutdown_agent(self):
        """测试关闭Agent"""
        logger.info("测试05: 关闭Agent")
        
        # 关闭Agent
        self.agent.shutdown()
        
        # 状态应该是OFFLINE
        self.assertEqual(self.agent.status, self.AgentStatus.OFFLINE)
        logger.info(f"  关闭后状态: {self.agent.status}")
        
        # 重置状态以便其他测试
        self.agent.reset()

    def test_06_agent_config(self):
        """测试Agent配置"""
        logger.info("测试06: Agent配置")
        
        config = self.agent.config
        
        # 验证配置属性
        self.assertEqual(config.agent_id, "TEST_AGENT_001")
        self.assertEqual(config.name, "测试Agent")
        self.assertEqual(config.model_name, "test-model")
        self.assertEqual(config.model_provider, "openai")
        
        logger.info(f"  配置: agent_id={config.agent_id}, model={config.model_name}")

    def test_07_usage_tracking(self):
        """测试使用计数跟踪"""
        logger.info("测试07: 使用计数跟踪")
        
        initial_count = self.agent._usage_count
        logger.info(f"  初始使用次数: {initial_count}")
        
        # 使用计数应该从0开始
        self.assertEqual(initial_count, 0)

    def test_08_error_tracking(self):
        """测试错误计数跟踪"""
        logger.info("测试08: 错误计数跟踪")
        
        error_count = self.agent._error_count
        logger.info(f"  错误计数: {error_count}")
        
        # 错误计数应该为0
        self.assertEqual(error_count, 0)


class TestAgentTypeAndStatus(unittest.TestCase):
    """测试AgentType和AgentStatus枚举"""

    @classmethod
    def setUpClass(cls):
        """设置测试类"""
        logger.info("=" * 60)
        logger.info("开始测试AgentType和AgentStatus枚举")
        logger.info("=" * 60)

        from solution_evaluation_services import AgentType, AgentStatus

        cls.AgentType = AgentType
        cls.AgentStatus = AgentStatus

    def test_01_agent_types(self):
        """测试AgentType枚举值"""
        logger.info("测试01: AgentType枚举值")
        
        expected_types = [
            "feasibility", "risk", "resource", "benefit",
            "compliance", "strategy", "general", "custom"
        ]
        
        for type_name in expected_types:
            agent_type = getattr(self.AgentType, type_name.upper())
            self.assertEqual(agent_type.value, type_name)
            logger.info(f"  {type_name.upper()}: {agent_type.value}")

    def test_02_agent_statuses(self):
        """测试AgentStatus枚举值"""
        logger.info("测试02: AgentStatus枚举值")
        
        expected_statuses = ["idle", "busy", "error", "offline"]
        
        for status_name in expected_statuses:
            status = getattr(self.AgentStatus, status_name.upper())
            self.assertEqual(status.value, status_name)
            logger.info(f"  {status_name.upper()}: {status.value}")


class TestAgentConfig(unittest.TestCase):
    """测试AgentConfig配置类"""

    @classmethod
    def setUpClass(cls):
        """设置测试类"""
        logger.info("=" * 60)
        logger.info("开始测试AgentConfig")
        logger.info("=" * 60)

        from solution_evaluation_services import AgentConfig, AgentType

        cls.AgentConfig = AgentConfig
        cls.AgentType = AgentType

    def test_01_create_config(self):
        """测试创建配置"""
        logger.info("测试01: 创建配置")
        
        config = self.AgentConfig(
            agent_id="CONFIG_TEST_001",
            name="配置测试Agent",
            agent_type=self.AgentType.FEASIBILITY,
            description="测试配置",
            model_name="gpt-4",
            model_provider="openai",
            temperature=0.5,
            max_tokens=2000
        )
        
        self.assertEqual(config.agent_id, "CONFIG_TEST_001")
        self.assertEqual(config.temperature, 0.5)
        self.assertEqual(config.max_tokens, 2000)
        
        logger.info(f"  配置创建成功: {config.agent_id}")

    def test_02_default_values(self):
        """测试默认值"""
        logger.info("测试02: 默认值")
        
        config = self.AgentConfig(
            agent_id="DEFAULT_TEST_001",
            name="默认配置测试",
            agent_type=self.AgentType.RISK
        )
        
        self.assertEqual(config.model_name, "gpt-4o")
        self.assertEqual(config.model_provider, "openai")
        self.assertEqual(config.temperature, 0.3)
        self.assertEqual(config.max_tokens, 4000)
        
        logger.info(f"  默认值: model={config.model_name}, temp={config.temperature}")

    def test_03_validation(self):
        """测试参数验证"""
        logger.info("测试03: 参数验证")
        
        from pydantic import ValidationError
        
        # 测试无效的temperature
        with self.assertRaises(ValidationError):
            self.AgentConfig(
                agent_id="VAL_TEST_001",
                name="验证测试",
                agent_type=self.AgentType.GENERAL,
                temperature=3.0  # 超出范围
            )
        
        logger.info("  参数验证通过")


if __name__ == '__main__':
    unittest.main()
