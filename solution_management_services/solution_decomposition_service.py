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
from solution_management_services.llm_client import LLMClient, LLMRequest, MockLLMClient


class DecompositionResult(BaseModel):
    """方案拆解结果"""
    success: bool = Field(description="是否成功")
    tasks_graph: Optional[TasksGraph] = Field(default=None, description="生成的任务图谱")
    tasks: List[Task] = Field(default_factory=list, description="生成的任务列表")
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
        logger: Optional[logging.Logger] = None
    ):
        self._llm_client = llm_client or MockLLMClient()
        self._storage_path = storage_path
        self._tasks: Dict[str, Task] = {}
        self._tasks_graphs: Dict[str, TasksGraph] = {}
        self._logger = logger or self._setup_logging()
        
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
        将方案拆解为任务和任务图谱
        
        调用大模型分析方案内容，生成结构化的任务列表和任务图谱。
        
        :param solution: 方案对象
        :return: 拆解结果，包含任务列表和任务图谱
        """
        import time
        start_time = time.time()
        
        self._logger.info(f"开始拆解方案: {solution.solution_id} - {solution.name}")
        
        # 构建提示词
        prompt = self._build_decomposition_prompt(solution)
        
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
                # 保存结果
                for task in tasks:
                    self._tasks[task.task_id] = task
                self._tasks_graphs[tasks_graph.graph_id] = tasks_graph
                
                processing_time = int((time.time() - start_time) * 1000)
                self._logger.info(
                    f"方案拆解完成: {solution.solution_id} -> "
                    f"{len(tasks)}个任务, 图谱ID: {tasks_graph.graph_id}"
                )
                
                return DecompositionResult(
                    success=True,
                    tasks_graph=tasks_graph,
                    tasks=tasks,
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