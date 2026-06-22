"""测试SolutionEvaluation模块"""
import unittest
import logging
import os
import sys
from datetime import datetime
from typing import Dict, Any

# 配置日志
log_file = os.path.join("logs", "test_solution_evaluation.log")
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


class TestSolutionEvaluation(unittest.TestCase):
    """测试SolutionEvaluation类"""

    @classmethod
    def setUpClass(cls):
        """设置测试类"""
        logger.info("=" * 60)
        logger.info("开始测试SolutionEvaluation")
        logger.info("=" * 60)

        from solution_evaluation_services import (
            SolutionEvaluation,
            DimensionEvaluation,
            EvaluationStatus
        )
        from bo.solution import Solution

        cls.SolutionEvaluation = SolutionEvaluation
        cls.DimensionEvaluation = DimensionEvaluation
        cls.EvaluationStatus = EvaluationStatus

        # 创建测试方案
        cls.test_solution = Solution(
            solution_id="SOL_TEST_001",
            name="测试方案",
            version="1.0",
            purpose="测试目的",
            objectives=["目标1", "目标2"],
            initiatives=["举措1", "举措2", "举措3"],
            work_content="测试工作内容"
        )

    def test_01_create_from_solution(self):
        """测试从方案创建评价对象"""
        logger.info("测试01: 从方案创建评价对象")
        
        evaluation = self.SolutionEvaluation.from_solution(
            self.test_solution,
            "EVAL_TEST_001",
            ["completeness", "rationality"]
        )
        
        self.assertEqual(evaluation.evaluation_id, "EVAL_TEST_001")
        self.assertEqual(evaluation.solution_id, "SOL_TEST_001")
        self.assertEqual(evaluation.solution_name, "测试方案")
        self.assertEqual(len(evaluation.evaluation_dimensions), 2)
        
        logger.info(f"  创建评价对象: {evaluation.evaluation_id}")

    def test_02_add_dimension_evaluation(self):
        """测试添加维度评价"""
        logger.info("测试02: 添加维度评价")
        
        evaluation = self.SolutionEvaluation.from_solution(
            self.test_solution,
            "EVAL_TEST_002",
            ["completeness"]
        )
        
        # 创建维度评价
        dimension_eval = self.DimensionEvaluation(
            dimension="completeness",
            agent_id="AGENT_001",
            agent_name="完整性Agent",
            score=85.5,
            level="good",
            summary="方案完整性良好",
            recommendations=["建议1"],
            status=self.EvaluationStatus.COMPLETED
        )
        
        evaluation.add_dimension_evaluation(dimension_eval)
        
        self.assertEqual(len(evaluation.dimension_evaluations), 1)
        
        logger.info(f"  添加维度评价: {dimension_eval.dimension} = {dimension_eval.score}")

    def test_03_update_dimension_evaluation(self):
        """测试更新维度评价"""
        logger.info("测试03: 更新维度评价")
        
        evaluation = self.SolutionEvaluation.from_solution(
            self.test_solution,
            "EVAL_TEST_003",
            ["completeness"]
        )
        
        # 添加第一个评价
        dim_eval1 = self.DimensionEvaluation(
            dimension="completeness",
            agent_id="AGENT_001",
            score=80.0,
            level="good",
            summary="第一次评价",
            status=self.EvaluationStatus.COMPLETED
        )
        evaluation.add_dimension_evaluation(dim_eval1)
        
        # 添加第二个评价（更新）
        dim_eval2 = self.DimensionEvaluation(
            dimension="completeness",
            agent_id="AGENT_002",
            score=90.0,
            level="excellent",
            summary="第二次评价",
            status=self.EvaluationStatus.COMPLETED
        )
        evaluation.add_dimension_evaluation(dim_eval2)
        
        # 验证只有一个评价
        self.assertEqual(len(evaluation.dimension_evaluations), 1)
        self.assertEqual(evaluation.dimension_evaluations[0].score, 90.0)
        
        logger.info("  维度评价更新成功")

    def test_04_set_dimension_agent(self):
        """测试设置维度Agent映射"""
        logger.info("测试04: 设置维度Agent映射")
        
        evaluation = self.SolutionEvaluation(
            evaluation_id="EVAL_TEST_004",
            solution_id="SOL_TEST_001",
            solution_name="测试方案"
        )
        
        evaluation.set_dimension_agent("completeness", "AGENT_001")
        evaluation.set_dimension_agent("rationality", "AGENT_002")
        
        self.assertEqual(evaluation.dimension_agents["completeness"], "AGENT_001")
        self.assertEqual(evaluation.dimension_agents["rationality"], "AGENT_002")
        self.assertIn("completeness", evaluation.evaluation_dimensions)
        self.assertIn("rationality", evaluation.evaluation_dimensions)
        
        logger.info(f"  维度映射: {evaluation.dimension_agents}")

    def test_05_get_dimension_evaluation(self):
        """测试获取维度评价"""
        logger.info("测试05: 获取维度评价")
        
        evaluation = self.SolutionEvaluation.from_solution(
            self.test_solution,
            "EVAL_TEST_005",
            ["completeness", "rationality"]
        )
        
        # 添加评价
        dim_eval1 = self.DimensionEvaluation(
            dimension="completeness",
            agent_id="AGENT_001",
            score=85.0,
            level="good",
            summary="完整性评价",
            status=self.EvaluationStatus.COMPLETED
        )
        evaluation.add_dimension_evaluation(dim_eval1)
        
        dim_eval2 = self.DimensionEvaluation(
            dimension="rationality",
            agent_id="AGENT_002",
            score=75.0,
            level="average",
            summary="合理性评价",
            status=self.EvaluationStatus.COMPLETED
        )
        evaluation.add_dimension_evaluation(dim_eval2)
        
        # 获取评价
        completeness_eval = evaluation.get_dimension_evaluation("completeness")
        self.assertIsNotNone(completeness_eval)
        self.assertEqual(completeness_eval.score, 85.0)
        
        logger.info(f"  获取completeness评价: {completeness_eval.score}")

    def test_06_get_agent_evaluations(self):
        """测试获取指定Agent的评价"""
        logger.info("测试06: 获取指定Agent的评价")
        
        evaluation = self.SolutionEvaluation.from_solution(
            self.test_solution,
            "EVAL_TEST_006",
            ["completeness", "rationality"]
        )
        
        # 添加评价
        dim_eval1 = self.DimensionEvaluation(
            dimension="completeness",
            agent_id="AGENT_001",
            score=85.0,
            level="good",
            summary="完整性评价",
            status=self.EvaluationStatus.COMPLETED
        )
        evaluation.add_dimension_evaluation(dim_eval1)
        
        dim_eval2 = self.DimensionEvaluation(
            dimension="rationality",
            agent_id="AGENT_001",
            score=75.0,
            level="average",
            summary="合理性评价",
            status=self.EvaluationStatus.COMPLETED
        )
        evaluation.add_dimension_evaluation(dim_eval2)
        
        # 获取Agent的评价
        agent_evals = evaluation.get_agent_evaluations("AGENT_001")
        self.assertEqual(len(agent_evals), 2)
        
        logger.info(f"  AGENT_001的评价数量: {len(agent_evals)}")

    def test_07_calculate_overall_score(self):
        """测试综合得分计算"""
        logger.info("测试07: 综合得分计算")
        
        evaluation = self.SolutionEvaluation.from_solution(
            self.test_solution,
            "EVAL_TEST_007",
            ["completeness", "rationality", "feasibility"]
        )
        
        # 添加多个维度评价
        evaluations = [
            ("completeness", 90.0, "excellent", 0.9),
            ("rationality", 80.0, "good", 0.8),
            ("feasibility", 70.0, "average", 0.85)
        ]
        
        for dim, score, level, conf in evaluations:
            dim_eval = self.DimensionEvaluation(
                dimension=dim,
                agent_id="AGENT_001",
                score=score,
                level=level,
                summary=f"{dim}评价",
                confidence=conf,
                status=self.EvaluationStatus.COMPLETED
            )
            evaluation.add_dimension_evaluation(dim_eval)
        
        # 触发综合得分计算
        evaluation.mark_completed()
        
        self.assertGreater(evaluation.overall_score, 0)
        self.assertIn(evaluation.overall_level, ["excellent", "good", "average", "poor", "critical"])
        
        logger.info(f"  综合得分: {evaluation.overall_score}, 等级: {evaluation.overall_level}")

    def test_08_mark_in_progress(self):
        """测试标记为评估中"""
        logger.info("测试08: 标记为评估中")
        
        evaluation = self.SolutionEvaluation.from_solution(
            self.test_solution,
            "EVAL_TEST_008",
            ["completeness"]
        )
        
        self.assertEqual(evaluation.status, self.EvaluationStatus.PENDING)
        
        evaluation.mark_in_progress()
        
        self.assertEqual(evaluation.status, self.EvaluationStatus.IN_PROGRESS)
        logger.info(f"  状态: {evaluation.status}")

    def test_09_mark_completed(self):
        """测试标记为已完成"""
        logger.info("测试09: 标记为已完成")
        
        evaluation = self.SolutionEvaluation.from_solution(
            self.test_solution,
            "EVAL_TEST_009",
            ["completeness"]
        )
        
        evaluation.mark_in_progress()
        evaluation.mark_completed()
        
        self.assertEqual(evaluation.status, self.EvaluationStatus.COMPLETED)
        self.assertIsNotNone(evaluation.completed_at)
        
        logger.info(f"  状态: {evaluation.status}, 完成时间: {evaluation.completed_at}")

    def test_10_mark_failed(self):
        """测试标记为失败"""
        logger.info("测试10: 标记为失败")
        
        evaluation = self.SolutionEvaluation.from_solution(
            self.test_solution,
            "EVAL_TEST_010",
            ["completeness"]
        )
        
        evaluation.mark_failed("测试失败")
        
        self.assertEqual(evaluation.status, self.EvaluationStatus.FAILED)
        
        logger.info(f"  状态: {evaluation.status}")

    def test_11_get_summary(self):
        """测试获取评价摘要"""
        logger.info("测试11: 获取评价摘要")
        
        evaluation = self.SolutionEvaluation.from_solution(
            self.test_solution,
            "EVAL_TEST_011",
            ["completeness", "rationality"]
        )
        
        dim_eval = self.DimensionEvaluation(
            dimension="completeness",
            agent_id="AGENT_001",
            score=85.0,
            level="good",
            summary="完整性良好",
            status=self.EvaluationStatus.COMPLETED
        )
        evaluation.add_dimension_evaluation(dim_eval)
        
        summary = evaluation.get_summary()
        
        self.assertIn("evaluation_id", summary)
        self.assertIn("solution_id", summary)
        self.assertIn("overall_score", summary)
        self.assertIn("dimensions_count", summary)
        self.assertEqual(summary["dimensions_count"], 2)
        
        logger.info(f"  摘要: evaluation_id={summary['evaluation_id']}, score={summary['overall_score']}")

    def test_12_get_detailed_report(self):
        """测试获取详细报告"""
        logger.info("测试12: 获取详细报告")
        
        evaluation = self.SolutionEvaluation.from_solution(
            self.test_solution,
            "EVAL_TEST_012",
            ["completeness"]
        )
        
        dim_eval = self.DimensionEvaluation(
            dimension="completeness",
            agent_id="AGENT_001",
            score=85.0,
            level="good",
            summary="完整性良好",
            recommendations=["建议1", "建议2"],
            status=self.EvaluationStatus.COMPLETED
        )
        evaluation.add_dimension_evaluation(dim_eval)
        evaluation.mark_completed()
        
        report = evaluation.get_detailed_report()
        
        self.assertIn("evaluation_id", report)
        self.assertIn("solution", report)
        self.assertIn("overall", report)
        self.assertIn("dimensions", report)
        self.assertEqual(len(report["dimensions"]), 1)
        
        logger.info(f"  报告维度: {len(report['dimensions'])}")

    def test_13_score_to_level_conversion(self):
        """测试分数到等级转换"""
        logger.info("测试13: 分数到等级转换")
        
        evaluation = self.SolutionEvaluation.from_solution(
            self.test_solution,
            "EVAL_TEST_013",
            []
        )
        
        test_cases = [
            (95, "excellent"),
            (85, "good"),
            (65, "average"),
            (45, "poor"),
            (25, "critical")
        ]
        
        for score, expected_level in test_cases:
            level = evaluation._score_to_level(score)
            self.assertEqual(level, expected_level)
            logger.info(f"  {score} -> {level}")


