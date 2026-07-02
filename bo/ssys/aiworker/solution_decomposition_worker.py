"""方案拆分智能员工模块

定义 SolutionDecompositionWorker（方案拆分智能员工）类，继承自 AIWorker 基础类，
负责对结构化方案（Solution）进行拆分，生成任务（Task）、任务图谱（TasksGraph）、
任务清单（TaskManifest）、任务流组（TaskFlowGroup）。

归属：系统空间（ssys），对象代码位于 bo/ssys/aiworker/ 目录下。
"""
from pydantic import Field, PrivateAttr
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timedelta
import uuid

from .ai_worker import AIWorker, logger


class SolutionDecompositionWorker(AIWorker):
    """
    方案拆分智能员工

    继承 AIWorker 基础类的全部能力（任务清单、排期、持续工作、任务传递等），
    并在此基础上扩展“方案拆分”能力：接收结构化方案（Solution），将其举措/工作内容
    拆分为一系列任务，并组装为任务图谱、任务流组与任务清单。

    典型职责：
      1. 接收结构化方案对象（Solution）。
      2. 将方案举措（initiatives）逐项拆分为普通任务（Task），并补充开始/结束任务。
      3. 建立任务间有向关联，生成任务图谱（TasksGraph）。
      4. 由图谱路径拆分出任务流组（TaskFlowGroup）。
      5. 汇总为任务清单（TaskManifest），供后续仿真执行与评估使用。

    :param worker_type: 员工类型标识，固定为 "SolutionDecompositionWorker"
    :param default_role: 未指定角色时任务的默认执行角色
    :param default_task_hours: 单个任务默认资源消耗（工时）
    :ivar _decomposition_results: 已生成的拆分结果缓存
    """

    worker_type: str = Field(default="SolutionDecompositionWorker", description="智能员工类型标识")
    default_role: str = Field(default="EXECUTOR", description="未指定角色时任务的默认执行角色")
    default_task_hours: float = Field(default=1.0, description="单个任务默认资源消耗（工时）")

    _decomposition_results: List[Dict[str, Any]] = PrivateAttr(default_factory=list)

    # ------------------------------------------------------------------
    # 核心能力：方案拆分
    # ------------------------------------------------------------------
    def decompose(self, solution: "Solution") -> Dict[str, Any]:
        """
        对结构化方案进行拆分，生成任务、任务图谱、任务流组、任务清单。

        拆分策略（自动、确定性）：
          1. 依据方案举措 initiatives 逐项生成普通任务；举措为空时，回退使用
             工作内容 / 方案目的合成一个默认任务。
          2. 首部补充开始任务（StartTask），尾部补充结束任务（EndTask），
             按顺序建立线性有向链路（START → T1 → ... → Tn → END）。
          3. 执行角色在方案 roles 列表中轮转分配；roles 为空时使用 default_role。
          4. 组装任务图谱（TasksGraph），由其路径拆分出任务流组（TaskFlowGroup），
             再汇总为任务清单（TaskManifest）。

        :param solution: 结构化方案对象（bo.solution.Solution）
        :return: 拆分结果字典，包含键：
                 tasks / tasks_graph / flow_groups / task_manifest
        :raises ValueError: solution 为空时抛出
        """
        from ...task import Task, StartTask, EndTask, Priority
        from ...tasks_graph import TasksGraph
        from ...task_manifest import TaskManifest

        if solution is None:
            raise ValueError("待拆分的结构化方案不能为空")

        logger.info(f"员工{self.name}开始拆分方案：{solution.solution_id} {solution.name}")

        prefix = self._id_prefix(solution.solution_id)
        roles = solution.roles or []
        base_time = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)

        # 1. 抽取待拆分的工作项
        work_items = self._extract_work_items(solution)

        # 2. 生成任务链
        tasks: List[Task] = []

        start_task = StartTask(
            task_id=f"{prefix}_START",
            task_name=f"{solution.name}-开始",
            expected_start_time=base_time,
            expected_end_time=base_time,
            content=solution.purpose or f"启动方案「{solution.name}」的拆分执行",
            execute_role="SYSTEM",
            resource_consumption=0.0,
            priority=Priority.LOW,
            output_target_role="",  # 由流组校验阶段自动回填
            task_destinations=[],
        )
        tasks.append(start_task)

        normal_tasks: List[Task] = []
        for idx, item in enumerate(work_items, start=1):
            role = roles[(idx - 1) % len(roles)] if roles else self.default_role
            t_start = base_time + timedelta(hours=(idx - 1) * self.default_task_hours)
            t_end = t_start + timedelta(hours=self.default_task_hours)
            task = Task(
                task_id=f"{prefix}_T{idx:03d}",
                task_name=item[:64] if item else f"任务{idx}",
                expected_start_time=t_start,
                expected_end_time=t_end,
                content=item,
                execute_role=role,
                resource_consumption=self.default_task_hours,
                priority=Priority.MEDIUM,
                output_target_role="",
                task_destinations=[],
            )
            normal_tasks.append(task)
            tasks.append(task)

        end_task = EndTask(
            task_id=f"{prefix}_END",
            task_name=f"{solution.name}-结束",
            expected_start_time=base_time,
            expected_end_time=base_time,
            content=f"方案「{solution.name}」拆分执行完成",
            execute_role="SYSTEM",
            resource_consumption=0.0,
            priority=Priority.LOW,
            output_target_role="",
            task_source=None,
            task_destinations=[],
        )
        tasks.append(end_task)

        # 3. 建立线性有向关联：START -> T1 -> ... -> Tn -> END
        chain = [start_task] + normal_tasks + [end_task]
        for i in range(len(chain) - 1):
            current, nxt = chain[i], chain[i + 1]
            current.task_destinations = [nxt.task_id]
            nxt.task_source = current.task_id
            # 结束任务不设输出目标角色
            current.output_target_role = "" if nxt is end_task else nxt.execute_role

        # 4. 任务图谱
        tasks_graph = TasksGraph(
            graph_id=f"GRAPH_{prefix}",
            graph_name=f"{solution.name}_任务图谱",
            tasks=tasks,
            description=f"由方案 {solution.solution_id} 拆分生成的任务图谱",
        )

        # 5. 任务流组（由图谱路径拆分）
        flow_groups = tasks_graph.split_into_flow_groups()

        # 6. 任务清单
        task_manifest = TaskManifest(
            manifest_id=f"MANIFEST_{prefix}",
            manifest_name=f"{solution.name}_任务清单",
            flow_groups=flow_groups,
            description=f"由方案 {solution.solution_id} 拆分生成的任务清单",
        )
        task_manifest._solution_id = solution.solution_id

        result = {
            "solution_id": solution.solution_id,
            "tasks": tasks,
            "tasks_graph": tasks_graph,
            "flow_groups": flow_groups,
            "task_manifest": task_manifest,
        }
        self._decomposition_results.append(result)

        logger.info(
            f"员工{self.name}完成方案拆分：{solution.solution_id} -> "
            f"任务{len(tasks)}个/图谱路径{len(flow_groups)}条/任务流组{len(flow_groups)}个"
        )
        return result

    def decompose_to_manifest(self, solution: "Solution") -> "TaskManifest":
        """
        拆分方案并仅返回任务清单（便捷方法）。

        :param solution: 结构化方案对象
        :return: TaskManifest 对象
        """
        return self.decompose(solution)["task_manifest"]

    def get_decomposition_results(self) -> List[Dict[str, Any]]:
        """
        获取本员工已生成的全部拆分结果。

        :return: 拆分结果字典列表
        """
        return list(self._decomposition_results)

    # ------------------------------------------------------------------
    # 内部工具
    # ------------------------------------------------------------------
    def _extract_work_items(self, solution: "Solution") -> List[str]:
        """
        从方案中抽取需要拆分为任务的工作项。

        优先使用方案举措（initiatives）；举措为空时依次回退到目标（objectives）、
        工作内容（work_content）、方案目的（purpose）；均为空时生成一个占位任务。

        :param solution: 结构化方案对象
        :return: 工作项文本列表（至少 1 项）
        """
        if solution.initiatives:
            return [x for x in solution.initiatives if x and x.strip()]
        if solution.objectives:
            return [x for x in solution.objectives if x and x.strip()]
        if solution.work_content and solution.work_content.strip():
            return [solution.work_content.strip()]
        if solution.purpose and solution.purpose.strip():
            return [solution.purpose.strip()]
        return [f"执行方案「{solution.name}」"]

    @staticmethod
    def _id_prefix(solution_id: Optional[str]) -> str:
        """基于方案ID构造任务/图谱/清单的ID前缀，缺失时生成随机前缀。"""
        if solution_id and solution_id.strip():
            return solution_id.strip()
        return f"SOL_{uuid.uuid4().hex[:8].upper()}"

    def __str__(self) -> str:
        """返回方案拆分智能员工的字符串表示。"""
        return (
            f"SolutionDecompositionWorker(工号={self.employee_id}, 姓名={self.name}, "
            f"部门={self.department}, 角色={self.roles}, 已拆分方案={len(self._decomposition_results)})"
        )


