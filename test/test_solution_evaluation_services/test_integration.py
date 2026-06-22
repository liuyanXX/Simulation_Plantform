"""方案评估与分析服务模块组合调用测试"""
import unittest
import logging
import os
import sys
import shutil
from datetime import datetime
from typing import Dict, Any

# 配置日志
log_file = os.path.join("logs", "test_integration.log")
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


class TestIntegration(unittest.TestCase):
    """组合调用测试"""

    @classmethod
    def setUpClass(cls):
        """设置测试类"""
        logger.info("=" * 80)
        logger.info("开始方案评估与分析服务模块组合调用测试")
        logger.info("=" * 80)

        from solution_evaluation_services import (
            EvaluationProxy,
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

        cls.EvaluationProxy = EvaluationProxy
        cls.ServiceGateway = ServiceGateway
        cls.AgentRegistry = AgentRegistry
        cls.SolutionEvaluation = SolutionEvaluation
        cls.DimensionEvaluation = DimensionEvaluation
        cls.EvaluationStatus = EvaluationStatus
        cls.AgentType = AgentType
        cls.BaseEvaluationAgent = BaseEvaluationAgent
        cls.AgentConfig = AgentConfig

        # 创建测试存储目录
        cls.test_storage_path = "test_integration_data"
        cls.test_sim_log_path = "test_int_simulation_logs"
        cls.test_eval_log_path = "test_int_evaluation_logs"
        
        os.makedirs(cls.test_storage_path, exist_ok=True)
        os.makedirs(cls.test_sim_log_path, exist_ok=True)
        os.makedirs(cls.test_eval_log_path, exist_ok=True)

        # 创建注册表
        cls.registry = AgentRegistry(storage_path=cls.test_storage_path)
        cls.registry.clear()

        # 注册多种类型的测试Agent
        agent_configs = [
            ("INT_AGENT_001", "完整性Agent", AgentType.CUSTOM, ["completeness", "analysis"]),
            ("INT_AGENT_002", "合理性Agent", AgentType.CUSTOM, ["rationality", "analysis"]),
            ("INT_AGENT_003", "可行性Agent", AgentType.FEASIBILITY, ["feasibility", "evaluation"]),
            ("INT_AGENT_004", "风险Agent", AgentType.RISK, ["risk", "evaluation"]),
            ("INT_AGENT_005", "仿真Agent", AgentType.CUSTOM, ["simulation", "analysis"])
        ]

        for agent_id, name, agent_type, caps in agent_configs:
            config = AgentConfig(
                agent_id=agent_id,
                name=name,
                agent_type=agent_type,
                description=f"{name}的描述"
            )
            agent = BaseEvaluationAgent(config)
            cls.registry.register(agent, capabilities=caps)

        # 创建服务网关
        cls.gateway = ServiceGateway(cls.registry)

        # 创建评价代理
        cls.proxy = EvaluationProxy(
            registry=cls.registry,
            simulation_log_path=cls.test_sim_log_path,
            log_path=cls.test_eval_log_path
        )

        logger.info(f"  已注册Agent数量: {len(cls.registry.list_agents())}")

    @classmethod
    def tearDownClass(cls):
        """清理测试类"""
        logger.info("=" * 80)
        logger.info("方案评估与分析服务模块组合调用测试完成")
        logger.info("=" * 80)
        
        shutil.rmtree(cls.test_storage_path, ignore_errors=True)
        shutil.rmtree(cls.test_sim_log_path, ignore_errors=True)
        shutil.rmtree(cls.test_eval_log_path, ignore_errors=True)

    def test_01_registry_gateway_proxy_workflow(self):
        """测试01: 注册表-网关-代理工作流"""
        logger.info("测试01: 注册表-网关-代理工作流")
        
        # 1. 通过注册表获取可用Agent
        available_agents = self.registry.get_available_agents()
        logger.info(f"  1.1 可用Agent数: {len(available_agents)}")
        
        # 2. 通过网关获取可用Agent
        gateway_agents = self.gateway.get_available_agents()
        logger.info(f"  1.2 网关Agent数: {gateway_agents['total']}")
        
        # 3. 通过代理获取可用Agent
        proxy_agents = self.proxy.get_available_agents()
        logger.info(f"  1.3 代理Agent数: {proxy_agents.get('total', 0)}")
        
        # 4. 验证一致性
        self.assertGreater(len(available_agents), 0)
        self.assertEqual(gateway_agents['total'], len(available_agents))
        
        logger.info("  ✓ 注册表-网关-代理工作流正常")

    def test_02_create_and_evaluate_workflow(self):
        """测试02: 创建和评价工作流"""
        logger.info("测试02: 创建和评价工作流")
        
        from bo.solution import Solution
        
        # 1. 创建测试方案
        test_solution = Solution(
            solution_id="SOL_INT_001",
            name="集成测试方案",
            version="1.0",
            purpose="测试集成评价功能",
            objectives=["目标1: 提高效率", "目标2: 降低成本"],
            initiatives=["举措1: 优化流程", "举措2: 引入自动化"],
            work_content="详细的方案内容描述"
        )
        logger.info(f"  2.1 创建方案: {test_solution.solution_id}")
        
        # 2. 创建评价
        evaluation = self.proxy.create_evaluation(
            test_solution,
            ["completeness", "rationality"],
            evaluator="系统测试"
        )
        logger.info(f"  2.2 创建评价: {evaluation.evaluation_id}")
        
        # 3. 执行评价
        result = self.proxy.evaluate_solution(
            test_solution,
            ["completeness"]
        )
        logger.info(f"  2.3 执行评价: {result.status}")
        
        # 4. 获取摘要
        summary = self.proxy.get_evaluation_summary(result)
        logger.info(f"  2.4 评价摘要: score={summary.get('overall_score')}")
        
        self.assertIsNotNone(evaluation)
        self.assertIsNotNone(result)
        
        logger.info("  ✓ 创建和评价工作流正常")

    def test_03_multi_dimension_evaluation(self):
        """测试03: 多维度评价"""
        logger.info("测试03: 多维度评价")
        
        from bo.solution import Solution
        
        # 创建测试方案
        test_solution = Solution(
            solution_id="SOL_INT_002",
            name="多维度测试方案",
            version="1.0",
            purpose="多维度评价测试",
            objectives=["目标1", "目标2"],
            initiatives=["举措1", "举措2", "举措3", "举措4"],
            work_content="多维度测试内容"
        )
        
        # 创建多维度评价
        evaluation = self.proxy.create_evaluation(
            test_solution,
            ["completeness", "rationality", "feasibility", "risk"]
        )
        
        logger.info(f"  3.1 评价维度数: {len(evaluation.evaluation_dimensions)}")
        
        # 为每个维度添加评价
        dimensions = [
            ("completeness", 88.5, "good", "完整性良好"),
            ("rationality", 82.0, "good", "合理性良好"),
            ("feasibility", 75.0, "average", "可行性一般"),
            ("risk", 68.0, "average", "风险中等")
        ]
        
        for i, (dim, score, level, summary) in enumerate(dimensions):
            dim_eval = self.DimensionEvaluation(
                dimension=dim,
                agent_id=f"INT_AGENT_{str(i+1).zfill(3)}",
                agent_name=f"测试Agent{i+1}",
                score=score,
                level=level,
                summary=summary,
                recommendations=[f"{dim}建议{i+1}"],
                status=self.EvaluationStatus.COMPLETED,
                confidence=0.85
            )
            evaluation.add_dimension_evaluation(dim_eval)
        
        # 标记完成
        evaluation.mark_completed()
        
        logger.info(f"  3.2 维度评价数: {len(evaluation.dimension_evaluations)}")
        logger.info(f"  3.3 综合得分: {evaluation.overall_score}")
        logger.info(f"  3.4 综合等级: {evaluation.overall_level}")
        
        # 获取详细报告
        report = self.proxy.get_evaluation_report(evaluation)
        
        self.assertEqual(len(report["dimensions"]), 4)
        self.assertGreater(evaluation.overall_score, 0)
        
        logger.info("  ✓ 多维度评价正常")

    def test_04_agent_selection_and_routing(self):
        """测试04: Agent选择和路由"""
        logger.info("测试04: Agent选择和路由")
        
        from bo.solution import Solution
        
        # 创建测试方案
        test_solution = Solution(
            solution_id="SOL_INT_003",
            name="路由测试方案",
            version="1.0",
            purpose="测试Agent路由",
            objectives=["目标1"],
            initiatives=["举措1"],
            work_content="路由测试内容"
        )
        
        # 创建评价
        evaluation = self.SolutionEvaluation.from_solution(
            test_solution,
            "EVAL_INT_003",
            ["feasibility", "risk"]
        )
        
        # 按维度路由
        for dimension in ["feasibility", "risk"]:
            logger.info(f"  4.1 路由到维度: {dimension}")
            result = self.gateway.route_to_agent(evaluation, dimension)
            logger.info(f"  4.2 路由结果: {result.status}")
        
        logger.info("  ✓ Agent选择和路由正常")

    def test_05_evaluation_with_simulation(self):
        """测试05: 带仿真的评价"""
        logger.info("测试05: 带仿真的评价")
        
        from bo.solution import Solution
        
        # 创建测试方案
        test_solution = Solution(
            solution_id="SOL_INT_004",
            name="仿真测试方案",
            version="1.0",
            purpose="测试仿真集成",
            objectives=["目标1"],
            initiatives=["举措1"],
            work_content="仿真测试内容"
        )
        
        # 创建仿真日志
        sim_log_content = """Simulation Log:
        [2026-06-19 10:00:00] Simulation started
        [2026-06-19 10:00:05] Loading configuration
        [2026-06-19 10:00:10] Initializing agents
        [2026-06-19 10:00:15] Running simulation steps
        [2026-06-19 10:00:30] Simulation completed successfully
        [2026-06-19 10:00:31] Results: efficiency=85%, coverage=92%
        """
        
        sim_log_file = os.path.join(self.test_sim_log_path, "SOL_INT_004.log")
        with open(sim_log_file, 'w', encoding='utf-8') as f:
            f.write(sim_log_content)
        
        logger.info(f"  5.1 创建仿真日志: {sim_log_file}")
        
        # 执行带仿真的评价
        evaluation = self.proxy.evaluate_solution(
            test_solution,
            ["completeness", "simulation"],
            include_simulation=True
        )
        
        logger.info(f"  5.2 评价状态: {evaluation.status}")
        
        self.assertTrue(os.path.exists(sim_log_file))
        
        logger.info("  ✓ 带仿真的评价正常")

    def test_06_evaluation_statistics(self):
        """测试06: 评价统计"""
        logger.info("测试06: 评价统计")
        
        # 获取注册表统计
        registry_stats = self.registry.get_statistics()
        logger.info(f"  6.1 注册表统计: {registry_stats}")
        
        # 获取网关Agent信息
        gateway_info = self.gateway.get_available_agents()
        logger.info(f"  6.2 网关Agent信息: total={gateway_info['total']}")
        
        # 获取代理可用维度
        dimensions = self.proxy.get_available_dimensions()
        logger.info(f"  6.3 可用维度: {dimensions}")
        
        self.assertGreater(registry_stats['total_agents'], 0)
        self.assertGreater(len(dimensions), 0)
        
        logger.info("  ✓ 评价统计正常")

    def test_07_evaluation_save_and_report(self):
        """测试07: 评价保存和报告生成"""
        logger.info("测试07: 评价保存和报告生成")
        
        from bo.solution import Solution
        
        # 创建测试方案
        test_solution = Solution(
            solution_id="SOL_INT_005",
            name="报告测试方案",
            version="1.0",
            purpose="测试报告功能",
            objectives=["目标1", "目标2"],
            initiatives=["举措1", "举措2"],
            work_content="报告测试内容"
        )
        
        # 创建评价
        evaluation = self.proxy.create_evaluation(
            test_solution,
            ["completeness", "rationality"]
        )
        
        # 添加评价结果
        dim_eval = self.DimensionEvaluation(
            dimension="completeness",
            agent_id="INT_AGENT_001",
            score=90.0,
            level="excellent",
            summary="方案非常完整",
            recommendations=["建议1: 继续保持", "建议2: 可以进一步优化"],
            status=self.EvaluationStatus.COMPLETED
        )
        evaluation.add_dimension_evaluation(dim_eval)
        evaluation.mark_completed()
        
        # 保存评价
        save_path = self.proxy.save_evaluation(evaluation)
        logger.info(f"  7.1 评价保存: {save_path}")
        self.assertTrue(os.path.exists(save_path))
        
        # 生成摘要
        summary = self.proxy.get_evaluation_summary(evaluation)
        logger.info(f"  7.2 摘要: score={summary.get('overall_score')}")
        
        # 生成详细报告
        report = self.proxy.get_evaluation_report(evaluation)
        logger.info(f"  7.3 报告维度数: {len(report.get('dimensions', []))}")
        
        self.assertIsNotNone(summary)
        self.assertIsNotNone(report)
        
        logger.info("  ✓ 评价保存和报告生成正常")

    def test_08_health_check_workflow(self):
        """测试08: 健康检查工作流"""
        logger.info("测试08: 健康检查工作流")
        
        # 检查所有Agent健康状态
        health_all = self.registry.check_all_health()
        logger.info(f"  8.1 所有Agent健康状态:")
        
        for agent_id, health in health_all.items():
            logger.info(f"      {agent_id}: {health['status']}")
        
        # 检查特定Agent
        for agent_id in ["INT_AGENT_001", "INT_AGENT_002"]:
            health = self.registry.check_health(agent_id)
            logger.info(f"  8.2 {agent_id}: {health['status']}")
        
        self.assertGreater(len(health_all), 0)
        
        logger.info("  ✓ 健康检查工作流正常")

    def test_09_gateway_dimension_mapping(self):
        """测试09: 网关维度映射"""
        logger.info("测试09: 网关维度映射")
        
        # 获取当前映射
        mapping = self.gateway.get_dimension_agent_mapping()
        logger.info(f"  9.1 当前维度映射: {len(mapping)} 个")
        
        # 添加自定义映射
        self.gateway.register_dimension_agent_mapping("custom", self.AgentType.GENERAL)
        
        # 验证映射已添加
        updated_mapping = self.gateway.get_dimension_agent_mapping()
        self.assertIn("custom", updated_mapping)
        
        logger.info(f"  9.2 更新后维度映射: {len(updated_mapping)} 个")
        
        logger.info("  ✓ 网关维度映射正常")

    def test_10_complete_evaluation_lifecycle(self):
        """测试10: 完整评价生命周期"""
        logger.info("测试10: 完整评价生命周期")
        
        from bo.solution import Solution
        
        # 1. 创建方案
        test_solution = Solution(
            solution_id="SOL_INT_LIFECYCLE",
            name="生命周期测试方案",
            version="1.0",
            purpose="测试完整生命周期",
            objectives=["目标1: 优化流程", "目标2: 提高质量"],
            initiatives=["举措1: 引入新技术", "举措2: 培训团队", "举措3: 完善制度"],
            work_content="完整的方案内容"
        )
        logger.info(f"  10.1 创建方案: {test_solution.solution_id}")
        
        # 2. 创建评价
        evaluation = self.proxy.create_evaluation(
            test_solution,
            ["completeness", "rationality", "feasibility"],
            evaluator="生命周期测试"
        )
        self.assertEqual(evaluation.status, self.EvaluationStatus.PENDING)
        logger.info(f"  10.2 创建评价: {evaluation.evaluation_id}, status={evaluation.status}")
        
        # 3. 添加评价结果
        dimensions = [
            ("completeness", 92.0, "excellent", "非常完整"),
            ("rationality", 85.0, "good", "合理"),
            ("feasibility", 78.0, "good", "可行")
        ]
        
        for i, (dim, score, level, summary) in enumerate(dimensions):
            dim_eval = self.DimensionEvaluation(
                dimension=dim,
                agent_id=f"INT_AGENT_{str(i+1).zfill(3)}",
                score=score,
                level=level,
                summary=summary,
                recommendations=[f"{dim}优化建议"],
                status=self.EvaluationStatus.COMPLETED,
                confidence=0.9
            )
            evaluation.add_dimension_evaluation(dim_eval)
        
        # 4. 标记完成
        evaluation.mark_completed()
        logger.info(f"  10.3 标记完成: status={evaluation.status}, score={evaluation.overall_score}")
        
        # 5. 保存评价
        save_path = self.proxy.save_evaluation(evaluation)
        logger.info(f"  10.4 保存评价: {save_path}")
        
        # 6. 生成报告
        report = self.proxy.get_evaluation_report(evaluation)
        logger.info(f"  10.5 生成报告: {len(report['dimensions'])} 个维度")
        
        # 7. 获取评价历史
        history = self.proxy.get_evaluation_history(test_solution.solution_id)
        logger.info(f"  10.6 评价历史: {len(history)} 条")
        
        self.assertEqual(evaluation.status, self.EvaluationStatus.COMPLETED)
        self.assertGreater(evaluation.overall_score, 0)
        
        logger.info("  ✓ 完整评价生命周期正常")


if __name__ == '__main__':
    unittest.main()