class TestDimensionEvaluation(unittest.TestCase):
    """测试DimensionEvaluation类"""

    @classmethod
    def setUpClass(cls):
        """设置测试类"""
        logger.info("=" * 60)
        logger.info("开始测试DimensionEvaluation")
        logger.info("=" * 60)

        from solution_evaluation_services import DimensionEvaluation, EvaluationStatus

        cls.DimensionEvaluation = DimensionEvaluation
        cls.EvaluationStatus = EvaluationStatus

    def test_01_create_dimension_evaluation(self):
        """测试创建维度评价"""
        logger.info("测试01: 创建维度评价")
        
        dim_eval = self.DimensionEvaluation(
            dimension="completeness",
            agent_id="AGENT_001",
            agent_name="完整性Agent",
            score=85.5,
            level="good",
            summary="方案完整性良好",
            details={"metrics": {"goal": 90, "initiative": 80}},
            recommendations=["建议1", "建议2"],
            confidence=0.9,
            status=self.EvaluationStatus.COMPLETED
        )
        
        self.assertEqual(dim_eval.dimension, "completeness")
        self.assertEqual(dim_eval.score, 85.5)
        self.assertEqual(len(dim_eval.recommendations), 2)
        
        logger.info(f"  创建维度评价: {dim_eval.dimension} = {dim_eval.score}")

    def test_02_default_values(self):
        """测试默认值"""
        logger.info("测试02: 默认值")
        
        dim_eval = self.DimensionEvaluation(
            dimension="rationality",
            agent_id="AGENT_001",
            score=75.0,
            level="average",
            summary="合理性评价"
        )
        
        self.assertEqual(dim_eval.confidence, 0.8)
        self.assertEqual(dim_eval.status, self.EvaluationStatus.PENDING)
        self.assertEqual(len(dim_eval.recommendations), 0)
        
        logger.info(f"  默认值: confidence={dim_eval.confidence}, status={dim_eval.status}")

    def test_03_validation(self):
        """测试参数验证"""
        logger.info("测试03: 参数验证")
        
        from pydantic import ValidationError
        
        # 测试无效的score
        with self.assertRaises(ValidationError):
            self.DimensionEvaluation(
                dimension="completeness",
                agent_id="AGENT_001",
                score=150.0,  # 超出范围
                level="good",
                summary="测试"
            )
        
        # 测试无效的confidence
        with self.assertRaises(ValidationError):
            self.DimensionEvaluation(
                dimension="completeness",
                agent_id="AGENT_001",
                score=85.0,
                level="good",
                summary="测试",
                confidence=1.5  # 超出范围
            )
        
        logger.info("  参数验证通过")


class TestEvaluationStatus(unittest.TestCase):
    """测试EvaluationStatus枚举"""

    @classmethod
    def setUpClass(cls):
        """设置测试类"""
        logger.info("=" * 60)
        logger.info("开始测试EvaluationStatus枚举")
        logger.info("=" * 60)

        from solution_evaluation_services import EvaluationStatus

        cls.EvaluationStatus = EvaluationStatus

    def test_01_status_values(self):
        """测试状态值"""
        logger.info("测试01: 状态值")
        
        expected_statuses = ["pending", "in_progress", "completed", "failed"]
        
        for status_name in expected_statuses:
            status = getattr(self.EvaluationStatus, status_name.upper())
            self.assertEqual(status.value, status_name)
            logger.info(f"  {status_name.upper()}: {status.value}")


if __name__ == '__main__':
    unittest.main()
