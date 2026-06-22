"""方案管理服务主模块

整合三个子模块：
- SolutionManagementService: 方案管理服务（文档CRUD）
- SolutionUnderstandingService: 方案理解服务（文档→结构化方案）
- SolutionDecompositionService: 方案拆解服务（方案→任务图谱）

提供统一的方案全生命周期管理入口。
"""
import os
import logging
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(MODULE_DIR)

from .solution_management_service import SolutionManagementService
from .solution_understanding_service import SolutionUnderstandingService
from .solution_decomposition_service import SolutionDecompositionService
from ai_modules.basic.llm_client import LLMClient, LLMClientFactory

import sys
sys.path.append(PROJECT_ROOT)
from bo.solution import Solution, SolutionDocument
from bo.task import Task
from bo.tasks_graph import TasksGraph


class SolutionProcessResult(BaseModel):
    """方案处理全流程结果"""
    success: bool = Field(default=False, description="是否成功")
    document_id: Optional[str] = Field(default=None, description="文档ID")
    solution_id: Optional[str] = Field(default=None, description="方案ID")
    tasks_graph_id: Optional[str] = Field(default=None, description="任务图谱ID")
    task_count: int = Field(default=0, description="任务数量")
    message: str = Field(default="", description="处理结果消息")
    errors: List[str] = Field(default_factory=list, description="错误信息列表")


