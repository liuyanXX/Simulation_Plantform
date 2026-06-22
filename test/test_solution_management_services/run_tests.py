import os
import sys
import unittest
import logging
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/test_solution_management_all.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def run_tests():
    """运行所有方案管理服务模块测试"""
    logger.info("=" * 80)
    logger.info("开始运行方案管理服务模块测试")
    logger.info("=" * 80)
    
    start_time = datetime.now()
    
    test_files = [
        'test_llm_client.py',
        'test_solution_management_service.py',
        'test_solution_understanding_service.py',
        'test_solution_decomposition_service.py',
        'test_solution_management_module.py',
        'test_integration.py'
    ]
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    test_dir = os.path.dirname(os.path.abspath(__file__))
    
    for test_file in test_files:
        test_path = os.path.join(test_dir, test_file)
        if os.path.exists(test_path):
            logger.info(f"加载测试: {test_file}")
            try:
                tests = loader.loadTestsFromName(test_file[:-3])
                suite.addTests(tests)
            except Exception as e:
                logger.warning(f"加载失败 {test_file}: {e}")
        else:
            logger.warning(f"测试文件不存在: {test_file}")
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    logger.info("=" * 80)
    logger.info("测试结果汇总")
    logger.info("=" * 80)
    logger.info(f"总测试数: {result.testsRun}")
    logger.info(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    logger.info(f"失败: {len(result.failures)}")
    logger.info(f"错误: {len(result.errors)}")
    logger.info(f"耗时: {duration:.2f}秒")
    logger.info("=" * 80)
    
    if result.failures:
        logger.info("失败的测试:")
        for test, trace in result.failures:
            logger.info(f"  - {test}")
    
    if result.errors:
        logger.info("错误的测试:")
        for test, trace in result.errors:
            logger.info(f"  - {test}")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    os.makedirs('logs', exist_ok=True)
    success = run_tests()
    sys.exit(0 if success else 1)