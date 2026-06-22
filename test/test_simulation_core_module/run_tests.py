import os
import sys
import unittest
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

os.makedirs('logs', exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/test_simulation_core_module.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def run_all_tests():
    """运行所有测试"""
    logger.info("=" * 70)
    logger.info("开始运行仿真核心模块测试套件")
    logger.info("=" * 70)
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromName('test_worker_type_registry'))
    suite.addTests(loader.loadTestsFromName('test_simulation_task'))
    suite.addTests(loader.loadTestsFromName('test_simulation_process_engine'))
    suite.addTests(loader.loadTestsFromName('test_task_dispatch_engine'))
    suite.addTests(loader.loadTestsFromName('test_simulation_process_module'))
    suite.addTests(loader.loadTestsFromName('test_integration'))
    
    runner = unittest.TextTestRunner(verbosity=2)
    
    logger.info("\n" + "=" * 70)
    logger.info("运行单元测试...")
    logger.info("=" * 70)
    
    result = runner.run(suite)
    
    logger.info("\n" + "=" * 70)
    logger.info("测试结果汇总")
    logger.info("=" * 70)
    logger.info(f"测试用例总数: {result.testsRun}")
    logger.info(f"失败用例数: {len(result.failures)}")
    logger.info(f"错误用例数: {len(result.errors)}")
    
    if result.failures:
        logger.info("\n失败用例:")
        for test, traceback in result.failures:
            logger.info(f"  - {test}")
            logger.info(f"    {traceback[:200]}...")
    
    if result.errors:
        logger.info("\n错误用例:")
        for test, traceback in result.errors:
            logger.info(f"  - {test}")
            logger.info(f"    {traceback[:200]}...")
    
    logger.info("=" * 70)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)