# 延迟导入以更新前向引用（Solution 位于 bo/solution.py）
from ...solution import Solution  # noqa: E402
from ...task_manifest import TaskManifest  # noqa: E402
SolutionDecompositionWorker.update_forward_refs()


if __name__ == "__main__":
    from ...solution import Solution as _Solution

    worker = SolutionDecompositionWorker(
        employee_id="EMP_SD_001",
        name="方案拆分员",
        department="方案拆分部",
        roles=["需求分析师", "开发工程师", "测试工程师"],
    )

    demo_solution = _Solution(
        solution_id="SOL_DEMO_001",
        name="企业数字化转型实施方案",
        version="1.0",
        purpose="推动企业数字化转型，提升整体运营效率",
        objectives=["实现核心业务流程数字化", "建立数据驱动的决策体系"],
        initiatives=["引入云平台", "建设大数据分析系统", "开展员工数字化培训"],
        roles=["需求分析师", "开发工程师", "测试工程师"],
        work_content="完成数字化转型的规划、实施与推广",
    )

    print("=== 测试：方案拆分 ===")
    result = worker.decompose(demo_solution)
    print(f"生成任务数：{len(result['tasks'])}")
    print(f"任务流组数：{len(result['flow_groups'])}")
    print("\n任务图谱摘要：")
    import json as _json
    print(_json.dumps(result["tasks_graph"].get_graph_summary(), ensure_ascii=False, indent=2))
    print("\n任务清单摘要：")
    print(_json.dumps(result["task_manifest"].get_manifest_summary(), ensure_ascii=False, indent=2))
    print("\n任务流组明细：")
    for fg in result["flow_groups"]:
        print(_json.dumps(fg.get_flow_summary(), ensure_ascii=False, indent=2))
