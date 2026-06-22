"""测试EvaluationProxy模块"""
import unittest
import logging
import os
import sys
import shutil
from datetime import datetime
from typing import Dict, Any

# 配置日志
log_file = os.path.join("logs", "test_evaluation_proxy.log")
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


class TestEvaluationProxy(unittest.TestCase):
    """测试EvaluationProxy类"""

    @classmethod
    def setUpClass(cls):
        """设置测试类"""
        logger.info("=" * 60)
        logger.info("开始测试EvaluationProxy")
        logger.info("=" * 60)

        from solution_evaluation_services import (
            EvaluationProxy,
            AgentRegistry,
            SolutionEvaluation,
            EvaluationStatus,
            AgentType,
            BaseEvaluationAgent,
            AgentConfig
        )
        from bo.solution import Solution

        cls.EvaluationProxy = EvaluationProxy
        cls.AgentRegistry = AgentRegistry
        cls.SolutionEvaluation = SolutionEvaluation
        cls.EvaluationStatus = EvaluationStatus
        cls.AgentType = AgentType
        cls.BaseEvaluationAgent = BaseEvaluationAgent
        cls.AgentConfig = AgentConfig

        # 创建测试方案
        cls.test_solution = Solution(
            solution_id="SOL_PROXY_001",
            name="代理测试方案",
            version="1.0",
            purpose="测试目的",
            objectives=["目标1", "目标2"],
            initiatives=["举措1", "举措2", "举措3"],
            work_content="测试工作内容"
        )

        # 创建测试存储目录
        cls.test_storage_path = "test_proxy_data"
        cls.test_sim_log_path = "test_simulation_logs"
        cls.test_eval_log_path = "test_evaluation_logs"
        
        os.makedirs(cls.test_storage_path, exist_ok=True)
        os.makedirs(cls.test_sim_log_path, exist_ok=True)
        os.makedirs(cls.test_eval_log_path, exist_ok=True)

        # 创建注册表并注册测试Agent
        cls.test_registry = AgentRegistry(storage_path=cls.test_storage_path)
        cls.test_registry.clear()

        # 注册测试Agent
        test_config1 = AgentConfig(
            agent_id="PROXY_TEST_001",
            name="代理测试Agent1",
            agent_type=AgentType.CUSTOM,
            description="代理测试"
        )
        test_agent1 = BaseEvaluationAgent(test_config1)
        cls.test_registry.register(test_agent1)

        test_config2 = AgentConfig(
            agent_id="PROXY_TEST_002",
            name="代理测试Agent2",
            agent_type=AgentType.FEASIBILITY,
            description="可行性测试"
        )
        test_agent2 = BaseEvaluationAgent(test_config2)
        cls.test_registry.register(test_agent2)

        # 创建评价代理
        cls.proxy = EvaluationProxy(
            registry=cls.test_registry,
            simulation_log_path=cls.test_sim_log_path,
            log_path=cls.test_eval_log_path
        )

    @classmethod
    def tearDownClass(cls):
        """清理测试类"""
        logger.info("=" * 60)
        logger.info("EvaluationProxy测试完成")
        logger.info("=" * 60)
        
        # 清理测试数据
        shutil.rmtree(cls.test_storage_path, ignore_errors=True)
        shutil.rmtree(cls.test_sim_log_path, ignore_errors=True)
        shutil.rmtree(cls.test_eval_log_path, ignore_errors=True)

    def test_01_create_proxy(self):
        """测试创建评价代理"""
        logger.info("测试01: 创建评价代理")
        
        self.assertIsNotNone(self.proxy)
        self.assertIsNotNone(self.proxy._registry)
        self.assertIsNotNone(self.proxy._gateway)
        
        logger.info("  评价代理创建成功")

    def test_02_create_evaluation(self):
        """测试创建方案评价"""
        logger.info("测试02: 创建方案评价")
        
        evaluation = self.proxy.create_evaluation(
            self.test_solution,
            ["completeness", "rationality"],
            evaluator="测试评价人"
        )
        
        self.assertIsNotNone(evaluation)
        self.assertEqual(evaluation.solution_id, "SOL_PROXY_001")
        self.assertEqual(len(evaluation.evaluation_dimensions), 2)
        self.assertEqual(evaluation.evaluator, "测试评价人")
        
        logger.info(f"  创建评价: {evaluation.evaluation_id}")

    def test_03_evaluate_solution(self):
        """测试评价方案"""
        logger.info("测试03: 评价方案")
        
        evaluation = self.proxy.evaluate_solution(
            self.test_solution,
            ["completeness"],
            evaluator="测试评价人"
        )
        
        self.assertIsNotNone(evaluation)
        self.assertIn(evaluation.status, [
            self.EvaluationStatus.COMPLETED,
            self.EvaluationStatus.FAILED,
            self.EvaluationStatus.IN_PROGRESS
        ])
        
        logger.info(f"  评价完成，状态: {evaluation.status}")

    def test_04_evaluate_solution_with_simulation(self):
        """测试带仿真的方案评价"""
        logger.info("测试04: 带仿真的方案评价")
        
        # 创建仿真日志
        sim_log = "Test simulation log content"
        sim_log_file = os.path.join(self.test_sim_log_path, "SOL_PROXY_001.log")
        with open(sim_log_file, 'w', encoding='utf-8') as f:
            f.write(sim_log)
        
        evaluation = self.proxy.evaluate_solution(
            self.test_solution,
            ["completeness"],
            include_simulation=True
        )
        
        self.assertIsNotNone(evaluation)
        
        logger.info(f"  带仿真评价完成，状态: {evaluation.status}")

    def test_05_get_available_dimensions(self):
        """测试获取可用维度"""
        logger.info("测试05: 获取可用维度")
        
        dimensions = self.proxy.get_available_dimensions()
        
        self.assertIsInstance(dimensions, list)
        self.assertGreater(len(dimensions), 0)
        
        logger.info(f"  可用维度: {dimensions}")

    def test_06_get_available_agents(self):
        """测试获取可用Agent"""
        logger.info("测试06: 获取可用Agent")
        
        agents = self.proxy.get_available_agents()
        
        self.assertIsInstance(agents, dict)
        self.assertIn("total", agents)
        self.assertIn("agents", agents)
        
        logger.info(f"  可用Agent数量: {agents.get('total', 0)}")

    def test_07_register_agent(self):
        """测试注册Agent"""
        logger.info("测试07: 注册Agent")
        
        from solution_evaluation_services import BaseEvaluationAgent, AgentConfig
        
        new_config = AgentConfig(
            agent_id="PROXY_TEST_003",
            name="新注册Agent",
            agent_type=self.AgentType.RISK
        )
        new_agent = BaseEvaluationAgent(new_config)
        
        result = self.proxy.register_agent(new_agent, capabilities=["risk_analysis"])
        
        self.assertTrue(result)
        
        logger.info("  Agent注册成功")

    def test_08_get_evaluation_summary(self):
        """测试获取评价摘要"""
        logger.info("测试08: 获取评价摘要")
        
        # 先创建评价
        evaluation = self.proxy.create_evaluation(
            self.test_solution,
            ["completeness"]
        )
        
        # 获取摘要
        summary = self.proxy.get_evaluation_summary(evaluation)
        
        self.assertIsInstance(summary, dict)
        self.assertIn("evaluation_id", summary)
        
        logger.info(f"  评价摘要: {summary}")

    def test_09_get_evaluation_report(self):
        """测试获取评价报告"""
        logger.info("测试09: 获取评价报告")
        
        # 先创建评价
        evaluation = self.proxy.create_evaluation(
            self.test_solution,
            ["completeness"]
        )
        
        # 获取报告
        report = self.proxy.get_evaluation_report(evaluation)
        
        self.assertIsInstance(report, dict)
        
        logger.info("  评价报告获取成功")

    def test_10_get_evaluation_history(self):
        """测试获取评价历史"""
        logger.info("测试10: 获取评价历史")
        
        history = self.proxy.get_evaluation_history("SOL_PROXY_001")
        
        self.assertIsInstance(history, list)
        
        logger.info(f"  评价历史数量: {len(history)}")

    def test_11_save_and_load_evaluation(self):
        """测试保存和加载评价"""
        logger.info("测试11: 保存和加载评价")
        
        # 创建评价
        evaluation = self.proxy.create_evaluation(
            self.test_solution,
            ["completeness"]
        )
        
        # 保存
        save_path = self.proxy.save_evaluation(evaluation)
        self.assertTrue(os.path.exists(save_path))
        
        logger.info(f"  评价保存到: {save_path}")

    def test_12_create_evaluation_with_multiple_dimensions(self):
        """测试多维度评价创建"""
        logger.info("测试12: 多维度评价创建")
        
        evaluation = self.proxy.create_evaluation(
            self.test_solution,
            ["completeness", "rationality", "feasibility", "risk"]
        )
        
        self.assertEqual(len(evaluation.evaluation_dimensions), 4)
        
        # 验证维度映射
        for dim in ["completeness", "rationality", "feasibility", "risk"]:
            self.assertIn(dim, evaluation.evaluation_dimensions)
        
        logger.info(f"  多维度评价: {len(evaluation.evaluation_dimensions)} 个维度")


