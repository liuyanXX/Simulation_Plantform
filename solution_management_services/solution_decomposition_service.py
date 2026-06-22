"""方案拆解服务子模块

负责把方案拆解到任务和任务图谱。

使用大模型进行方案到任务的智能拆解，并构建有向图结构的任务图谱。
"""
import os
import json
import logging
from datetime import datetime
from typing import Optional, Dict, List, Any, Tuple
from pydantic import BaseModel, Field

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/..')
from bo.solution import Solution
from bo.task import Task, TaskType, Priority
from bo.tasks_graph import TasksGraph
from bo.task_flow_group import TaskFlowGroup
from bo.task_manifest import TaskManifest
from ai_modules.basic.llm_client import LLMClient, LLMRequest, LLMClientFactory
from knowledge_management.knowledge_manager import KnowledgeManager
from knowledge_management.models import Knowledge


class DecompositionResult(BaseModel):
    """方案拆解结果"""
    success: bool = Field(description="是否成功")
    tasks_graph: Optional[TasksGraph] = Field(default=None, description="生成的任务图谱")
    tasks: List[Task] = Field(default_factory=list, description="生成的任务列表")
    flow_groups: List[TaskFlowGroup] = Field(default_factory=list, description="生成的任务流组列表")
    task_manifest: Optional[TaskManifest] = Field(default=None, description="生成的任务清单")
    raw_response: Optional[str] = Field(default=None, description="大模型原始响应")
    error_message: Optional[str] = Field(default=None, description="错误信息")
    processing_time_ms: Optional[int] = Field(default=None, description="处理时间（毫秒）")


class TaskTemplate(BaseModel):
    """任务模板，用于大模型输出"""
    task_id: str = Field(description="任务唯一标识")
    task_name: str = Field(description="任务名称")
    task_type: str = Field(description="任务类型: start/normal/end/halt")
    content: str = Field(description="工作内容")
    execute_role: str = Field(description="执行角色")
    resource_consumption: float = Field(description="资源消耗（工时）")
    priority: str = Field(description="优先级: high/medium/low")
    output_target_role: str = Field(description="输出目标角色")
    task_source: Optional[str] = Field(default=None, description="来源任务ID")
    task_destinations: List[str] = Field(default_factory=list, description="去向任务ID列表")