class SolutionManagementModule:
    """
    方案管理服务主模块
    
    作为方案管理的统一入口，协调三个子模块完成方案的完整处理流程：
    
    1. 文档管理阶段（SolutionManagementService）
       - 导入原始方案文档
       - 管理文档版本
       - 转换文档为纯文本
    
    2. 方案理解阶段（SolutionUnderstandingService）
       - 调用大模型分析文档文本
       - 提取结构化方案对象
       - 管理方案对象
    
    3. 方案拆解阶段（SolutionDecompositionService）
       - 调用大模型将方案拆解为任务
       - 构建任务图谱
       - 管理任务和图谱
    
    :param llm_client: 大模型客户端（会被三个子模块共享）
    :param storage_base_path: 基础存储路径
    :param logger: 日志记录器
    
    示例用法：
        module = SolutionManagementModule()
        
        # 完整流程：文档 -> 方案 -> 任务图谱
        result = module.process_document_full("DOC001")
        
        # 分步执行
        module.import_document("path/to/doc.docx", "DOC001")
        module.understand_document("DOC001")
        module.decompose_solution("SOL_DOC001")
    """
    
    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        storage_base_path: str = os.path.join(PROJECT_ROOT, "data"),
        logger: Optional[logging.Logger] = None,
        client_type: Optional[str] = None
    ):
        """
        初始化方案管理服务主模块
        
        :param llm_client: 大模型客户端（可选，默认通过工厂创建）
        :param storage_base_path: 基础存储路径
        :param logger: 日志记录器
        :param client_type: 客户端类型（可选，默认从配置读取）
        """
        self._logger = logger or self._setup_logging()
        
        if llm_client is None:
            self._llm_client = LLMClientFactory.create_client(client_type=client_type)
        else:
            self._llm_client = llm_client
        
        # 初始化三个子模块
        self._doc_service = SolutionManagementService(
            storage_path=os.path.join(storage_base_path, "documents"),
            logger=self._logger
        )
        self._understanding_service = SolutionUnderstandingService(
            llm_client=self._llm_client,
            storage_path=os.path.join(storage_base_path, "solutions"),
            logger=self._logger
        )
        self._decomposition_service = SolutionDecompositionService(
            llm_client=self._llm_client,
            storage_path=os.path.join(storage_base_path, "tasks_graphs"),
            logger=self._logger
        )
        
        self._logger.info("方案管理服务主模块已初始化")
    
    def _setup_logging(self) -> logging.Logger:
        """配置日志系统"""
        logger = logging.getLogger("SolutionManagementModule")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    # ========== 子模块访问器 ==========
    
    @property
    def document_service(self) -> SolutionManagementService:
        """获取方案文档管理子模块"""
        return self._doc_service
    
    @property
    def understanding_service(self) -> SolutionUnderstandingService:
        """获取方案理解子模块"""
        return self._understanding_service
    
    @property
    def decomposition_service(self) -> SolutionDecompositionService:
        """获取方案拆解子模块"""
        return self._decomposition_service
    
    # ========== 全流程处理 ==========
    
    def process_document_full(self, document_id: str) -> SolutionProcessResult:
        """
        完整处理流程：文档 -> 方案 -> 任务图谱
        
        依次执行文档理解、方案拆解的完整流程。
        
        :param document_id: 文档ID
        :return: 处理结果
        """
        result = SolutionProcessResult(document_id=document_id)
        
        self._logger.info(f"开始完整处理流程: {document_id}")
        
        # 步骤1: 验证文档存在
        document = self._doc_service.get_document(document_id)
        if not document:
            result.errors.append(f"文档不存在: {document_id}")
            result.message = "文档不存在，无法处理"
            return result
        
        # 步骤2: 文档理解 -> 方案对象
        understanding_result = self._understanding_service.understand_document(document)
        if not understanding_result.success:
            result.errors.append(f"文档理解失败: {understanding_result.error_message}")
            result.message = "文档理解失败"
            return result
        
        solution = understanding_result.solution
        result.solution_id = solution.solution_id
        
        self._logger.info(f"文档理解完成: {document_id} -> {solution.solution_id}")
        
        # 步骤3: 方案拆解 -> 任务图谱
        decomposition_result = self._decomposition_service.decompose_solution(solution)
        if not decomposition_result.success:
            result.errors.append(f"方案拆解失败: {decomposition_result.error_message}")
            result.message = "方案拆解失败"
            return result
        
        tasks_graph = decomposition_result.tasks_graph
        result.tasks_graph_id = tasks_graph.graph_id
        result.task_count = len(decomposition_result.tasks)
        
        result.success = True
        result.message = (
            f"处理完成: 文档({document_id}) -> "
            f"方案({solution.solution_id}) -> "
            f"任务图谱({tasks_graph.graph_id}, {result.task_count}个任务)"
        )
        
        self._logger.info(result.message)
        return result
    
    def process_document_to_solution(self, document_id: str) -> Optional[Solution]:
        """
        处理流程：文档 -> 方案
        
        :param document_id: 文档ID
        :return: 生成的方案对象，如果失败返回None
        """
        document = self._doc_service.get_document(document_id)
        if not document:
            self._logger.error(f"文档不存在: {document_id}")
            return None
        
        result = self._understanding_service.understand_document(document)
        if result.success:
            return result.solution
        else:
            self._logger.error(f"文档理解失败: {result.error_message}")
            return None
    
    def process_solution_to_tasks(self, solution_id: str) -> Optional[TasksGraph]:
        """
        处理流程：方案 -> 任务图谱
        
        :param solution_id: 方案ID
        :return: 生成的任务图谱，如果失败返回None
        """
        solution = self._understanding_service.get_solution(solution_id)
        if not solution:
            self._logger.error(f"方案不存在: {solution_id}")
            return None
        
        result = self._decomposition_service.decompose_solution(solution)
        if result.success:
            return result.tasks_graph
        else:
            self._logger.error(f"方案拆解失败: {result.error_message}")
            return None
    
    # ========== 便捷方法 ==========
    
    def import_document(
        self,
        file_path: str,
        document_id: str,
        version: str = "1.0",
        description: Optional[str] = None
    ) -> SolutionDocument:
        """
        导入方案文档
        
        :param file_path: 文件路径
        :param document_id: 文档ID
        :param version: 版本号
        :param description: 描述
        :return: 创建的文档对象
        """
        return self._doc_service.create_document_from_file(
            document_id=document_id,
            file_path=file_path,
            version=version,
            description=description
        )
    
    def create_document_from_text(
        self,
        document_id: str,
        text_content: str,
        file_name: str = "document.txt",
        version: str = "1.0"
    ) -> SolutionDocument:
        """
        从文本内容创建文档
        
        :param document_id: 文档ID
        :param text_content: 文本内容
        :param file_name: 文件名
        :param version: 版本号
        :return: 创建的文档对象
        """
        document = SolutionDocument(
            document_id=document_id,
            file_name=file_name,
            version=version,
            text_content=text_content
        )
        return self._doc_service.create_document(document)
    
    def understand_document(self, document_id: str) -> Optional[Solution]:
        """
        理解文档（便捷方法）
        
        :param document_id: 文档ID
        :return: 生成的方案对象
        """
        return self.process_document_to_solution(document_id)
    
    def decompose_solution(self, solution_id: str) -> Optional[TasksGraph]:
        """
        拆解方案（便捷方法）
        
        :param solution_id: 方案ID
        :return: 生成的任务图谱
        """
        return self.process_solution_to_tasks(solution_id)
    
    # ========== 查询方法 ==========
    
    def get_document(self, document_id: str) -> Optional[SolutionDocument]:
        """获取文档"""
        return self._doc_service.get_document(document_id)
    
    def get_solution(self, solution_id: str) -> Optional[Solution]:
        """获取方案"""
        return self._understanding_service.get_solution(solution_id)
    
    def get_tasks_graph(self, graph_id: str) -> Optional[TasksGraph]:
        """获取任务图谱"""
        return self._decomposition_service.get_tasks_graph(graph_id)
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务"""
        return self._decomposition_service.get_task(task_id)
    
    # ========== 保存方法 ==========
    
    def save_all(self) -> Dict[str, List[str]]:
        """
        保存所有数据
        
        :return: 保存的文件路径字典
        """
        return {
            "documents": self._doc_service.save_all_documents(),
            "solutions": self._understanding_service.save_all_solutions(),
            "tasks_graphs": self._decomposition_service.save_all_tasks_graphs()
        }
    
    # ========== 统计方法 ==========
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取全模块统计信息
        
        :return: 统计信息字典
        """
        return {
            "documents": self._doc_service.get_statistics(),
            "solutions": self._understanding_service.get_statistics(),
            "tasks_and_graphs": self._decomposition_service.get_statistics()
        }