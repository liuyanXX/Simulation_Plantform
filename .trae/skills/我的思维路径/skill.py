"""
我的思维路径 - 交互日志记录模块

功能：记录与Trae交互的内容到日志文件
"""

import os
import datetime

LOG_FILE_NAME = "交互日志.log"


def get_log_path() -> str:
    """获取日志文件路径"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))))
    return os.path.join(project_root, LOG_FILE_NAME)


def ensure_log_file():
    """确保日志文件存在"""
    log_path = get_log_path()
    if not os.path.exists(log_path):
        with open(log_path, 'w', encoding='utf-8') as f:
            f.write("")


def log_interaction(log_type: str, content: str):
    """
    记录交互内容到日志文件
    
    Args:
        log_type: 日志类型（用户提问/系统回答/操作记录/系统分析/代码修改/日志记录）
        content: 日志内容
    """
    ensure_log_file()
    log_path = get_log_path()
    
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    log_entry = f"""================================================================================
时间: {timestamp}
类型: {log_type}
内容:
{content}
--------------------------------------------------------------------------------

"""
    
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(log_entry)


def log_user_question(question: str):
    """记录用户提问"""
    log_interaction("用户提问", question)


def log_system_answer(answer: str):
    """记录系统回答"""
    log_interaction("系统回答", answer)


def log_operation(operation: str):
    """记录操作记录"""
    log_interaction("操作记录", operation)


def log_analysis(analysis: str):
    """记录系统分析"""
    log_interaction("系统分析", analysis)


def log_code_modification(modification: str):
    """记录代码修改"""
    log_interaction("代码修改", modification)


def log_logging(logging: str):
    """记录日志记录操作"""
    log_interaction("日志记录", logging)


def view_logs(lines: int = 100) -> str:
    """
    查看最近的日志记录
    
    Args:
        lines: 返回的行数
    
    Returns:
        日志内容字符串
    """
    log_path = get_log_path()
    if not os.path.exists(log_path):
        return "日志文件不存在"
    
    with open(log_path, 'r', encoding='utf-8') as f:
        all_lines = f.readlines()
    
    start = max(0, len(all_lines) - lines)
    return ''.join(all_lines[start:])


if __name__ == "__main__":
    # 测试功能
    log_user_question("测试思维路径记录功能（Simulation_Plantform）")
    log_system_answer("测试成功，思维路径已记录（Simulation_Plantform）")
    log_operation("测试操作：调用log_interaction函数（Simulation_Plantform）")
    print("测试完成，日志已记录")