class SolutionDecompositionService:
    """
    方案拆解服务子模块
    
    通过调用外部大模型，将结构化的方案对象拆解为具体的任务列表和任务图谱。
    提供对任务和图谱的完整生命周期管理。
    
    核心功能：
    - decompose_solution: 将方案拆解为任务和任务图谱
    - create_task: 创建任务
    - get_task: 查询任务
    - update_task: 更新任务
    - delete_task: 删除任务
    - create_tasks_graph: 创建任务图谱
    - get_tasks_graph: 查询任务图谱
    - save_tasks_graph: 保存任务图谱
    
    :param llm_client: 大模型客户端
    :param storage_path: 存储路径
    :param logger: 日志记录器
    """
    
    # ========== 提示词模板 ==========
    
    DECOMPOSITION_SYSTEM_PROMPT = """你是一位专业的项目管理专家。你的任务是将业务方案拆解为具体的任务和任务流程。

请根据方案内容，拆解出完整的任务执行流程，遵循以下规则：

1. 任务类型：
   - start: 流程开始任务（必须有且仅有一个）
   - normal: 普通执行任务（可以有多个）
   - end: 流程结束任务（可以有多个，表示正常完成）
   - halt: 流程终止任务（可选，表示异常终止）

2. 任务依赖关系：
   - 使用 task_source 表示上一个任务ID
   - 使用 task_destinations 表示下一个任务ID列表（支持分支）
   - 确保任务ID的引用正确，形成完整的有向图

3. 任务属性：
   - execute_role: 执行任务的角色（如PM项目经理、DEV开发、TEST测试、OP运维等）
   - resource_consumption: 预估工时（浮点数，单位：人天）
   - priority: 优先级（high/medium/low）
   - output_target_role: 任务输出交付给哪个角色

4. 流程设计原则：
   - 从start任务开始，到end或halt任务结束
   - 支持并行任务（多个任务有相同的task_source）
   - 支持条件分支（一个任务有多个task_destinations）
   - 确保没有循环依赖

5. 角色建议：
   - SYSTEM: 系统自动化任务
   - PM: 项目经理
   - DEV: 开发人员
   - TEST: 测试人员
   - OP: 运维人员
   - BA: 业务分析师
   - ARCH: 架构师
   - UI: UI设计师
   - PO: 产品负责人

输出要求：
- 必须严格遵循JSON格式输出
- 所有任务必须有唯一的task_id
- 确保任务间的引用关系正确
- 输出可以被Python的json.loads()解析
"""

    DECOMPOSITION_USER_PROMPT_TEMPLATE = """请将以下业务方案拆解为具体的任务执行流程：

【方案信息】
方案ID: {solution_id}
方案名称: {name}
方案版本: {version}
方案目的: {purpose}
方案目标: {objectives}
方案举措: {initiatives}
工作机制: {working_mechanism}
涉及组织: {organization}
涉及人员: {personnel}
涉及角色: {roles}
工作内容: {work_content}
限制条件: {constraints}
风险: {risks}
问题: {issues}

请输出以下JSON格式的任务列表和任务图谱：
{{
    "graph_id": "基于方案ID的图谱ID",
    "graph_name": "图谱名称",
    "description": "图谱描述",
    "tasks": [
        {{
            "task_id": "TASK001",
            "task_name": "任务名称（人类可读）",
            "task_type": "start",
            "content": "任务具体工作内容描述",
            "execute_role": "执行角色（如PM/DEV/TEST/SYSTEM等）",
            "resource_consumption": 1.0,
            "priority": "high",
            "output_target_role": "输出目标角色",
            "task_source": null,
            "task_destinations": ["TASK002"]
        }},
        {{
            "task_id": "TASK002",
            "task_name": "任务名称",
            "task_type": "normal",
            "content": "任务具体工作内容",
            "execute_role": "DEV",
            "resource_consumption": 3.0,
            "priority": "high",
            "output_target_role": "TEST",
            "task_source": "TASK001",
            "task_destinations": ["TASK003"]
        }},
        {{
            "task_id": "TASK003",
            "task_name": "结束",
            "task_type": "end",
            "content": "流程结束",
            "execute_role": "SYSTEM",
            "resource_consumption": 0.0,
            "priority": "low",
            "output_target_role": "",
            "task_source": "TASK002",
            "task_destinations": []
        }}
    ]
}}

要求：
1. 必须包含且仅包含一个start任务和一个end任务
2. 任务数量建议5-20个，根据方案复杂度确定
3. 每个任务的resource_consumption必须大于0（start和end任务可以为0）
4. 任务间的task_source和task_destinations必须正确对应
5. 如果方案中有并行工作，使用多个任务指向同一个目的地或一个任务指向多个目的地来表示
6. 任务名称要简洁明了，体现具体工作内容
"""

    TASK_ENHANCEMENT_PROMPT_TEMPLATE = """请对以下任务进行优化和补充：

【方案信息】
方案名称: {name}
方案目标: {objectives}

【现有任务列表】
{tasks_json}

请优化以下内容：
1. 补充任务的详细描述，使工作内容更清晰
2. 检查并修正任务间的依赖关系
3. 评估并调整resource_consumption的合理性
4. 确保execute_role的分配合理
5. 补充可能遗漏的关键任务

输出完整的优化后的任务列表（JSON格式）。
"""
    
    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        storage_path: str = "tasks_graphs",
        logger: Optional[logging.Logger] = None,
        client_type: Optional[str] = None,
        knowledge_manager: Optional[KnowledgeManager] = None
    ):
        """
        初始化方案拆解服务
        
        :param llm_client: 大模型客户端（可选，默认通过工厂创建）
        :param storage_path: 存储路径
        :param logger: 日志记录器
        :param client_type: 客户端类型（可选，默认从配置读取）
        :param knowledge_manager: 知识管理器（可选，默认创建新实例）
        """
        if llm_client is None:
            self._llm_client = LLMClientFactory.create_client(client_type=client_type)
        else:
            self._llm_client = llm_client
        self._storage_path = storage_path
        self._tasks: Dict[str, Task] = {}
        self._tasks_graphs: Dict[str, TasksGraph] = {}
        self._logger = logger or self._setup_logging()
        self._knowledge_manager = knowledge_manager or KnowledgeManager()
        
        # 运行日志文件路径
        self._run_log_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "运行日志.log"
        )
        
        os.makedirs(self._storage_path, exist_ok=True)
        self._logger.info("方案拆解服务已初始化")
    
    def _setup_logging(self) -> logging.Logger:
        """配置日志系统"""
        logger = logging.getLogger("SolutionDecompositionService")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    # ========== 核心拆解功能 ==========
    
    def decompose_solution(self, solution: Solution) -> DecompositionResult:
        """
        将方案拆解为任务、任务流组、任务清单和任务图谱
        
        调用大模型分析方案内容，生成结构化的任务列表和任务图谱，
        并将提示词写入知识库，将原始方案内容和拆解结果写入运行日志。
        
        :param solution: 方案对象
        :return: 拆解结果，包含任务列表、任务图谱、任务流组和任务清单
        """
        import time
        start_time = time.time()
        
        self._logger.info(f"开始拆解方案: {solution.solution_id} - {solution.name}")
        
        # 构建提示词
        prompt = self._build_decomposition_prompt(solution)
        
        # 将提示词写入知识库
        self._save_prompt_to_knowledge(solution, prompt)
        
        # 记录原始方案内容到运行日志
        self._log_solution_content(solution)
        
        # 调用大模型
        try:
            request = LLMRequest(
                prompt=prompt,
                system_prompt=self.DECOMPOSITION_SYSTEM_PROMPT,
                temperature=0.5,
                max_tokens=6000
            )
            
            response = self._llm_client.call_with_retry(request, max_retries=3)
            
            # 解析响应
            tasks, tasks_graph = self._parse_decomposition_response(
                response.content,
                solution.solution_id
            )
            
            if tasks and tasks_graph:
                # 从任务图谱拆分任务流组
                flow_groups = tasks_graph.split_into_flow_groups()
                
                # 创建任务清单
                task_manifest = TaskManifest(
                    manifest_id=f"MANIFEST_{solution.solution_id}",
                    manifest_name=f"{solution.name}任务清单",
                    flow_groups=flow_groups,
                    description=f"方案【{solution.name}】的任务清单",
                    status=TaskManifest.ManifestStatus.DRAFT
                )
                task_manifest._solution_id = solution.solution_id
                
                # 保存结果
                for task in tasks:
                    self._tasks[task.task_id] = task
                self._tasks_graphs[tasks_graph.graph_id] = tasks_graph
                
                processing_time = int((time.time() - start_time) * 1000)
                self._logger.info(
                    f"方案拆解完成: {solution.solution_id} -> "
                    f"{len(tasks)}个任务, {len(flow_groups)}个任务流组, "
                    f"图谱ID: {tasks_graph.graph_id}, 清单ID: {task_manifest.manifest_id}"
                )
                
                # 记录拆解结果到运行日志
                self._log_decomposition_result(solution, tasks_graph, flow_groups, task_manifest, response.content)
                
                return DecompositionResult(
                    success=True,
                    tasks_graph=tasks_graph,
                    tasks=tasks,
                    flow_groups=flow_groups,
                    task_manifest=task_manifest,
                    raw_response=response.content,
                    processing_time_ms=processing_time
                )
            else:
                return DecompositionResult(
                    success=False,
                    raw_response=response.content,
                    error_message="无法从响应中解析出有效的任务和图谱"
                )
                
        except Exception as e:
            self._logger.error(f"方案拆解失败: {e}")
            return DecompositionResult(
                success=False,
                error_message=f"大模型调用失败: {str(e)}"
            )
    
    def _build_decomposition_prompt(self, solution: Solution) -> str:
        """
        构建拆解提示词
        
        :param solution: 方案对象
        :return: 完整的提示词
        """
        return self.DECOMPOSITION_USER_PROMPT_TEMPLATE.format(
            solution_id=solution.solution_id,
            name=solution.name,
            version=solution.version,
            purpose=solution.purpose or "未指定",
            objectives=solution.objectives or [],
            initiatives=solution.initiatives or [],
            working_mechanism=solution.working_mechanism or "未指定",
            organization=solution.organization or [],
            personnel=solution.personnel or [],
            roles=solution.roles or [],
            work_content=solution.work_content or "未指定",
            constraints=solution.constraints or [],
            risks=solution.risks or [],
            issues=solution.issues or []
        )
    
    def _parse_decomposition_response(
        self,
        response_text: str,
        solution_id: str
    ) -> Tuple[Optional[List[Task]], Optional[TasksGraph]]:
        """
        从响应中解析任务列表和任务图谱
        
        :param response_text: 响应文本
        :param solution_id: 方案ID
        :return: (任务列表, 任务图谱)
        """
        try:
            # 提取JSON
            json_str = self._extract_json_from_text(response_text)
            if not json_str:
                self._logger.error("无法从响应中提取JSON")
                return None, None
            
            data = json.loads(json_str)
            
            # 检查 tasks 字段
            if 'tasks' not in data:
                self._logger.error(f"响应中缺少 'tasks' 字段，可用键: {list(data.keys())}")
                return None, None
            if not data['tasks']:
                self._logger.error("'tasks' 字段为空列表")
                return None, None
            
            # 解析任务列表
            tasks = []
            for task_data in data.get('tasks', []):
                # 处理日期字段（设置默认值）
                now = datetime.now()
                task_data['expected_start_time'] = now
                task_data['expected_end_time'] = now
                
                # 确保task_type和priority是枚举类型
                if isinstance(task_data.get('task_type'), str):
                    task_data['task_type'] = TaskType(task_data['task_type'])
                if isinstance(task_data.get('priority'), str):
                    task_data['priority'] = Priority(task_data['priority'])
                
                task = Task(**task_data)
                tasks.append(task)
            
            # 构建任务图谱
            graph_id = data.get('graph_id', f"GRAPH_{solution_id}")
            graph_name = data.get('graph_name', f"{solution_id}任务图谱")
            description = data.get('description', '')
            
            tasks_graph = TasksGraph(
                graph_id=graph_id,
                graph_name=graph_name,
                tasks=tasks,
                description=description
            )
            
            return tasks, tasks_graph
            
        except Exception as e:
            self._logger.error(f"解析拆解响应失败: {e}")
            return None, None
    
    def _extract_json_from_text(self, text: str) -> Optional[str]:
        """
        从文本中提取JSON内容
        
        :param text: 可能包含JSON的文本
        :return: 提取的JSON字符串
        """
        text = text.strip()
        
        if text.startswith("```json"):
            start = text.find("```json") + 7
            end = text.find("```", start)
            if end > start:
                return text[start:end].strip()
        
        if text.startswith("```"):
            start = text.find("```") + 3
            end = text.find("```", start)
            if end > start:
                return text[start:end].strip()
        
        start_idx = text.find('{')
        end_idx = text.rfind('}')
        
        if start_idx >= 0 and end_idx > start_idx:
            return text[start_idx:end_idx + 1]
        
        return text if text.startswith('{') else None
    
    def enhance_tasks(self, tasks: List[Task], solution: Solution) -> DecompositionResult:
        """
        优化和增强任务列表
        
        调用大模型对已有的任务进行优化和补充。
        
        :param tasks: 现有任务列表
        :param solution: 方案对象
        :return: 优化后的结果
        """
        self._logger.info(f"开始优化任务列表: {len(tasks)}个任务")
        
        # 构建提示词
        tasks_json = json.dumps(
            [t.model_dump(mode='json') for t in tasks],
            ensure_ascii=False,
            indent=2
        )
        
        prompt = self.TASK_ENHANCEMENT_PROMPT_TEMPLATE.format(
            name=solution.name,
            objectives=solution.objectives or [],
            tasks_json=tasks_json
        )
        
        try:
            request = LLMRequest(
                prompt=prompt,
                system_prompt=self.DECOMPOSITION_SYSTEM_PROMPT,
                temperature=0.4,
                max_tokens=6000
            )
            
            response = self._llm_client.call_with_retry(request, max_retries=2)
            
            # 解析优化后的任务
            enhanced_tasks, tasks_graph = self._parse_decomposition_response(
                response.content,
                solution.solution_id
            )
            
            if enhanced_tasks and tasks_graph:
                # 更新存储
                for task in enhanced_tasks:
                    self._tasks[task.task_id] = task
                self._tasks_graphs[tasks_graph.graph_id] = tasks_graph
                
                self._logger.info(f"任务优化完成: {len(enhanced_tasks)}个任务")
                return DecompositionResult(
                    success=True,
                    tasks_graph=tasks_graph,
                    tasks=enhanced_tasks,
                    raw_response=response.content
                )
            else:
                return DecompositionResult(
                    success=False,
                    raw_response=response.content,
                    error_message="无法解析优化后的任务"
                )
                
        except Exception as e:
            self._logger.error(f"任务优化失败: {e}")
            return DecompositionResult(
                success=False,
                error_message=f"任务优化失败: {str(e)}"
            )
    
    # ========== 任务CRUD操作 ==========
    
    def create_task(self, task: Task) -> Task:
        """
        创建任务
        
        :param task: 任务对象
        :return: 创建后的任务
        :raises ValueError: 如果任务ID已存在
        """
        if task.task_id in self._tasks:
            raise ValueError(f"任务ID {task.task_id} 已存在")
        
        self._tasks[task.task_id] = task
        self._logger.info(f"创建任务: {task.task_id} - {task.task_name}")
        return task
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """
        获取任务
        
        :param task_id: 任务ID
        :return: 任务对象，如果不存在返回None
        """
        return self._tasks.get(task_id)
    
    def list_tasks(self, task_type: Optional[TaskType] = None) -> List[Task]:
        """
        查询任务列表
        
        :param task_type: 任务类型过滤
        :return: 任务列表
        """
        tasks = list(self._tasks.values())
        if task_type:
            tasks = [t for t in tasks if t.task_type == task_type]
        return tasks
    
    def update_task(self, task_id: str, **kwargs) -> Task:
        """
        更新任务
        
        :param task_id: 任务ID
        :param kwargs: 要更新的属性
        :return: 更新后的任务
        """
        task = self.get_task(task_id)
        if not task:
            raise ValueError(f"任务不存在: {task_id}")
        
        update_data = task.model_dump()
        update_data.update(kwargs)
        
        updated_task = Task(**update_data)
        self._tasks[task_id] = updated_task
        
        self._logger.info(f"更新任务: {task_id}")
        return updated_task
    
    def delete_task(self, task_id: str) -> bool:
        """
        删除任务
        
        :param task_id: 任务ID
        :return: 如果删除成功返回True
        """
        if task_id not in self._tasks:
            raise ValueError(f"任务不存在: {task_id}")
        
        del self._tasks[task_id]
        self._logger.info(f"删除任务: {task_id}")
        return True
    
    # ========== 任务图谱操作 ==========
    
    def create_tasks_graph(self, tasks_graph: TasksGraph) -> TasksGraph:
        """
        创建任务图谱
        
        :param tasks_graph: 任务图谱对象
        :return: 创建后的任务图谱
        """
        if tasks_graph.graph_id in self._tasks_graphs:
            raise ValueError(f"图谱ID {tasks_graph.graph_id} 已存在")
        
        self._tasks_graphs[tasks_graph.graph_id] = tasks_graph
        
        # 同时注册所有任务
        for task in tasks_graph.tasks:
            if task.task_id not in self._tasks:
                self._tasks[task.task_id] = task
        
        self._logger.info(f"创建任务图谱: {tasks_graph.graph_id}")
        return tasks_graph
    
    def get_tasks_graph(self, graph_id: str) -> Optional[TasksGraph]:
        """
        获取任务图谱
        
        :param graph_id: 图谱ID
        :return: 任务图谱对象，如果不存在返回None
        """
        return self._tasks_graphs.get(graph_id)
    
    def list_tasks_graphs(self) -> List[TasksGraph]:
        """
        获取所有任务图谱
        
        :return: 任务图谱列表
        """
        return list(self._tasks_graphs.values())
    
    def delete_tasks_graph(self, graph_id: str) -> bool:
        """
        删除任务图谱
        
        :param graph_id: 图谱ID
        :return: 如果删除成功返回True
        """
        if graph_id not in self._tasks_graphs:
            raise ValueError(f"图谱不存在: {graph_id}")
        
        del self._tasks_graphs[graph_id]
        self._logger.info(f"删除任务图谱: {graph_id}")
        return True
    
    # ========== 存储操作 ==========
    
    def save_tasks_graph(self, graph_id: str) -> str:
        """
        保存任务图谱
        
        :param graph_id: 图谱ID
        :return: 保存的文件路径
        """
        tasks_graph = self.get_tasks_graph(graph_id)
        if not tasks_graph:
            raise ValueError(f"图谱不存在: {graph_id}")
        
        file_path = os.path.join(self._storage_path, f"{graph_id}.json")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(tasks_graph.model_dump_json(indent=2))
        
        self._logger.info(f"保存任务图谱: {graph_id} -> {file_path}")
        return file_path
    
    def save_all_tasks_graphs(self) -> List[str]:
        """
        保存所有任务图谱
        
        :return: 保存的文件路径列表
        """
        saved_paths = []
        for graph_id in self._tasks_graphs:
            path = self.save_tasks_graph(graph_id)
            saved_paths.append(path)
        return saved_paths
    
    def load_tasks_graph(self, file_path: str) -> TasksGraph:
        """
        从文件加载任务图谱
        
        :param file_path: 文件路径
        :return: 加载的任务图谱
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 解析任务
        tasks = []
        for task_data in data.get('tasks', []):
            if isinstance(task_data.get('task_type'), str):
                task_data['task_type'] = TaskType(task_data['task_type'])
            if isinstance(task_data.get('priority'), str):
                task_data['priority'] = Priority(task_data['priority'])
            
            now = datetime.now()
            task_data.setdefault('expected_start_time', now.isoformat())
            task_data.setdefault('expected_end_time', now.isoformat())
            
            task = Task(**task_data)
            tasks.append(task)
        
        tasks_graph = TasksGraph(
            graph_id=data['graph_id'],
            graph_name=data.get('graph_name', data['graph_id']),
            tasks=tasks,
            description=data.get('description')
        )
        
        self._tasks_graphs[tasks_graph.graph_id] = tasks_graph
        for task in tasks:
            self._tasks[task.task_id] = task
        
        self._logger.info(f"加载任务图谱: {tasks_graph.graph_id} <- {file_path}")
        return tasks_graph
    
    # ========== 统计操作 ==========
    
    def get_task_count(self) -> int:
        """
        获取任务总数
        
        :return: 任务数量
        """
        return len(self._tasks)
    
    def get_tasks_graph_count(self) -> int:
        """
        获取图谱总数
        
        :return: 图谱数量
        """
        return len(self._tasks_graphs)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        :return: 统计信息字典
        """
        tasks = list(self._tasks.values())
        
        type_counts = {}
        priority_counts = {}
        role_counts = {}
        total_resource = 0.0
        
        for task in tasks:
            type_counts[task.task_type.value] = type_counts.get(task.task_type.value, 0) + 1
            priority_counts[task.priority.value] = priority_counts.get(task.priority.value, 0) + 1
            role_counts[task.execute_role] = role_counts.get(task.execute_role, 0) + 1
            total_resource += task.resource_consumption
        
        return {
            "total_tasks": len(tasks),
            "total_graphs": len(self._tasks_graphs),
            "task_type_distribution": type_counts,
            "priority_distribution": priority_counts,
            "role_distribution": role_counts,
            "total_resource_consumption": round(total_resource, 2)
        }
    
    # ========== 知识管理和日志记录 ==========
    
    def _save_prompt_to_knowledge(self, solution: Solution, prompt: str) -> None:
        """
        将提示词写入知识库
        
        :param solution: 方案对象
        :param prompt: 提示词内容
        """
        try:
            knowledge_id = f"KNOW_DECOMP_{solution.solution_id}"
            
            # 检查知识是否已存在
            existing_knowledge = self._knowledge_manager.get_knowledge(knowledge_id)
            
            knowledge = Knowledge(
                knowledge_id=knowledge_id,
                title=f"方案拆解提示词 - {solution.name}",
                summary=f"用于拆解方案【{solution.name}】的大模型提示词",
                content=f"""方案拆解提示词

【方案信息】
方案ID: {solution.solution_id}
方案名称: {solution.name}
方案版本: {solution.version}

【系统提示词】
{self.DECOMPOSITION_SYSTEM_PROMPT}

【用户提示词】
{prompt}

【生成时间】
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
""",
                tags=["方案拆解", "提示词", solution.solution_id],
                category="decomposition"
            )
            
            if existing_knowledge:
                self._knowledge_manager.update_knowledge(knowledge)
                self._logger.info(f"更新知识库中的提示词: {knowledge_id}")
            else:
                self._knowledge_manager.add_knowledge(knowledge)
                self._logger.info(f"将提示词写入知识库: {knowledge_id}")
                
        except Exception as e:
            self._logger.error(f"写入知识库失败: {e}")
    
    def _log_solution_content(self, solution: Solution) -> None:
        """
        记录原始方案内容到运行日志
        
        :param solution: 方案对象
        """
        try:
            log_content = f"""
================================================================================
方案拆解 - 原始方案内容
================================================================================
时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
方案ID: {solution.solution_id}
方案名称: {solution.name}
方案版本: {solution.version}

【方案基本信息】
方案目的: {solution.purpose or '未指定'}
方案目标: {', '.join(solution.objectives) if solution.objectives else '未指定'}
方案举措: {', '.join(solution.initiatives) if solution.initiatives else '未指定'}
工作机制: {solution.working_mechanism or '未指定'}

【组织与人员】
涉及组织: {', '.join(solution.organization) if solution.organization else '未指定'}
涉及人员: {', '.join(solution.personnel) if solution.personnel else '未指定'}
涉及角色: {', '.join(solution.roles) if solution.roles else '未指定'}

【工作内容】
{solution.work_content or '未指定'}

【限制条件】
{', '.join(solution.constraints) if solution.constraints else '无'}

【风险与问题】
风险: {', '.join(solution.risks) if solution.risks else '无'}
问题: {', '.join(solution.issues) if solution.issues else '无'}

================================================================================
"""
            
            with open(self._run_log_path, 'a', encoding='utf-8') as f:
                f.write(log_content)
                
            self._logger.info(f"原始方案内容已记录到运行日志")
            
        except Exception as e:
            self._logger.error(f"记录方案内容失败: {e}")
    
    def _log_decomposition_result(
        self,
        solution: Solution,
        tasks_graph: TasksGraph,
        flow_groups: List[TaskFlowGroup],
        task_manifest: TaskManifest,
        raw_response: str
    ) -> None:
        """
        记录拆解结果到运行日志
        
        :param solution: 方案对象
        :param tasks_graph: 任务图谱
        :param flow_groups: 任务流组列表
        :param task_manifest: 任务清单
        :param raw_response: 大模型原始响应
        """
        try:
            log_content = f"""
================================================================================
方案拆解 - 拆解结果
================================================================================
时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
方案ID: {solution.solution_id}
方案名称: {solution.name}

【任务图谱信息】
图谱ID: {tasks_graph.graph_id}
图谱名称: {tasks_graph.graph_name}
图谱描述: {tasks_graph.description or '无'}
任务总数: {len(tasks_graph.tasks)}

【任务流组信息】
任务流组数量: {len(flow_groups)}
任务清单ID: {task_manifest.manifest_id}
任务清单名称: {task_manifest.manifest_name}
任务清单状态: {task_manifest.status.value}

【任务流组详情】
"""
            
            for i, flow_group in enumerate(flow_groups, 1):
                log_content += f"""
任务流组 {i}:
  流组ID: {flow_group.flow_id}
  流组名称: {flow_group.flow_name}
  流组描述: {flow_group.description or '无'}
  任务数量: {len(flow_group.tasks)}
  任务列表: {' -> '.join([t.task_id for t in flow_group.tasks])}
"""
            
            log_content += f"""
【大模型原始响应】
{raw_response}

================================================================================
"""
            
            with open(self._run_log_path, 'a', encoding='utf-8') as f:
                f.write(log_content)
                
            self._logger.info(f"拆解结果已记录到运行日志")
            
        except Exception as e:
            self._logger.error(f"记录拆解结果失败: {e}")
    
    # ========== 持久化服务 ==========
    
    def _get_task_service(self):
        """获取任务服务实例"""
        from data_storage_services.sql_db_services.task_service import TaskService
        return TaskService()
    
    def _get_flow_group_service(self):
        """获取任务流组服务实例"""
        from data_storage_services.sql_db_services.task_flow_group_service import TaskFlowGroupService
        return TaskFlowGroupService()
    
    def _get_task_manifest_service(self):
        """获取任务清单服务实例"""
        from data_storage_services.sql_db_services.task_manifest_service import TaskManifestService
        return TaskManifestService()
    
    def _get_tasks_graph_service(self):
        """获取任务图谱服务实例"""
        from data_storage_services.sql_db_services.tasks_graph_service import TasksGraphService
        return TasksGraphService()
    
    # --- 任务持久化服务 ---
    
    def save_task(self, task: Task) -> bool:
        """
        保存任务到数据库（新增或更新）
        
        :param task: 任务对象
        :return: 保存成功返回True
        """
        try:
            service = self._get_task_service()
            try:
                if service.exists(task.task_id):
                    service.update(task)
                    self._logger.info(f"更新任务: {task.task_id}")
                else:
                    service.create(task)
                    self._logger.info(f"保存任务: {task.task_id}")
                return True
            finally:
                service.disconnect()
        except Exception as e:
            self._logger.error(f"保存任务失败: {e}")
            return False
    
    def save_all_tasks(self) -> int:
        """
        保存所有任务到数据库
        
        :return: 保存的任务数量
        """
        count = 0
        for task in self._tasks.values():
            if self.save_task(task):
                count += 1
        self._logger.info(f"保存所有任务完成: {count}/{len(self._tasks)}")
        return count
    
    def get_task_from_db(self, task_id: str) -> Optional[Task]:
        """
        从数据库获取任务
        
        :param task_id: 任务ID
        :return: 任务对象，如果不存在返回None
        """
        try:
            service = self._get_task_service()
            try:
                task = service.read(task_id)
                if task:
                    self._tasks[task.task_id] = task
                return task
            finally:
                service.disconnect()
        except Exception as e:
            self._logger.error(f"获取任务失败: {e}")
            return None
    
    def delete_task_from_db(self, task_id: str) -> bool:
        """
        从数据库删除任务
        
        :param task_id: 任务ID
        :return: 删除成功返回True
        """
        try:
            service = self._get_task_service()
            try:
                result = service.delete(task_id)
                if task_id in self._tasks:
                    del self._tasks[task_id]
                self._logger.info(f"删除任务: {task_id}")
                return result
            finally:
                service.disconnect()
        except Exception as e:
            self._logger.error(f"删除任务失败: {e}")
            return False
    
    # --- 任务流组持久化服务 ---
    
    def save_flow_group(self, flow_group: TaskFlowGroup, manifest_id: str = None) -> bool:
        """
        保存任务流组到数据库（新增或更新）
        
        :param flow_group: 任务流组对象
        :param manifest_id: 任务清单ID
        :return: 保存成功返回True
        """
        try:
            service = self._get_flow_group_service()
            try:
                flow_group._manifest_id = manifest_id
                if service.exists(flow_group.flow_id):
                    service.update(flow_group)
                    self._logger.info(f"更新任务流组: {flow_group.flow_id}")
                else:
                    service.create_with_tasks(flow_group, manifest_id)
                    self._logger.info(f"保存任务流组: {flow_group.flow_id}")
                return True
            finally:
                service.disconnect()
        except Exception as e:
            self._logger.error(f"保存任务流组失败: {e}")
            return False
    
    def get_flow_group_from_db(self, flow_id: str) -> Optional[TaskFlowGroup]:
        """
        从数据库获取任务流组（包含任务列表）
        
        :param flow_id: 任务流组ID
        :return: 任务流组对象，如果不存在返回None
        """
        try:
            service = self._get_flow_group_service()
            try:
                flow_group = service.read_with_tasks(flow_id)
                return flow_group
            finally:
                service.disconnect()
        except Exception as e:
            self._logger.error(f"获取任务流组失败: {e}")
            return None
    
    def delete_flow_group_from_db(self, flow_id: str) -> int:
        """
        从数据库删除任务流组及其所有任务
        
        :param flow_id: 任务流组ID
        :return: 删除的任务数量
        """
        try:
            service = self._get_flow_group_service()
            try:
                result = service.delete_with_tasks(flow_id)
                self._logger.info(f"删除任务流组: {flow_id}")
                return result
            finally:
                service.disconnect()
        except Exception as e:
            self._logger.error(f"删除任务流组失败: {e}")
            return 0
    
    def list_flow_groups_from_db(self) -> List[TaskFlowGroup]:
        """
        从数据库获取所有任务流组
        
        :return: 任务流组列表
        """
        try:
            service = self._get_flow_group_service()
            try:
                return service.read_all()
            finally:
                service.disconnect()
        except Exception as e:
            self._logger.error(f"获取任务流组列表失败: {e}")
            return []
    
    # --- 任务清单持久化服务 ---
    
    def save_task_manifest(self, manifest: TaskManifest, solution_id: str = None) -> bool:
        """
        保存任务清单到数据库（新增或更新）
        
        :param manifest: 任务清单对象
        :param solution_id: 方案ID
        :return: 保存成功返回True
        """
        try:
            service = self._get_task_manifest_service()
            try:
                manifest._solution_id = solution_id
                if service.exists(manifest.manifest_id):
                    service.update(manifest)
                    self._logger.info(f"更新任务清单: {manifest.manifest_id}")
                else:
                    service.create_with_flow_groups(manifest, solution_id)
                    self._logger.info(f"保存任务清单: {manifest.manifest_id}")
                return True
            finally:
                service.disconnect()
        except Exception as e:
            self._logger.error(f"保存任务清单失败: {e}")
            return False
    
    def get_task_manifest_from_db(self, manifest_id: str) -> Optional[TaskManifest]:
        """
        从数据库获取任务清单（包含任务流组和任务列表）
        
        :param manifest_id: 任务清单ID
        :return: 任务清单对象，如果不存在返回None
        """
        try:
            service = self._get_task_manifest_service()
            try:
                return service.read_with_flow_groups(manifest_id)
            finally:
                service.disconnect()
        except Exception as e:
            self._logger.error(f"获取任务清单失败: {e}")
            return None
    
    def delete_task_manifest_from_db(self, manifest_id: str) -> int:
        """
        从数据库删除任务清单及其所有任务流组和任务
        
        :param manifest_id: 任务清单ID
        :return: 删除的任务流组数量
        """
        try:
            service = self._get_task_manifest_service()
            try:
                result = service.delete_with_flow_groups(manifest_id)
                self._logger.info(f"删除任务清单: {manifest_id}")
                return result
            finally:
                service.disconnect()
        except Exception as e:
            self._logger.error(f"删除任务清单失败: {e}")
            return 0
    
    def list_task_manifests_from_db(self) -> List[TaskManifest]:
        """
        从数据库获取所有任务清单
        
        :return: 任务清单列表
        """
        try:
            service = self._get_task_manifest_service()
            try:
                return service.read_all()
            finally:
                service.disconnect()
        except Exception as e:
            self._logger.error(f"获取任务清单列表失败: {e}")
            return []
    
    # --- 任务图谱持久化服务 ---
    
    def save_tasks_graph_to_db(self, graph: TasksGraph, manifest_id: str = None) -> bool:
        """
        保存任务图谱到数据库（新增或更新）
        
        :param graph: 任务图谱对象
        :param manifest_id: 任务清单ID
        :return: 保存成功返回True
        """
        try:
            service = self._get_tasks_graph_service()
            try:
                graph._manifest_id = manifest_id
                if service.exists(graph.graph_id):
                    service.update(graph)
                    self._logger.info(f"更新任务图谱: {graph.graph_id}")
                else:
                    service.create_with_tasks(graph, manifest_id)
                    self._logger.info(f"保存任务图谱: {graph.graph_id}")
                return True
            finally:
                service.disconnect()
        except Exception as e:
            self._logger.error(f"保存任务图谱失败: {e}")
            return False
    
    def get_tasks_graph_from_db(self, graph_id: str) -> Optional[TasksGraph]:
        """
        从数据库获取任务图谱（包含任务列表）
        
        :param graph_id: 任务图谱ID
        :return: 任务图谱对象，如果不存在返回None
        """
        try:
            service = self._get_tasks_graph_service()
            try:
                graph = service.read_with_tasks(graph_id)
                if graph:
                    self._tasks_graphs[graph.graph_id] = graph
                    for task in graph.tasks:
                        self._tasks[task.task_id] = task
                return graph
            finally:
                service.disconnect()
        except Exception as e:
            self._logger.error(f"获取任务图谱失败: {e}")
            return None
    
    def delete_tasks_graph_from_db(self, graph_id: str) -> int:
        """
        从数据库删除任务图谱及其所有任务
        
        :param graph_id: 任务图谱ID
        :return: 删除的任务数量
        """
        try:
            service = self._get_tasks_graph_service()
            try:
                result = service.delete_with_tasks(graph_id)
                if graph_id in self._tasks_graphs:
                    del self._tasks_graphs[graph_id]
                self._logger.info(f"删除任务图谱: {graph_id}")
                return result
            finally:
                service.disconnect()
        except Exception as e:
            self._logger.error(f"删除任务图谱失败: {e}")
            return 0
    
    def list_tasks_graphs_from_db(self) -> List[TasksGraph]:
        """
        从数据库获取所有任务图谱
        
        :return: 任务图谱列表
        """
        try:
            service = self._get_tasks_graph_service()
            try:
                return service.read_all()
            finally:
                service.disconnect()
        except Exception as e:
            self._logger.error(f"获取任务图谱列表失败: {e}")
            return []
    
    # --- 批量操作服务 ---
    
    def save_decomposition_result(self, result: DecompositionResult) -> bool:
        """
        保存方案拆解结果到数据库
        
        将任务图谱、任务流组、任务清单和所有任务保存到数据库。
        
        :param result: 方案拆解结果
        :return: 保存成功返回True
        """
        if not result.success:
            self._logger.warning("拆解结果不成功，跳过保存")
            return False
        
        try:
            success = True
            
            # 1. 保存任务清单（会级联保存任务流组和任务）
            if result.task_manifest:
                manifest_id = getattr(result.task_manifest, '_solution_id', None)
                if not self.save_task_manifest(result.task_manifest, manifest_id):
                    success = False
                    self._logger.error("保存任务清单失败")
            
            # 2. 保存任务图谱（会级联保存任务）
            if result.tasks_graph:
                if not self.save_tasks_graph_to_db(result.tasks_graph):
                    success = False
                    self._logger.error("保存任务图谱失败")
            
            # 3. 直接保存所有任务（以防遗漏）
            for task in result.tasks:
                if task.task_id not in self._tasks:
                    if not self.save_task(task):
                        self._logger.warning(f"保存任务失败: {task.task_id}")
            
            if success:
                self._logger.info(f"方案拆解结果保存成功")
            return success
            
        except Exception as e:
            self._logger.error(f"保存方案拆解结果失败: {e}")
            return False
    
    def load_decomposition_from_db(self, manifest_id: str = None, graph_id: str = None) -> Optional[DecompositionResult]:
        """
        从数据库加载方案拆解结果
        
        :param manifest_id: 任务清单ID（优先）
        :param graph_id: 任务图谱ID（当manifest_id为None时使用）
        :return: 方案拆解结果，如果不不存在返回None
        """
        try:
            result = DecompositionResult(success=False)
            
            if manifest_id:
                # 从任务清单加载
                manifest = self.get_task_manifest_from_db(manifest_id)
                if manifest:
                    result.success = True
                    result.task_manifest = manifest
                    result.flow_groups = manifest.flow_groups
                    result.tasks = manifest.get_all_tasks()
                    
                    # 获取第一个图谱作为代表（如果有）
                    if manifest.flow_groups:
                        graph_id = f"GRAPH_{manifest_id}"
                        graph = self.get_tasks_graph_from_db(graph_id)
                        if graph:
                            result.tasks_graph = graph
                    
                    self._logger.info(f"从数据库加载任务清单: {manifest_id}")
                    return result
            
            if graph_id:
                # 从任务图谱加载
                graph = self.get_tasks_graph_from_db(graph_id)
                if graph:
                    result.success = True
                    result.tasks_graph = graph
                    result.tasks = graph.tasks
                    result.flow_groups = graph.split_into_flow_groups()
                    
                    # 创建任务清单
                    manifest_id = f"MANIFEST_{graph_id.replace('GRAPH_', '')}"
                    manifest = self.get_task_manifest_from_db(manifest_id)
                    if manifest:
                        result.task_manifest = manifest
                    
                    self._logger.info(f"从数据库加载任务图谱: {graph_id}")
                    return result
            
            self._logger.warning(f"未找到指定的清单或图谱: manifest_id={manifest_id}, graph_id={graph_id}")
            return result
            
        except Exception as e:
            self._logger.error(f"从数据库加载方案拆解结果失败: {e}")
            return None