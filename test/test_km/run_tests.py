"""测试运行脚本

运行所有知识管理模块的测试。
"""

import unittest
import os
import sys
import logging
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def run_all_tests():
    """运行所有测试"""
    # 配置日志
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'log')
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(log_dir, 'test_all.log')
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
    logger.info("开始运行知识管理模块测试套件")
    logger.info(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 80)

    # 发现并加载所有测试
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover(
        start_dir=os.path.dirname(__file__),
        pattern='test_*.py'
    )

    # 运行测试
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)

    # 输出测试结果摘要
    logger.info("\n" + "=" * 80)
    logger.info("测试结果摘要")
    logger.info("=" * 80)
    logger.info(f"运行测试: {result.testsRun}")
    logger.info(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    logger.info(f"失败: {len(result.failures)}")
    logger.info(f"错误: {len(result.errors)}")

    if result.failures:
        logger.info("\n失败的测试:")
        for test, traceback in result.failures:
            logger.info(f"  - {test}")
            logger.info(f"    {traceback}")

    if result.errors:
        logger.info("\n出错的测试:")
        for test, traceback in result.errors:
            logger.info(f"  - {test}")
            logger.info(f"    {traceback}")

    logger.info("\n" + "=" * 80)
    logger.info("测试完成")
    logger.info("=" * 80)

    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
