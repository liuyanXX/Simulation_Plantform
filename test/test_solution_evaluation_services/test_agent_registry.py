"""测试AgentRegistry模块"""
import unittest
import logging
import os
import sys
import shutil
from datetime import datetime
from typing import Dict, Any

# 配置日志
log_file = os.path.join("logs", "test_agent_registry.log")
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


class TestAgentRegistry(unittest.TestCase):
    """测试AgentRegistry类"""

    @classmethod
    def setUpClass(cls):
        """设置测试类"""
        logger.info("=" * 60)
        logger.info("开始测试AgentRegistry")
        logger.info("=" * 60)

        # 创建测试存储目录
        cls.test_storage_path = "test_agent_registry_data"
        os.makedirs(cls.test_storage_path, exist_ok=True)

        from solution_evaluation_services import (
            AgentRegistry,
            AgentConfig,
            AgentType,
            AgentStatus,
            BaseEvaluationAgent
        )

        cls.AgentRegistry = AgentRegistry
        cls.AgentConfig = AgentConfig
        cls.AgentType = AgentType
        cls.BaseEvaluationAgent = BaseEvaluationAgent

        # 创建测试Agent
        cls.test_config1 = AgentConfig(
            agent_id="REG_TEST_001",
            name="测试Agent1",
            agent_type=AgentType.FEASIBILITY,
            description="测试Agent1"
        )

        cls.test_config2 = AgentConfig(
            agent_id="REG_TEST_002",
            name="测试Agent2",
            agent_type=AgentType.RISK,
            description="测试Agent2"
        )

        cls.test_config3 = AgentConfig(
            agent_id="REG_TEST_003",
            name="测试Agent3",
            agent_type=AgentType.FEASIBILITY,
            description="测试Agent3"
        )

        cls.agent1 = BaseEvaluationAgent(cls.test_config1)
        cls.agent2 = BaseEvaluationAgent(cls.test_config2)
        cls.agent3 = BaseEvaluationAgent(cls.test_config3)

        # 创建注册表实例
        cls.registry = AgentRegistry(storage_path=cls.test_storage_path)
        cls.registry.clear()  # 清空现有注册

    @classmethod
    def tearDownClass(cls):
        """清理测试类"""
        logger.info("=" * 60)
        logger.info("AgentRegistry测试完成")
        logger.info("=" * 60)
        
        # 清理测试数据
        if hasattr(cls, 'test_storage_path'):
            shutil.rmtree(cls.test_storage_path, ignore_errors=True)

    def test_01_register_agent(self):
        """测试注册Agent"""
        logger.info("测试01: 注册Agent")
        
        result = self.registry.register(
            self.agent1,
            capabilities=["capability1", "capability2"],
            description="测试注册"
        )
        
        self.assertTrue(result)
        
        # 验证注册信息
        registration = self.registry.get_registration("REG_TEST_001")
        self.assertIsNotNone(registration)
        self.assertEqual(registration.name, "测试Agent1")
        self.assertEqual(registration.agent_type, self.AgentType.FEASIBILITY)
        
        logger.info(f"  注册成功: {registration.agent_id}")

    def test_02_register_multiple_agents(self):
        """测试注册多个Agent"""
        logger.info("测试02: 注册多个Agent")
        
        self.registry.register(self.agent2)
        self.registry.register(self.agent3)
        
        agents = self.registry.list_agents()
        self.assertEqual(len(agents), 3)
        
        logger.info(f"  当前注册Agent数量: {len(agents)}")

    def test_03_get_agent(self):
        """测试获取Agent"""
        logger.info("测试03: 获取Agent")
        
        agent = self.registry.get_agent("REG_TEST_001")
        
        self.assertIsNotNone(agent)
        self.assertEqual(agent.agent_id, "REG_TEST_001")
        self.assertEqual(agent.name, "测试Agent1")
        
        logger.info(f"  获取Agent: {agent.name}")

    def test_04_get_agent_not_found(self):
        """测试获取不存在的Agent"""
        logger.info("测试04: 获取不存在的Agent")
        
        agent = self.registry.get_agent("NON_EXISTENT")
        self.assertIsNone(agent)
        
        logger.info("  Agent不存在，返回None")

    def test_05_unregister_agent(self):
        """测试注销Agent"""
        logger.info("测试05: 注销Agent")
        
        # 先注册一个Agent
        temp_config = self.AgentConfig(
            agent_id="UNREG_TEST",
            name="临时测试Agent",
            agent_type=self.AgentType.RESOURCE
        )
        temp_agent = self.BaseEvaluationAgent(temp_config)
        self.registry.register(temp_agent)
        
        # 注销
        result = self.registry.unregister("UNREG_TEST")
        self.assertTrue(result)
        
        # 验证已注销
        agent = self.registry.get_agent("UNREG_TEST")
        self.assertIsNone(agent)
        
        logger.info("  注销成功")

    def test_06_get_agents_by_type(self):
        """测试按类型获取Agent"""
        logger.info("测试06: 按类型获取Agent")
        
        feasibility_agents = self.registry.get_agents_by_type(self.AgentType.FEASIBILITY)
        
        self.assertGreaterEqual(len(feasibility_agents), 1)
        
        for agent in feasibility_agents:
            self.assertEqual(agent.agent_type, self.AgentType.FEASIBILITY)
            logger.info(f"  {agent.agent_type.value} Agent: {agent.name}")

    def test_07_get_available_agents(self):
        """测试获取可用Agent"""
        logger.info("测试07: 获取可用Agent")
        
        available = self.registry.get_available_agents()
        logger.info(f"  可用Agent数量: {len(available)}")
        
        # 按类型获取
        feasibility_available = self.registry.get_available_agents(self.AgentType.FEASIBILITY)
        logger.info(f"  可用可行性Agent数量: {len(feasibility_available)}")

    def test_08_select_agent(self):
        """测试选择Agent"""
        logger.info("测试08: 选择Agent")
        
        # 测试round_robin策略
        agent1 = self.registry.select_agent(self.AgentType.FEASIBILITY, "round_robin")
        agent2 = self.registry.select_agent(self.AgentType.FEASIBILITY, "round_robin")
        
        # 至少应该选择一个Agent
        self.assertIsNotNone(agent1)
        logger.info(f"  选中Agent: {agent1.name if agent1 else 'None'}")

    def test_09_select_agent_random(self):
        """测试随机选择Agent"""
        logger.info("测试09: 随机选择Agent")
        
        agent = self.registry.select_agent(self.AgentType.FEASIBILITY, "random")
        
        if agent:
            self.assertEqual(agent.agent_type, self.AgentType.FEASIBILITY)
            logger.info(f"  随机选中: {agent.name}")
        else:
            logger.info("  未找到可用Agent")

    def test_10_heartbeat(self):
        """测试心跳更新"""
        logger.info("测试10: 心跳更新")
        
        result = self.registry.heartbeat("REG_TEST_001")
        self.assertTrue(result)
        
        registration = self.registry.get_registration("REG_TEST_001")
        self.assertIsNotNone(registration.last_heartbeat)
        
        logger.info("  心跳更新成功")

    def test_11_check_health(self):
        """测试健康检查"""
        logger.info("测试11: 健康检查")
        
        health = self.registry.check_health("REG_TEST_001")
        
        self.assertIn("status", health)
        self.assertIn("agent_id", health)
        self.assertEqual(health["agent_id"], "REG_TEST_001")
        
        logger.info(f"  健康状态: {health['status']}")

    def test_12_check_all_health(self):
        """测试所有Agent健康检查"""
        logger.info("测试12: 所有Agent健康检查")
        
        health_all = self.registry.check_all_health()
        
        self.assertGreater(len(health_all), 0)
        
        for agent_id, health in health_all.items():
            logger.info(f"  {agent_id}: {health['status']}")

    def test_13_get_statistics(self):
        """测试获取统计信息"""
        logger.info("测试13: 获取统计信息")
        
        stats = self.registry.get_statistics()
        
        self.assertIn("total_agents", stats)
        self.assertIn("available_agents", stats)
        self.assertIn("by_type", stats)
        
        logger.info(f"  总Agent数: {stats['total_agents']}")
        logger.info(f"  可用Agent数: {stats['available_agents']}")

    def test_14_list_agents(self):
        """测试列出Agent"""
        logger.info("测试14: 列出Agent")
        
        agents = self.registry.list_agents()
        
        self.assertGreater(len(agents), 0)
        
        for agent_info in agents:
            logger.info(f"  Agent: {agent_info['agent_id']} - {agent_info['name']}")

    def test_15_list_registrations(self):
        """测试列出注册信息"""
        logger.info("测试15: 列出注册信息")
        
        registrations = self.registry.list_registrations()
        
        self.assertGreater(len(registrations), 0)
        
        logger.info(f"  注册信息数量: {len(registrations)}")

    def test_16_update_registration(self):
        """测试更新注册信息"""
        logger.info("测试16: 更新注册信息")
        
        # 重新注册相同ID的Agent会更新注册信息
        result = self.registry.register(self.agent1, description="更新后的描述")
        
        self.assertTrue(result)
        
        registration = self.registry.get_registration("REG_TEST_001")
        self.assertEqual(registration.description, "更新后的描述")
        
        logger.info("  注册信息更新成功")

    def test_17_clear_registry(self):
        """测试清空注册表"""
        logger.info("测试17: 清空注册表")
        
        # 先注册一个Agent
        temp_config = self.AgentConfig(
            agent_id="CLEAR_TEST",
            name="清空测试Agent",
            agent_type=self.AgentType.COMPLIANCE
        )
        temp_agent = self.BaseEvaluationAgent(temp_config)
        self.registry.register(temp_agent)
        
        # 清空
        self.registry.clear()
        
        agents = self.registry.list_agents()
        self.assertEqual(len(agents), 0)
        
        logger.info("  注册表已清空")


