"""方案理解服务子模块

负责把原始方案文档对象拆分为结构化形式的方案对象，
并提供对该对象的增、删、改、查、存服务。

使用大模型进行文档理解和结构化提取。
"""
import os
import json
import logging
from datetime import datetime
from typing import Optional, Dict, List, Any
from pydantic import BaseModel, Field

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/..')
from bo.solution import Solution, SolutionDocument, SolutionStatus, SolutionPriority
from ai_modules.basic.llm_client import LLMClient, LLMRequest, LLMClientFactory


class UnderstandingResult(BaseModel):
    """方案理解结果"""
    success: bool = Field(description="是否成功")
    solution: Optional[Solution] = Field(default=None, description="理解后的方案对象")
    raw_response: Optional[str] = Field(default=None, description="大模型原始响应")
    error_message: Optional[str] = Field(default=None, description="错误信息")
    processing_time_ms: Optional[int] = Field(default=None, description="处理时间（毫秒）")


class SolutionUnderstandingService:
    """
    方案理解服务子模块
    
    通过调用外部大模型，将非结构化的方案文档文本转化为结构化的方案对象。
    提供对方案对象的完整生命周期管理。
    
    核心功能：
    - understand_document: 理解文档并提取结构化方案
    - create_solution: 创建方案对象
    - get_solution: 查询方案对象
    - update_solution: 更新方案对象
    - delete_solution: 删除方案对象
    - save_solution: 保存方案对象
    
    :param llm_client: 大模型客户端
    :param storage_path: 方案存储路径
    :param logger: 日志记录器
    """
    
    # ========== 提示词模板 ==========
    
    UNDERSTANDING_SYSTEM_PROMPT = """你是一位专业的业务方案分析专家。你的任务是将非结构化的方案文档转化为结构化的方案对象。

请仔细分析文档内容，提取以下信息：
1. 方案基本信息：ID、名称、版本、状态、优先级
2. 方案目的：为什么要做这个方案
3. 方案目标：具体要达到什么目标（列表）
4. 方案举措：具体要采取哪些措施（列表）
5. 工作机制：如何组织和协调工作
6. 涉及组织：哪些部门或组织参与
7. 涉及人员：哪些角色或人员参与
8. 涉及角色：方案中定义的角色
9. 工作内容：具体的工作描述
10. 限制条件：有什么约束和限制
11. 风险：存在什么风险
12. 问题：当前存在的问题
13. 其他说明：其他重要信息

输出要求：
- 必须严格遵循JSON格式输出
- 所有字段都必须包含，如果没有相关内容则使用空字符串或空列表
- 状态必须是以下之一：draft, review, approved, active, suspended, completed, archived
- 优先级必须是以下之一：low, medium, high, critical
- 确保JSON格式正确，可以被Python的json.loads()解析
"""

    UNDERSTANDING_USER_PROMPT_TEMPLATE = """请分析以下方案文档，提取结构化信息：

【方案文档内容】
{document_text}

请输出以下JSON格式的结构化方案对象：
{{
    "solution_id": "方案唯一标识（从文档中推断或使用文档ID）",
    "name": "方案名称",
    "version": "版本号（默认1.0）",
    "status": "方案状态（draft/review/approved/active/suspended/completed/archived）",
    "priority": "优先级（low/medium/high/critical）",
    "purpose": "方案目的",
    "objectives": ["目标1", "目标2", ...],
    "initiatives": ["举措1", "举措2", ...],
    "working_mechanism": "工作机制描述",
    "organization": ["组织1", "组织2", ...],
    "personnel": ["人员1", "人员2", ...],
    "roles": ["角色1", "角色2", ...],
    "work_content": "工作内容描述",
    "constraints": ["限制1", "限制2", ...],
    "risks": ["风险1", "风险2", ...],
    "issues": ["问题1", "问题2", ...],
    "other_notes": "其他说明",
    "description": "方案描述"
}}

注意：
1. 如果文档中未明确提及某个字段，请根据上下文合理推断或留空
2. 目标和举措必须提炼为简洁的列表项
3. 确保输出的JSON格式完全正确
"""
    
    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        storage_path: str = "solutions",
        logger: Optional[logging.Logger] = None,
        client_type: Optional[str] = None
    ):
        """
        初始化方案理解服务
        
        :param llm_client: 大模型客户端（可选，默认通过工厂创建）
        :param storage_path: 方案存储路径
        :param logger: 日志记录器
        :param client_type: 客户端类型（可选，默认从配置读取）
        """
        if llm_client is None:
            self._llm_client = LLMClientFactory.create_client(client_type=client_type)
        else:
            self._llm_client = llm_client
        self._storage_path = storage_path
        self._solutions: Dict[str, Solution] = {}
        self._logger = logger or self._setup_logging()
        
        os.makedirs(self._storage_path, exist_ok=True)
        self._logger.info("方案理解服务已初始化")
    
    def _setup_logging(self) -> logging.Logger:
        """配置日志系统"""
        logger = logging.getLogger("SolutionUnderstandingService")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    # ========== 核心理解功能 ==========
    
    def understand_document(self, document: SolutionDocument) -> UnderstandingResult:
        """
        理解方案文档，提取结构化方案对象
        
        调用大模型分析文档内容，将非结构化文本转化为结构化的方案对象。
        
        :param document: 方案文档对象
        :return: 理解结果，包含结构化方案对象
        """
        import time
        start_time = time.time()
        
        self._logger.info(f"开始理解文档: {document.document_id}")
        
        # 获取文档文本内容
        document_text = document.text_content
        if not document_text:
            self._logger.error(f"文档 {document.document_id} 没有文本内容")
            return UnderstandingResult(
                success=False,
                error_message="文档没有文本内容，无法进行分析"
            )
        
        # 构建提示词
        prompt = self.UNDERSTANDING_USER_PROMPT_TEMPLATE.format(
            document_text=document_text[:8000]  # 限制文本长度，避免超出token限制
        )
        
        # 调用大模型
        try:
            request = LLMRequest(
                prompt=prompt,
                system_prompt=self.UNDERSTANDING_SYSTEM_PROMPT,
                temperature=0.3,  # 使用较低温度，保证输出稳定性
                max_tokens=4000
            )
            
            response = self._llm_client.call_with_retry(request, max_retries=3)
            
            # 解析响应
            solution = self._parse_solution_from_response(response.content, document.document_id)
            
            if solution:
                # 保存理解结果
                self._solutions[solution.solution_id] = solution
                
                processing_time = int((time.time() - start_time) * 1000)
                self._logger.info(f"文档理解完成: {document.document_id} -> {solution.solution_id}")
                
                return UnderstandingResult(
                    success=True,
                    solution=solution,
                    raw_response=response.content,
                    processing_time_ms=processing_time
                )
            else:
                return UnderstandingResult(
                    success=False,
                    raw_response=response.content,
                    error_message="无法从响应中解析出有效的方案对象"
                )
                
        except Exception as e:
            self._logger.error(f"文档理解失败: {e}")
            return UnderstandingResult(
                success=False,
                error_message=f"大模型调用失败: {str(e)}"
            )
    
    def _parse_solution_from_response(self, response_text: str, default_id: str) -> Optional[Solution]:
        """
        从大模型响应中解析方案对象
        
        :param response_text: 大模型响应文本
        :param default_id: 默认方案ID（如果响应中未包含）
        :return: 解析后的方案对象，如果失败返回None
        """
        try:
            # 尝试提取JSON内容
            # 大模型可能在JSON前后添加了说明文字
            json_str = self._extract_json_from_text(response_text)
            
            if not json_str:
                self._logger.error("无法从响应中提取JSON内容")
                return None
            
            data = json.loads(json_str)
            
            # 确保有solution_id
            if 'solution_id' not in data or not data['solution_id']:
                data['solution_id'] = f"SOL_{default_id}"
            
            # 创建方案对象
            solution = Solution(**data)
            return solution
            
        except json.JSONDecodeError as e:
            self._logger.error(f"JSON解析失败: {e}")
            return None
        except Exception as e:
            self._logger.error(f"解析方案对象失败: {e}")
            return None
    
    def _extract_json_from_text(self, text: str) -> Optional[str]:
        """
        从文本中提取JSON内容
        
        :param text: 可能包含JSON的文本
        :return: 提取的JSON字符串
        """
        # 尝试直接解析
        text = text.strip()
        
        # 如果文本以 ```json 开头，提取中间内容
        if text.startswith("```json"):
            start = text.find("```json") + 7
            end = text.find("```", start)
            if end > start:
                return text[start:end].strip()
        
        # 如果文本以 ``` 开头，提取中间内容
        if text.startswith("```"):
            start = text.find("```") + 3
            end = text.find("```", start)
            if end > start:
                return text[start:end].strip()
        
        # 尝试找到JSON对象的开始和结束
        start_idx = text.find('{')
        end_idx = text.rfind('}')
        
        if start_idx >= 0 and end_idx > start_idx:
            return text[start_idx:end_idx + 1]
        
        # 如果找不到JSON结构，尝试直接解析整个文本
        return text if text.startswith('{') else None
    
    # ========== 方案对象CRUD操作 ==========
    
    def create_solution(self, solution: Solution) -> Solution:
        """
        创建方案对象
        
        :param solution: 方案对象
        :return: 创建后的方案对象
        :raises ValueError: 如果方案ID已存在
        """
        if solution.solution_id in self._solutions:
            raise ValueError(f"方案ID {solution.solution_id} 已存在")
        
        self._solutions[solution.solution_id] = solution
        self._logger.info(f"创建方案: {solution.solution_id} - {solution.name}")
        return solution
    
    def get_solution(self, solution_id: str) -> Optional[Solution]:
        """
        根据ID获取方案对象
        
        :param solution_id: 方案ID
        :return: 方案对象，如果不存在返回None
        """
        solution = self._solutions.get(solution_id)
        if solution:
            self._logger.info(f"查询方案: {solution_id}")
        else:
            self._logger.warning(f"方案不存在: {solution_id}")
        return solution
    
    def list_solutions(
        self,
        status: Optional[SolutionStatus] = None,
        priority: Optional[SolutionPriority] = None,
        keyword: Optional[str] = None
    ) -> List[Solution]:
        """
        查询方案列表
        
        :param status: 状态过滤
        :param priority: 优先级过滤
        :param keyword: 关键词过滤（匹配名称、目的、描述）
        :return: 符合条件的方案列表
        """
        solutions = list(self._solutions.values())
        
        if status:
            solutions = [s for s in solutions if s.status == status]
        if priority:
            solutions = [s for s in solutions if s.priority == priority]
        if keyword:
            keyword = keyword.lower()
            solutions = [
                s for s in solutions
                if (s.name and keyword in s.name.lower()) or
                   (s.purpose and keyword in s.purpose.lower()) or
                   (s.description and keyword in s.description.lower())
            ]
        
        self._logger.info(f"查询到 {len(solutions)} 个方案")
        return solutions
    
    def get_all_solutions(self) -> List[Solution]:
        """
        获取所有方案对象
        
        :return: 所有方案列表
        """
        return list(self._solutions.values())
    
    def update_solution(self, solution_id: str, **kwargs) -> Solution:
        """
        更新方案对象属性
        
        :param solution_id: 方案ID
        :param kwargs: 要更新的属性
        :return: 更新后的方案对象
        :raises ValueError: 如果方案不存在
        """
        solution = self.get_solution(solution_id)
        if not solution:
            raise ValueError(f"方案不存在: {solution_id}")
        
        update_data = solution.model_dump()
        update_data.update(kwargs)
        update_data['updated_at'] = datetime.now()
        
        updated_solution = Solution(**update_data)
        self._solutions[solution_id] = updated_solution
        
        self._logger.info(f"更新方案: {solution_id}")
        return updated_solution
    
    def delete_solution(self, solution_id: str) -> bool:
        """
        删除方案对象
        
        :param solution_id: 方案ID
        :return: 如果删除成功返回True
        :raises ValueError: 如果方案不存在
        """
        if solution_id not in self._solutions:
            raise ValueError(f"方案不存在: {solution_id}")
        
        del self._solutions[solution_id]
        self._logger.info(f"删除方案: {solution_id}")
        return True
    
    # ========== 存储操作 ==========
    
    def save_solution(self, solution_id: str) -> str:
        """
        保存方案对象到存储介质
        
        :param solution_id: 方案ID
        :return: 保存的文件路径
        """
        solution = self.get_solution(solution_id)
        if not solution:
            raise ValueError(f"方案不存在: {solution_id}")
        
        file_path = os.path.join(self._storage_path, f"{solution_id}.json")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(solution.to_json())
        
        self._logger.info(f"保存方案: {solution_id} -> {file_path}")
        return file_path
    
    def save_all_solutions(self) -> List[str]:
        """
        保存所有方案
        
        :return: 保存的文件路径列表
        """
        saved_paths = []
        for solution_id in self._solutions:
            path = self.save_solution(solution_id)
            saved_paths.append(path)
        
        self._logger.info(f"保存了 {len(saved_paths)} 个方案")
        return saved_paths
    
    def load_solution(self, file_path: str) -> Solution:
        """
        从文件加载方案
        
        :param file_path: 文件路径
        :return: 加载的方案对象
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        solution = Solution(**data)
        self._solutions[solution.solution_id] = solution
        
        self._logger.info(f"加载方案: {solution.solution_id} <- {file_path}")
        return solution
    
    def load_all_solutions(self) -> int:
        """
        从存储目录加载所有方案
        
        :return: 加载的方案数量
        """
        count = 0
        for file_name in os.listdir(self._storage_path):
            if file_name.endswith('.json'):
                file_path = os.path.join(self._storage_path, file_name)
                try:
                    self.load_solution(file_path)
                    count += 1
                except Exception as e:
                    self._logger.error(f"加载方案失败: {file_path}, 错误: {e}")
        
        self._logger.info(f"从存储加载了 {count} 个方案")
        return count
    
    # ========== 统计操作 ==========
    
    def get_solution_count(self) -> int:
        """
        获取方案总数
        
        :return: 方案数量
        """
        return len(self._solutions)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取方案统计信息
        
        :return: 统计信息字典
        """
        solutions = self.get_all_solutions()
        
        status_counts = {}
        priority_counts = {}
        
        for solution in solutions:
            status_counts[solution.status.value] = status_counts.get(solution.status.value, 0) + 1
            priority_counts[solution.priority.value] = priority_counts.get(solution.priority.value, 0) + 1
        
        return {
            "total_count": len(solutions),
            "status_distribution": status_counts,
            "priority_distribution": priority_counts
        }