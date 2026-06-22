"""智能模型连接模块测试运行器

运行所有AI模块相关测试。
"""

import os
import sys
import unittest
import logging
from datetime import datetime

# 添加项目根目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, project_root)

# 定义日志目录
logs_dir = os.path.join(project_root, 'logs')
os.makedirs(logs_dir, exist_ok=True)

from test.test_ai.test_llm_client_module import get_test_suite


def run_tests():
    """运行所有AI模块测试"""
    logger = logging.getLogger("TestRunner")
    logger.info("=" * 80)
    logger.info("开始运行智能模型连接模块测试")
    logger.info("=" * 80)
    
    start_time = datetime.now()
    
    # 确保logs目录存在
    os.makedirs(logs_dir, exist_ok=True)
    
    # 配置日志文件
    log_file = os.path.join(logs_dir, f"test_ai_module_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    
    # 添加处理器到根日志
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2, resultclass=unittest.TestResult)
    result = runner.run(get_test_suite())
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    # 输出摘要
    summary = f"""
================================================================================
测试完成摘要
================================================================================
开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}
结束时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}
耗时: {duration:.2f}秒

运行测试: {result.testsRun}
成功: {result.testsRun - len(result.failures) - len(result.errors)}
失败: {len(result.failures)}
错误: {len(result.errors)}

"""
    print(summary)
    logger.info(summary)
    
    # 记录失败详情
    if result.failures:
        logger.error("=" * 80)
        logger.error("失败的测试:")
        for test, traceback in result.failures:
            logger.error(f"  - {test}")
            logger.error(traceback)
    
    if result.errors:
        logger.error("=" * 80)
        logger.error("错误的测试:")
        for test, traceback in result.errors:
            logger.error(f"  - {test}")
            logger.error(traceback)
    
    # 写入测试文档
    write_test_documentation(result, start_time, end_time, duration)
    
    return 0 if result.wasSuccessful() else 1


def write_test_documentation(result, start_time, end_time, duration):
    """写入测试文档"""
    doc_path = os.path.join(logs_dir, "测试文档.log")
    
    success_count = result.testsRun - len(result.failures) - len(result.errors)
    was_successful = result.wasSuccessful()
    
    # 状态描述
    if was_successful:
        status_desc = "全部通过"
    elif success_count > 0:
        status_desc = "部分通过"
    else:
        status_desc = "全部失败"
    
    content = f"""
================================================================================
智能模型连接模块测试文档
================================================================================
生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

================================================================================
一、测试概述
================================================================================
本次测试针对智能模型连接模块(ai_modules/basic/llm_client.py)进行全面测试，
验证模块的数据模型、客户端实现和工厂类功能。

测试模块:
- ai_modules.basic.llm_client
  - 数据模型: LLMRequest, LLMResponse, LLMConfig, OllamaConfig, OpenAIConfig, MockConfig
  - 抽象基类: LLMClient
  - 具体实现: MockLLMClient, OllamaLLMClient, OpenAIClient
  - 工厂类: LLMClientFactory

================================================================================
二、测试环境
================================================================================
测试框架: unittest
开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}
结束时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}
耗时: {duration:.2f}秒

================================================================================
三、测试结果
================================================================================
测试状态: {status_desc}
运行测试数: {result.testsRun}
成功: {success_count}
失败: {len(result.failures)}
错误: {len(result.errors)}

"""

    # 测试用例统计
    content += """
================================================================================
四、测试用例详情
================================================================================

1. 数据模型测试 (TestLLMRequest, TestLLMResponse, TestConfigModels)
   - test_create_valid_request: 测试创建有效的LLMRequest
   - test_request_with_all_fields: 测试包含所有字段的请求
   - test_prompt_validation: 测试提示词验证（空字符串应抛出异常）
   - test_temperature_constraints: 测试温度参数范围约束
   - test_create_response: 测试创建LLMResponse
   - test_response_with_usage: 测试包含token使用量的响应
   - test_ollama_config_defaults: 测试Ollama配置默认值
   - test_ollama_config_custom: 测试Ollama自定义配置
   - test_openai_config: 测试OpenAI配置
   - test_mock_config: 测试Mock配置
   - test_llm_config: 测试主配置模型

2. Mock客户端测试 (TestMockLLMClient)
   - test_call_understand_prompt: 测试理解提示词场景
   - test_call_decompose_prompt: 测试拆解提示词场景
   - test_call_unknown_prompt: 测试未知提示词（返回通用响应）
   - test_custom_responses: 测试自定义模拟响应映射
   - test_call_with_retry: 测试带重试机制的调用

3. Ollama客户端测试 (TestOllamaLLMClient)
   - test_init_with_defaults: 测试默认初始化参数
   - test_init_with_custom: 测试自定义初始化参数
   - test_disconnect: 测试断开连接
   - test_call_without_server: 测试无Ollama服务时的异常处理

4. OpenAI客户端测试 (TestOpenAIClient)
   - test_init_with_defaults: 测试默认初始化参数
   - test_init_with_custom: 测试自定义初始化参数

5. 工厂类测试 (TestLLMClientFactory)
   - test_create_mock_client: 测试创建Mock客户端
   - test_create_ollama_client: 测试创建Ollama客户端
   - test_create_openai_client: 测试创建OpenAI客户端
   - test_singleton_pattern: 测试单例模式
   - test_force_new_instance: 测试强制创建新实例
   - test_unknown_client_type: 测试未知客户端类型处理
   - test_register_client: 测试动态注册新客户端类型
   - test_close_and_reset: 测试关闭和重置工厂
   - test_config_loading: 测试配置文件加载
   - test_set_config: 测试程序化设置配置

6. 集成测试 (TestLLMClientIntegration)
   - test_config_and_factory_workflow: 测试配置和工厂完整工作流
   - test_multiple_client_types: 测试多种客户端类型切换
   - test_custom_parameters_override: 测试自定义参数覆盖配置

"""

    # 失败详情
    if result.failures:
        content += """
================================================================================
五、失败的测试
================================================================================
"""
        for i, (test, traceback) in enumerate(result.failures, 1):
            content += f"""
[{i}] {test}
{traceback}
"""
    
    if result.errors:
        content += """
================================================================================
六、出错的测试
================================================================================
"""
        for i, (test, traceback) in enumerate(result.errors, 1):
            content += f"""
[{i}] {test}
{traceback}
"""

    # 功能说明
    content += """
================================================================================
七、模块功能说明
================================================================================

1. LLMClientFactory (工厂类)
   - 从配置文件(llm_config.json)加载LLM配置
   - 根据配置动态创建LLMClient子类实例
   - 支持单例模式，确保同一配置只创建一个实例
   - 支持动态注册新的客户端类型

2. 支持的客户端类型
   - mock: MockLLMClient - 用于测试和开发
   - ollama: OllamaLLMClient - 连接本地Ollama服务
   - openai: OpenAIClient - 连接OpenAI API

3. 配置文件格式
   - 位置: ai_modules/basic/llm_config.json
   - 支持为每种客户端类型配置独立参数
   - 默认使用ollama + deepseek-r1:latest

================================================================================
八、测试通过标准
================================================================================
- 所有测试用例必须通过
- 无失败、无错误
- 测试日志正确生成

================================================================================
"""
    
    with open(doc_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"\n测试文档已生成: {doc_path}")


if __name__ == "__main__":
    exit_code = run_tests()
    sys.exit(exit_code)
