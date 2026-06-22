"""测试ServiceGateway模块"""
import unittest
import logging
import os
import sys
from datetime import datetime
from typing import Dict, Any

# 配置日志
log_file = os.path.join("logs", "test_service_gateway.log")
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


class TestServiceGateway(unittest.TestCase):
    """测试ServiceGateway类"""

    @classmethod
    def setUpClass(cls):
        """设置测试类"""
        logger.info("=" * 60)
        logger.info("开始测试ServiceGateway")
        logger.info("=" * 60)

        from solution_evaluation_services import (
            ServiceGateway,
            AgentRegistry,
            SolutionEvaluation,
            DimensionEvaluation,
            EvaluationStatus,
            AgentType
        )
        from bo.solution import Solution

        cls.ServiceGateway = ServiceGateway
        cls.AgentRegistry = AgentRegistry
        cls.SolutionEvaluation = SolutionEvaluation
        cls.DimensionEvaluation = DimensionEvaluation
        cls.EvaluationStatus = EvaluationStatus
        cls.AgentType = AgentType

        # 创建测试方案
        cls.test_solution = Solution(
            solution_id="SOL_GW_001",
            name="网关测试方案",
            version="1.0",
            purpose="测试目的",
            objectives=["目标1", "目标2"],
            initiatives=["举措1", "举措2"],
            work_content="测试工作内容"
        )

        # 创建注册表
        cls.test_registry = AgentRegistry(storage_path="test_gateway_registry")

        # 创建网关
        cls.gateway = ServiceGateway(cls.test_registry)

    @classmethod
    def tearDownClass(cls):
        """清理测试类"""
        logger.info("=" * 60)
        logger.info("ServiceGateway测试完成")
        logger.info("=" * 60)
        
        # 清理
        import shutil
        shutil.rmtree("test_gateway_registry", ignore_errors=True)

    def test_01_create_gateway(self):
        """测试创建服务网关"""
        logger.info("测试01: 创建服务网关")
        
        gateway = self.ServiceGateway()
        
        self.assertIsNotNone(gateway)
        self.assertIsNotNone(gateway._dimension_agent_mapping)
        
        logger.info(f"  网关创建成功，维度映射数: {len(gateway._dimension_agent_mapping)}")

    def test_02_create_gateway_with_registry(self):
        """测试使用注册表创建网关"""
        logger.info("测试02: 使用注册表创建网关")
        
        self.assertIsNotNone(self.gateway._registry)
        logger.info("  注册表已关联")

    def test_03_get_dimension_agent_mapping(self):
        """测试获取维度Agent映射"""
        logger.info("测试03: 获取维度Agent映射")
        
        mapping = self.gateway.get_dimension_agent_mapping()
        
        self.assertIn("completeness", mapping)
        self.assertIn("rationality", mapping)
        self.assertIn("feasibility", mapping)
        self.assertIn("risk", mapping)
        
        logger.info(f"  映射维度: {list(mapping.keys())}")

    def test_04_register_dimension_agent_mapping(self):
        """测试注册维度Agent映射"""
        logger.info("测试04: 注册维度Agent映射")
        
        self.gateway.register_dimension_agent_mapping("custom_dimension", self.AgentType.GENERAL)
        
        mapping = self.gateway.get_dimension_agent_mapping()
        self.assertEqual(mapping["custom_dimension"], "general")
        
        logger.info("  自定义维度映射注册成功")

    def test_05_get_available_agents(self):
        """测试获取可用Agent"""
        logger.info("测试05: 获取可用Agent")
        
        available = self.gateway.get_available_agents()
        
        self.assertIn("total", available)
        self.assertIn("agents", available)
        self.assertIsInstance(available["agents"], list)
        
        logger.info(f"  可用Agent数量: {available['total']}")

    def test_06_process_evaluation_with_dimensions(self):
        """测试处理带维度的评价"""
        logger.info("测试06: 处理带维度的评价")
        
        evaluation = self.SolutionEvaluation.from_solution(
            self.test_solution,
            "EVAL_GW_001",
            ["completeness", "rationality"]
        )
        
        result = self.gateway.process_evaluation(evaluation)
        
        # 由于没有注册的Agent，应该标记为失败
        self.assertIn(result.status, [self.EvaluationStatus.FAILED, self.EvaluationStatus.COMPLETED])
        
        logger.info(f"  处理状态: {result.status}")

    def test_07_process_evaluation_no_dimensions(self):
        """测试处理无维度的评价"""
        logger.info("测试07: 处理无维度的评价")
        
        evaluation = self.SolutionEvaluation.from_solution(
            self.test_solution,
            "EVAL_GW_002",
            []  # 无维度
        )
        
        result = self.gateway.process_evaluation(evaluation)
        
        self.assertEqual(result.status, self.EvaluationStatus.FAILED)
        
        logger.info(f"  无维度评价状态: {result.status}")

    def test_08_route_to_agent(self):
        """测试路由到Agent"""
        logger.info("测试08: 路由到Agent")
        
        evaluation = self.SolutionEvaluation.from_solution(
            self.test_solution,
            "EVAL_GW_003",
            ["feasibility"]
        )
        
        result = self.gateway.route_to_agent(evaluation, "feasibility")
        
        # 结果应该是更新后的评价对象
        self.assertIsNotNone(result)
        
        logger.info(f"  路由结果状态: {result.status}")

    def test_09_route_to_agent_with_simulation_log(self):
        """测试带仿真日志的路由"""
        logger.info("测试09: 带仿真日志的路由")
        
        evaluation = self.SolutionEvaluation.from_solution(
            self.test_solution,
            "EVAL_GW_004",
            ["simulation"]
        )
        
        simulation_log = "Test simulation log content"
        result = self.gateway.route_to_agent(
            evaluation,
            "simulation",
            simulation_log=simulation_log
        )
        
        self.assertIsNotNone(result)
        
        logger.info("  带仿真日志路由完成")

    def test_10_get_agent_status(self):
        """测试获取Agent状态"""
        logger.info("测试10: 获取Agent状态")
        
        # 由于没有注册Agent，应该返回None
        status = self.gateway.get_agent_status("NON_EXISTENT")
        
        self.assertIsNone(status)
        
        logger.info("  Agent状态查询完成")

    def test_11_dimension_agent_mapping_keys(self):
        """测试维度映射键值"""
        logger.info("测试11: 维度映射键值")
        
        expected_dimensions = [
            "completeness", "rationality", "simulation",
            "feasibility", "risk", "resource",
            "benefit", "compliance", "strategy"
        ]
        
        mapping = self.gateway._dimension_agent_mapping
        
        for dim in expected_dimensions:
            self.assertIn(dim, mapping)
            logger.info(f"  {dim}: {mapping[dim]}")


