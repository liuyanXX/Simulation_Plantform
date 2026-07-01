"""数据存储服务测试运行器

运行所有数据存储服务的单元测试和集成测试。
"""

import unittest
import os
import sys
import logging
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def run_all_tests():
    """运行所有数据存储服务测试"""
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, '测试文档.log')

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger(__name__)

    logger.info("=" * 80)
    logger.info("数据存储服务测试")
    logger.info("=" * 80)
    logger.info(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 80)

    test_dir = os.path.dirname(__file__)

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    test_files = [
        'test_sqlite_operator.py',
        'test_solution_service.py',
        'test_task_service.py',
        'test_worker_service.py',
        'test_organization_service.py',
        'test_role_service.py',
        'test_task_manifest_service.py',
        'test_task_flow_group_service.py',
        'test_tasks_graph_service.py',
        'test_knowledge_service.py',
        'test_integration.py'
    ]

    logger.info("\n测试文件清单:")
    for i, test_file in enumerate(test_files, 1):
        logger.info(f"  {i}. {test_file}")

    logger.info("\n" + "-" * 80)
    logger.info("开始执行测试...")
    logger.info("-" * 80 + "\n")

    for test_file in test_files:
        test_module = test_file.replace('.py', '')
        try:
            suite.addTests(loader.discover(test_dir, pattern=test_file))
            logger.info(f"加载测试文件: {test_file}")
        except Exception as e:
            logger.error(f"加载测试文件失败 {test_file}: {e}")

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    logger.info("\n" + "=" * 80)
    logger.info("测试结果汇总")
    logger.info("=" * 80)
    logger.info(f"测试用例总数: {result.testsRun}")
    logger.info(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    logger.info(f"失败: {len(result.failures)}")
    logger.info(f"错误: {len(result.errors)}")

    if result.failures:
        logger.info("\n失败的测试:")
        for test, traceback in result.failures:
            logger.info(f"  - {test}")
            logger.info(f"    {traceback}")

    if result.errors:
        logger.info("\n错误的测试:")
        for test, traceback in result.errors:
            logger.info(f"  - {test}")
            logger.info(f"    {traceback}")

    logger.info("\n" + "=" * 80)
    logger.info("测试完成")
    logger.info("=" * 80)

    return result


if __name__ == '__main__':
    result = run_all_tests()
    sys.exit(0 if result.wasSuccessful() else 1)