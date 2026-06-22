"""运行方案评估与分析服务模块的所有测试"""
import unittest
import sys
import os
import logging
from datetime import datetime

# 配置日志
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
os.makedirs(log_dir, exist_ok=True)

log_file = os.path.join(log_dir, "test_all.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def run_tests():
    """运行所有测试"""
    logger.info("=" * 80)
    logger.info("开始运行方案评估与分析服务模块测试")
    logger.info("=" * 80)
    
    start_time = datetime.now()
    
    # 测试文件列表
    test_files = [
        'test_base_evaluation_agent.py',
        'test_agent_registry.py',
        'test_solution_evaluation.py',
        'test_service_gateway.py',
        'test_evaluation_proxy.py',
        'test_integration.py'
    ]
    
    # 加载所有测试
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 获取测试目录
    test_dir = os.path.dirname(os.path.abspath(__file__))
    
    for test_file in test_files:
        test_path = os.path.join(test_dir, test_file)
        if os.path.exists(test_path):
            logger.info(f"加载测试: {test_file}")
            tests = loader.loadTestsFromName(test_file[:-3])
            suite.addTests(tests)
        else:
            logger.warning(f"测试文件不存在: {test_file}")
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 输出结果
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
    
    # 写入汇总日志
    summary_file = os.path.join(log_dir, "test_summary.log")
    with open(summary_file, 'a', encoding='utf-8') as f:
        f.write(f"\n{'=' * 80}\n")
        f.write(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"测试文件数: {len(test_files)}\n")
        f.write(f"总测试数: {result.testsRun}\n")
        f.write(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}\n")
        f.write(f"失败: {len(result.failures)}\n")
        f.write(f"错误: {len(result.errors)}\n")
        f.write(f"耗时: {duration:.2f}秒\n")
        
        if result.failures:
            f.write("\n失败详情:\n")
            for test, traceback in result.failures:
                f.write(f"  - {test}\n")
                f.write(f"    {traceback}\n")
        
        if result.errors:
            f.write("\n错误详情:\n")
            for test, traceback in result.errors:
                f.write(f"  - {test}\n")
                f.write(f"    {traceback}\n")
        
        f.write("=" * 80 + "\n")
    
    # 返回结果码
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    exit_code = run_tests()
    sys.exit(exit_code)