class TestServiceGatewayIntegration(unittest.TestCase):
    """测试ServiceGateway集成"""

    @classmethod
    def setUpClass(cls):
        """设置测试类"""
        logger.info("=" * 60)
        logger.info("开始测试ServiceGateway集成")
        logger.info("=" * 60)

        from solution_evaluation_services import (
            ServiceGateway,
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
            solution_id="SOL_INT_001",
            name="集成测试方案",
            version="1.0",
            purpose="集成测试目的",
            objectives=["目标1"],
            initiatives=["举措1"],
            work_content="集成测试内容"
        )

        # 创建注册表并注册测试Agent
        cls.test_registry = AgentRegistry(storage_path="test_integration_registry")
        cls.test_registry.clear()

        # 注册一个测试Agent
        test_config = AgentConfig(
            agent_id="INT_TEST_001",
            name="集成测试Agent",
            agent_type=AgentType.CUSTOM,
            description="用于集成测试"
        )
        test_agent = BaseEvaluationAgent(test_config)
        cls.test_registry.register(test_agent, capabilities=["test"])

        # 创建网关
        cls.gateway = ServiceGateway(cls.test_registry)

    @classmethod
    def tearDownClass(cls):
        """清理测试类"""
        logger.info("=" * 60)
        logger.info("ServiceGateway集成测试完成")
        logger.info("=" * 60)
        
        import shutil
        shutil.rmtree("test_integration_registry", ignore_errors=True)

    def test_01_full_evaluation_workflow(self):
        """测试完整评价工作流"""
        logger.info("测试01: 完整评价工作流")
        
        # 创建评价
        evaluation = self.SolutionEvaluation.from_solution(
            self.test_solution,
            "EVAL_INT_001",
            ["completeness", "rationality"]
        )
        
        # 标记为进行中
        evaluation.mark_in_progress()
        self.assertEqual(evaluation.status, self.EvaluationStatus.IN_PROGRESS)
        
        # 添加维度评价
        dim_eval1 = self.DimensionEvaluation(
            dimension="completeness",
            agent_id="INT_TEST_001",
            agent_name="集成测试Agent",
            score=85.0,
            level="good",
            summary="完整性良好",
            status=self.EvaluationStatus.COMPLETED
        )
        evaluation.add_dimension_evaluation(dim_eval1)
        
        # 标记完成
        evaluation.mark_completed()
        self.assertEqual(evaluation.status, self.EvaluationStatus.COMPLETED)
        
        logger.info(f"  工作流完成，状态: {evaluation.status}")

    def test_02_evaluation_with_multiple_dimensions(self):
        """测试多维度评价"""
        logger.info("测试02: 多维度评价")
        
        dimensions = ["completeness", "rationality", "feasibility", "risk"]
        
        evaluation = self.SolutionEvaluation.from_solution(
            self.test_solution,
            "EVAL_INT_002",
            dimensions
        )
        
        # 为每个维度添加评价
        scores = [85.0, 78.0, 72.0, 68.0]
        for i, dim in enumerate(dimensions):
            dim_eval = self.DimensionEvaluation(
                dimension=dim,
                agent_id="INT_TEST_001",
                score=scores[i],
                level="good" if scores[i] >= 75 else "average",
                summary=f"{dim}评价",
                status=self.EvaluationStatus.COMPLETED
            )
            evaluation.add_dimension_evaluation(dim_eval)
        
        # 计算综合得分
        evaluation.mark_completed()
        
        self.assertEqual(len(evaluation.dimension_evaluations), 4)
        self.assertGreater(evaluation.overall_score, 0)
        
        logger.info(f"  多维度评价完成，综合得分: {evaluation.overall_score}")

    def test_03_evaluation_summary_and_report(self):
        """测试评价摘要和报告"""
        logger.info("测试03: 评价摘要和报告")
        
        evaluation = self.SolutionEvaluation.from_solution(
            self.test_solution,
            "EVAL_INT_003",
            ["completeness"]
        )
        
        dim_eval = self.DimensionEvaluation(
            dimension="completeness",
            agent_id="INT_TEST_001",
            score=85.0,
            level="good",
            summary="完整性良好",
            recommendations=["建议1", "建议2"],
            status=self.EvaluationStatus.COMPLETED
        )
        evaluation.add_dimension_evaluation(dim_eval)
        evaluation.mark_completed()
        
        # 获取摘要
        summary = evaluation.get_summary()
        self.assertIn("evaluation_id", summary)
        self.assertIn("overall_score", summary)
        
        # 获取详细报告
        report = evaluation.get_detailed_report()
        self.assertIn("solution", report)
        self.assertIn("overall", report)
        self.assertIn("dimensions", report)
        
        logger.info(f"  摘要和报告生成成功")


if __name__ == '__main__':
    unittest.main()