class TestEvaluationProxyWorkflow(unittest.TestCase):
    """测试EvaluationProxy工作流"""

    @classmethod
    def setUpClass(cls):
        """设置测试类"""
        logger.info("=" * 60)
        logger.info("开始测试EvaluationProxy工作流")
        logger.info("=" * 60)

        from solution_evaluation_services import (
            EvaluationProxy,
            AgentRegistry,
            SolutionEvaluation,
            DimensionEvaluation,
            EvaluationStatus,
            AgentType,
            BaseEvaluationAgent,
            AgentConfig
        )
        from bo.solution import Solution

        cls.SolutionEvaluation = SolutionEvaluation
        cls.DimensionEvaluation = DimensionEvaluation
        cls.EvaluationStatus = EvaluationStatus
        cls.AgentType = AgentType
        cls.BaseEvaluationAgent = BaseEvaluationAgent
        cls.AgentConfig = AgentConfig

        # 创建测试方案
        cls.test_solution = Solution(
            solution_id="SOL_WF_001",
            name="工作流测试方案",
            version="1.0",
            purpose="测试工作流",
            objectives=["目标1", "目标2"],
            initiatives=["举措1", "举措2"],
            work_content="工作流测试内容"
        )

        # 创建存储目录
        cls.test_storage_path = "test_workflow_data"
        cls.test_sim_log_path = "test_wf_simulation_logs"
        cls.test_eval_log_path = "test_wf_evaluation_logs"
        
        os.makedirs(cls.test_storage_path, exist_ok=True)
        os.makedirs(cls.test_sim_log_path, exist_ok=True)
        os.makedirs(cls.test_eval_log_path, exist_ok=True)

        # 创建注册表
        cls.test_registry = AgentRegistry(storage_path=cls.test_storage_path)
        cls.test_registry.clear()

        # 创建代理
        cls.proxy = EvaluationProxy(
            registry=cls.test_registry,
            simulation_log_path=cls.test_sim_log_path,
            log_path=cls.test_eval_log_path
        )

    @classmethod
    def tearDownClass(cls):
        """清理测试类"""
        logger.info("=" * 60)
        logger.info("EvaluationProxy工作流测试完成")
        logger.info("=" * 60)
        
        shutil.rmtree(cls.test_storage_path, ignore_errors=True)
        shutil.rmtree(cls.test_sim_log_path, ignore_errors=True)
        shutil.rmtree(cls.test_eval_log_path, ignore_errors=True)

    def test_01_complete_evaluation_workflow(self):
        """测试完整评价工作流"""
        logger.info("测试01: 完整评价工作流")
        
        # 1. 创建评价
        evaluation = self.proxy.create_evaluation(
            self.test_solution,
            ["completeness", "rationality"]
        )
        self.assertIsNotNone(evaluation)
        logger.info(f"  1. 创建评价: {evaluation.evaluation_id}")
        
        # 2. 执行评价
        evaluation = self.proxy.evaluate_solution(
            self.test_solution,
            ["completeness", "rationality"]
        )
        self.assertIsNotNone(evaluation)
        logger.info(f"  2. 执行评价: {evaluation.status}")
        
        # 3. 获取摘要
        summary = self.proxy.get_evaluation_summary(evaluation)
        self.assertIsNotNone(summary)
        logger.info(f"  3. 获取摘要: score={summary.get('overall_score')}")
        
        # 4. 获取报告
        report = self.proxy.get_evaluation_report(evaluation)
        self.assertIsNotNone(report)
        logger.info(f"  4. 获取报告: {len(report.get('dimensions', []))} 个维度")
        
        # 5. 保存评价
        save_path = self.proxy.save_evaluation(evaluation)
        self.assertTrue(os.path.exists(save_path))
        logger.info(f"  5. 保存评价: {save_path}")

    def test_02_evaluation_with_recommendations(self):
        """测试带建议的评价"""
        logger.info("测试02: 带建议的评价")
        
        # 创建评价并添加建议
        evaluation = self.proxy.create_evaluation(
            self.test_solution,
            ["completeness"]
        )
        
        # 添加带建议的维度评价
        dim_eval = self.DimensionEvaluation(
            dimension="completeness",
            agent_id="WF_AGENT_001",
            score=85.0,
            level="good",
            summary="方案完整性良好",
            recommendations=[
                "建议1: 完善风险管理部分",
                "建议2: 增加资源保障说明",
                "建议3: 细化时间节点"
            ],
            status=self.EvaluationStatus.COMPLETED
        )
        evaluation.add_dimension_evaluation(dim_eval)
        evaluation.mark_completed()
        
        # 获取报告
        report = self.proxy.get_evaluation_report(evaluation)
        
        recommendations = report["dimensions"][0]["recommendations"]
        self.assertEqual(len(recommendations), 3)
        
        logger.info(f"  建议数量: {len(recommendations)}")

    def test_03_evaluation_with_errors(self):
        """测试失败的评价"""
        logger.info("测试03: 失败的评价")
        
        # 创建无维度的评价
        evaluation = self.proxy.create_evaluation(
            self.test_solution,
            []  # 无维度
        )
        
        # 执行评价（应该失败）
        result = self.proxy.evaluate_solution(
            self.test_solution,
            []  # 无维度
        )
        
        self.assertEqual(result.status, self.EvaluationStatus.FAILED)
        
        logger.info(f"  失败评价状态: {result.status}")


if __name__ == '__main__':
    unittest.main()
