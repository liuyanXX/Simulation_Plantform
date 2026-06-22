"""用户交互模块 - 数据模型

定义用于前后端数据交换的Pydantic模型。
遵循面向对象设计原则和微服务设计原则。
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class SolutionStatus(str, Enum):
    """方案状态枚举"""
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class SolutionPriority(str, Enum):
    """方案优先级枚举"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EvaluationStatus(str, Enum):
    """评估状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ABORTED = "aborted"


class SimulationStatus(str, Enum):
    """仿真状态枚举"""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"


class SolutionInput(BaseModel):
    """方案录入输入模型"""
    solution_id: str = Field(..., description="方案唯一标识")
    name: str = Field(..., description="方案名称")
    version: str = Field(default="1.0", description="版本号")
    priority: SolutionPriority = Field(default=SolutionPriority.MEDIUM, description="方案优先级")
    purpose: Optional[str] = Field(default=None, description="方案目的")
    objectives: List[str] = Field(default_factory=list, description="方案目标列表")
    initiatives: List[str] = Field(default_factory=list, description="方案举措列表")
    working_mechanism: Optional[str] = Field(default=None, description="工作机制描述")
    organization: List[str] = Field(default_factory=list, description="涉及组织")
    personnel: List[str] = Field(default_factory=list, description="涉及人员")
    roles: List[str] = Field(default_factory=list, description="涉及角色")
    work_content: Optional[str] = Field(default=None, description="工作内容描述")
    constraints: List[str] = Field(default_factory=list, description="限制条件列表")
    risks: List[str] = Field(default_factory=list, description="风险列表")
    issues: List[str] = Field(default_factory=list, description="问题列表")
    other_notes: Optional[str] = Field(default=None, description="其他说明")
    description: Optional[str] = Field(default=None, description="方案描述")
    owner: Optional[str] = Field(default=None, description="方案负责人")
    created_by: Optional[str] = Field(default=None, description="创建人")
    tags: List[str] = Field(default_factory=list, description="标签列表")

    @field_validator('solution_id', 'name')
    @classmethod
    def required_fields_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("方案ID和名称不能为空")
        return v.strip()


class SolutionResponse(BaseModel):
    """方案响应模型"""
    solution_id: str = Field(..., description="方案唯一标识")
    name: str = Field(..., description="方案名称")
    version: str = Field(..., description="版本号")
    status: SolutionStatus = Field(..., description="方案状态")
    priority: SolutionPriority = Field(..., description="方案优先级")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    message: str = Field(..., description="操作结果消息")


class DecompositionRequest(BaseModel):
    """方案拆分请求模型"""
    solution_id: str = Field(..., description="方案唯一标识")
    decomposition_strategy: Optional[str] = Field(default="auto", description="拆分策略")


class DecompositionResponse(BaseModel):
    """方案拆分响应模型"""
    solution_id: str = Field(..., description="方案唯一标识")
    task_count: int = Field(default=0, description="任务数量")
    flow_group_count: int = Field(default=0, description="任务流组数量")
    graph_id: Optional[str] = Field(default=None, description="任务图谱ID")
    tasks: List[Dict[str, Any]] = Field(default_factory=list, description="任务列表")
    flow_groups: List[Dict[str, Any]] = Field(default_factory=list, description="任务流组列表")
    message: str = Field(..., description="操作结果消息")


class TaskInfoResponse(BaseModel):
    """任务信息响应模型"""
    task_id: str = Field(..., description="任务唯一标识")
    task_name: str = Field(..., description="任务名称")
    task_type: str = Field(..., description="任务类型")
    content: str = Field(..., description="工作内容")
    execute_role: str = Field(..., description="执行角色")
    resource_consumption: float = Field(..., description="资源消耗")
    priority: str = Field(..., description="优先级")
    task_source: Optional[str] = Field(default=None, description="任务来源")
    task_destinations: List[str] = Field(default_factory=list, description="任务去向")
    status: str = Field(default="pending", description="任务状态")


class FlowGroupInfoResponse(BaseModel):
    """任务流组信息响应模型"""
    flow_id: str = Field(..., description="任务流唯一标识")
    flow_name: str = Field(..., description="任务流名称")
    description: Optional[str] = Field(default=None, description="任务流描述")
    task_count: int = Field(default=0, description="任务数量")
    tasks: List[TaskInfoResponse] = Field(default_factory=list, description="任务列表")


class TaskGraphInfoResponse(BaseModel):
    """任务图谱信息响应模型"""
    graph_id: str = Field(..., description="图谱唯一标识")
    graph_name: str = Field(..., description="图谱名称")
    description: Optional[str] = Field(default=None, description="图谱描述")
    node_count: int = Field(default=0, description="节点数量")
    edge_count: int = Field(default=0, description="边数量")
    start_task_count: int = Field(default=0, description="开始任务数量")
    end_task_count: int = Field(default=0, description="结束任务数量")
    nodes: List[Dict[str, Any]] = Field(default_factory=list, description="节点列表")
    edges: List[Dict[str, Any]] = Field(default_factory=list, description="边列表")


class SimulationStartRequest(BaseModel):
    """仿真启动请求模型"""
    solution_id: str = Field(..., description="方案唯一标识")
    manifest_id: Optional[str] = Field(default=None, description="任务清单ID")
    simulation_config: Optional[Dict[str, Any]] = Field(default=None, description="仿真配置")


class SimulationLogResponse(BaseModel):
    """仿真日志响应模型"""
    solution_id: str = Field(..., description="方案唯一标识")
    simulation_id: str = Field(..., description="仿真唯一标识")
    status: SimulationStatus = Field(..., description="仿真状态")
    log_content: str = Field(default="", description="日志内容")
    current_step: Optional[str] = Field(default=None, description="当前步骤")
    progress: float = Field(default=0.0, description="进度百分比")
    start_time: Optional[datetime] = Field(default=None, description="开始时间")
    end_time: Optional[datetime] = Field(default=None, description="结束时间")
    message: str = Field(..., description="操作结果消息")


class EvaluationAgentSelection(BaseModel):
    """评估Agent选择模型"""
    agent_id: str = Field(..., description="Agent唯一标识")
    agent_name: str = Field(..., description="Agent名称")
    index_ids: List[str] = Field(default_factory=list, description="关联的评价指标ID列表")
    is_selected: bool = Field(default=False, description="是否被选中")


class EvaluationStartRequest(BaseModel):
    """评估启动请求模型"""
    solution_id: str = Field(..., description="方案唯一标识")
    evaluation_id: str = Field(..., description="评估唯一标识")
    selected_agents: List[EvaluationAgentSelection] = Field(default_factory=list, description="选中的评估Agent列表")
    selected_indices: List[str] = Field(default_factory=list, description="选中的评价指标ID列表")
    use_simulation_log: bool = Field(default=False, description="是否使用仿真日志")
    simulation_id: Optional[str] = Field(default=None, description="关联的仿真ID")


class EvaluationResultResponse(BaseModel):
    """评估结果响应模型"""
    evaluation_id: str = Field(..., description="评估唯一标识")
    solution_id: str = Field(..., description="方案唯一标识")
    status: EvaluationStatus = Field(..., description="评估状态")
    overall_score: Optional[float] = Field(default=None, description="总体评分")
    agent_results: List[Dict[str, Any]] = Field(default_factory=list, description="各Agent评估结果")
    index_scores: List[Dict[str, Any]] = Field(default_factory=list, description="各指标评分")
    recommendations: List[str] = Field(default_factory=list, description="改进建议")
    start_time: Optional[datetime] = Field(default=None, description="开始时间")
    end_time: Optional[datetime] = Field(default=None, description="结束时间")
    message: str = Field(..., description="操作结果消息")


class EvaluationAbortRequest(BaseModel):
    """评估中止请求模型"""
    evaluation_id: str = Field(..., description="评估唯一标识")
    reason: Optional[str] = Field(default=None, description="中止原因")


class ApiResponse(BaseModel):
    """通用API响应模型"""
    success: bool = Field(default=True, description="是否成功")
    code: int = Field(default=200, description="响应状态码")
    message: str = Field(default="操作成功", description="响应消息")
    data: Optional[Dict[str, Any]] = Field(default=None, description="响应数据")
    timestamp: datetime = Field(default_factory=datetime.now, description="响应时间")


class PageResponse(BaseModel):
    """页面响应模型（用于返回简单页面）"""
    title: str = Field(..., description="页面标题")
    message: str = Field(..., description="页面消息")
    status: str = Field(default="success", description="状态")
    detail: Optional[str] = Field(default=None, description="详细信息")
