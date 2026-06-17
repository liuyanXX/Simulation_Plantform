"""评价代理模块

负责接收被评价方案及评价要求，协调评价Agent进行方案评价。
"""
import os
import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bo.solution import Solution
from .solution_evaluation import SolutionEvaluation, EvaluationStatus
from .service_gateway import ServiceGateway
from .agent_registry import AgentRegistry, get_registry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EvaluationProxy:
    """
    评价代理
    
    职责：
    1. 接收被评价方案及评价要求
    2. 根据评价要求找到对应的评价Agent
    3. 把方案对象通过服务网关传递给对应的评价Agent
    4. 接收评价Agent给出的结论
    5. 整合所有评价Agent给出的评价结论，并向前返回
    6. 所有操作内容记录日志
    7. 如果评价要求中涉及仿真结果，则查找仿真日志并传递给仿真结果分析Agent
    """
    
    def __init__(self, registry: Optional[AgentRegistry] = None, 
                 simulation_log_path: Optional[str] = None,
                 log_path: Optional[str] = None):
        """
        初始化评价代理
        
        :param registry: Agent注册表，默认使用全局注册表
        :param simulation_log_path: 仿真日志存储路径
        :param log_path: 评价日志存储路径
        """
        self._registry = registry
        self._simulation_log_path = simulation_log_path or "simulation_logs"
        self._log_path = log_path or "evaluation_logs"
        self._gateway = ServiceGateway(registry)
        self._logger = logger
        
        # 创建必要的目录
        os.makedirs(self._simulation_log_path, exist_ok=True)
        os.makedirs(self._log_path, exist_ok=True)
    
    def _get_registry(self) -> AgentRegistry:
        """获取Agent注册表"""
        if self._registry is None:
            self._registry = get_registry()
        return self._registry
    
    def _find_simulation_log(self, solution_id: str) -> Optional[str]:
        """
        查找方案的仿真日志
        
        :param solution_id: 方案ID
        :return: 仿真日志内容
        """
        log_file = os.path.join(self._simulation_log_path, f"{solution_id}.log")
        
        if os.path.exists(log_file):
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                self._logger.error(f"读取仿真日志失败: {e}")
        
        return None
    
    def _log_operation(self, operation: str, details: Dict[str, Any]) -> None:
        """
        记录操作日志
        
        :param operation: 操作类型
        :param details: 操作详情
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "details": details
        }
        
        log_file = os.path.join(self._log_path, f"evaluation_{datetime.now().strftime('%Y%m%d')}.log")
        
        try:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        except Exception as e:
            self._logger.error(f"写入日志失败: {e}")
    
    def create_evaluation(self, solution: Solution, 
                         dimensions: List[str],
                         evaluator: Optional[str] = None) -> SolutionEvaluation:
        """
        创建方案评价对象
        
        :param solution: 方案对象
        :param dimensions: 评价维度列表
        :param evaluator: 评价人
        :return: 方案评价对象
        """
        evaluation_id = f"EVAL_{solution.solution_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        evaluation = SolutionEvaluation.from_solution(solution, evaluation_id, dimensions)
        evaluation.evaluator = evaluator
        
        # 设置维度-Agent映射
        for dimension in dimensions:
            agent_type = self._gateway._dimension_agent_mapping.get(dimension)
            if agent_type:
                registry = self._get_registry()
                agent = registry.select_agent(agent_type)
                if agent:
                    evaluation.set_dimension_agent(dimension, agent.agent_id)
        
        self._log_operation("create_evaluation", {
            "evaluation_id": evaluation_id,
            "solution_id": solution.solution_id,
            "dimensions": dimensions,
            "evaluator": evaluator
        })
        
        return evaluation
    
    def evaluate_solution(self, solution: Solution, 
                         dimensions: List[str],
                         evaluator: Optional[str] = None,
                         include_simulation: bool = False) -> SolutionEvaluation:
        """
        评价方案
        
        :param solution: 方案对象
        :param dimensions: 评价维度列表
        :param evaluator: 评价人
        :param include_simulation: 是否包含仿真结果分析
        :return: 方案评价对象
        """
        self._logger.info(f"开始评价方案: {solution.solution_id}, 维度: {dimensions}")
        
        # 创建评价对象
        evaluation = self.create_evaluation(solution, dimensions, evaluator)
        
        # 如果需要仿真分析，添加仿真维度
        if include_simulation and "simulation" not in dimensions:
            evaluation.evaluation_dimensions.append("simulation")
        
        # 查找仿真日志
        simulation_log = None
        if include_simulation or "simulation" in dimensions:
            simulation_log = self._find_simulation_log(solution.solution_id)
            if simulation_log:
                self._logger.info(f"找到仿真日志: {solution.solution_id}")
            else:
                self._logger.warning(f"未找到仿真日志: {solution.solution_id}")
        
        # 通过服务网关处理评价
        evaluation = self._gateway.process_evaluation(evaluation, simulation_log)
        
        # 记录评价完成
        self._log_operation("evaluate_solution", {
            "evaluation_id": evaluation.evaluation_id,
            "solution_id": solution.solution_id,
            "dimensions": dimensions,
            "status": evaluation.status.value,
            "overall_score": evaluation.overall_score,
            "overall_level": evaluation.overall_level
        })
        
        self._logger.info(f"方案评价完成: {solution.solution_id}, 得分: {evaluation.overall_score}")
        
        return evaluation
    
    def evaluate_by_evaluation_id(self, evaluation_id: str) -> Optional[SolutionEvaluation]:
        """
        根据评价ID执行评价
        
        :param evaluation_id: 评价ID
        :return: 方案评价对象
        """
        self._logger.info(f"根据评价ID执行评价: {evaluation_id}")
        
        # 这里可以从存储中加载评价对象
        # 暂时返回None，实际实现需要从数据库或文件加载
        return None
    
    def get_evaluation_summary(self, evaluation: SolutionEvaluation) -> Dict[str, Any]:
        """
        获取评价摘要
        
        :param evaluation: 方案评价对象
        :return: 评价摘要
        """
        return evaluation.get_summary()
    
    def get_evaluation_report(self, evaluation: SolutionEvaluation) -> Dict[str, Any]:
        """
        获取详细评价报告
        
        :param evaluation: 方案评价对象
        :return: 详细报告
        """
        return evaluation.get_detailed_report()
    
    def get_available_dimensions(self) -> List[str]:
        """
        获取可用的评价维度
        
        :return: 维度列表
        """
        return list(self._gateway._dimension_agent_mapping.keys())
    
    def get_available_agents(self) -> Dict[str, Any]:
        """
        获取可用的Agent信息
        
        :return: Agent信息
        """
        return self._gateway.get_available_agents()
    
    def register_agent(self, agent, capabilities: Optional[List[str]] = None) -> bool:
        """
        注册Agent
        
        :param agent: Agent实例
        :param capabilities: 能力列表
        :return: 是否注册成功
        """
        registry = self._get_registry()
        return registry.register(agent, capabilities)
    
    def get_evaluation_history(self, solution_id: str, 
                               limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取方案的评价历史
        
        :param solution_id: 方案ID
        :param limit: 返回数量限制
        :return: 评价历史列表
        """
        # 这里可以从存储中查询评价历史
        # 暂时返回空列表，实际实现需要从数据库或文件查询
        return []
    
    def save_evaluation(self, evaluation: SolutionEvaluation) -> str:
        """
        保存评价结果
        
        :param evaluation: 方案评价对象
        :return: 保存路径
        """
        save_path = os.path.join(self._log_path, f"{evaluation.evaluation_id}.json")
        
        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(evaluation.get_detailed_report(), f, ensure_ascii=False, indent=2, default=str)
            
            self._log_operation("save_evaluation", {
                "evaluation_id": evaluation.evaluation_id,
                "solution_id": evaluation.solution_id,
                "save_path": save_path
            })
            
            return save_path
        except Exception as e:
            self._logger.error(f"保存评价结果失败: {e}")
            raise
    
    def load_evaluation(self, evaluation_id: str) -> Optional[SolutionEvaluation]:
        """
        加载评价结果
        
        :param evaluation_id: 评价ID
        :return: 方案评价对象
        """
        load_path = os.path.join(self._log_path, f"{evaluation_id}.json")
        
        if not os.path.exists(load_path):
            return None
        
        try:
            with open(load_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 这里需要将数据转换回SolutionEvaluation对象
                # 暂时返回None，实际实现需要完整的反序列化逻辑
                return None
        except Exception as e:
            self._logger.error(f"加载评价结果失败: {e}")
            return None