class TestGlobalRegistryFunctions(unittest.TestCase):
    """测试全局注册表函数"""

    @classmethod
    def setUpClass(cls):
        """设置测试类"""
        logger.info("=" * 60)
        logger.info("开始测试全局注册表函数")
        logger.info("=" * 60)

        from solution_evaluation_services import (
            get_registry,
            register_agent,
            get_agent,
            select_agent,
            AgentConfig,
            AgentType,
            BaseEvaluationAgent
        )

        cls.get_registry = get_registry
        cls.register_agent = register_agent
        cls.get_agent = get_agent
        cls.select_agent = select_agent
        cls.AgentConfig = AgentConfig
        cls.AgentType = AgentType
        cls.BaseEvaluationAgent = BaseEvaluationAgent

    def test_01_get_registry_singleton(self):
        """测试获取全局注册表单例"""
        logger.info("测试01: 获取全局注册表单例")
        
        registry1 = self.get_registry()
        registry2 = self.get_registry()
        
        self.assertIs(registry1, registry2)
        
        logger.info("  全局注册表为单例")

    def test_02_register_agent_global(self):
        """测试全局注册Agent"""
        logger.info("测试02: 全局注册Agent")
        
        config = self.AgentConfig(
            agent_id="GLOBAL_TEST_001",
            name="全局测试Agent",
            agent_type=self.AgentType.STRATEGY
        )
        agent = self.BaseEvaluationAgent(config)
        
        result = self.register_agent(agent)
        
        self.assertTrue(result)
        
        logger.info("  全局注册成功")

    def test_03_get_agent_global(self):
        """测试全局获取Agent"""
        logger.info("测试03: 全局获取Agent")
        
        agent = self.get_agent("GLOBAL_TEST_001")
        
        self.assertIsNotNone(agent)
        self.assertEqual(agent.name, "全局测试Agent")
        
        logger.info(f"  获取Agent: {agent.name}")

    def test_04_select_agent_global(self):
        """测试全局选择Agent"""
        logger.info("测试04: 全局选择Agent")
        
        agent = self.select_agent(self.AgentType.STRATEGY)
        
        if agent:
            self.assertEqual(agent.agent_type, self.AgentType.STRATEGY)
            logger.info(f"  选中Agent: {agent.name}")
        else:
            logger.info("  未找到可用Agent")


if __name__ == '__main__':
    unittest.main()
