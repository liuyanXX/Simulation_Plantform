"""任务执行智能员工模块

定义 TaskExecutionWorker（任务执行智能员工）类，继承自 AIWorker 基础类，
负责对任务进行执行，并记录结构化执行日志（execution log）供未来分析使用。

归属：系统空间（ssys），对象代码位于 bo/ssys/aiworker/ 目录下。
"""
from pydantic import BaseModel, Field, PrivateAttr
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import time

from .ai_worker import AIWorker, logger


class ExecutionStatus:
    """执行结果状态常量。"""
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class ExecutionLogEntry(BaseModel):
    """
    单条任务执行日志

    完整留存一次任务执行的过程与结果，供未来的执行分析、复盘与优化使用。

    :param log_id: 日志唯一标识
    :param task_id: 被执行任务ID
    :param task_name: 任务名称
    :param employee_id: 执行员工工号
    :param employee_name: 执行员工姓名
    :param execute_role: 执行角色
    :param status: 执行结果状态（success/failed/skipped）
    :param start_time: 实际开始时间
    :param end_time: 实际结束时间
    :param duration_seconds: 执行耗时（秒）
    :param resource_consumption: 计划资源消耗（工时）
    :param raw_value: 任务原始产出/填报值（可选）
    :param remark: 备注/情况说明
    :param error_message: 失败时的错误信息
    :param created_at: 日志创建时间
    """
    log_id: str = Field(description="日志唯一标识")
    task_id: str = Field(description="被执行任务ID")
    task_name: Optional[str] = Field(default=None, description="任务名称")
    employee_id: str = Field(description="执行员工工号")
    employee_name: Optional[str] = Field(default=None, description="执行员工姓名")
    execute_role: Optional[str] = Field(default=None, description="执行角色")
    status: str = Field(default=ExecutionStatus.SUCCESS, description="执行结果状态")
    start_time: Optional[datetime] = Field(default=None, description="实际开始时间")
    end_time: Optional[datetime] = Field(default=None, description="实际结束时间")
    duration_seconds: float = Field(default=0.0, description="执行耗时（秒）")
    resource_consumption: float = Field(default=0.0, description="计划资源消耗（工时）")
    raw_value: Optional[str] = Field(default=None, description="任务原始产出/填报值")
    remark: Optional[str] = Field(default=None, description="备注/情况说明")
    error_message: Optional[str] = Field(default=None, description="失败时的错误信息")
    created_at: datetime = Field(default_factory=datetime.now, description="日志创建时间")

    def to_json(self) -> str:
        """转换为 JSON 字符串。"""
        return json.dumps(self.model_dump(mode='json'), ensure_ascii=False, indent=2)


class TaskExecutionWorker(AIWorker):
    """
    任务执行智能员工

    继承 AIWorker 基础类的全部能力（任务清单、排期、持续工作、任务传递等），
    在执行任务时额外记录结构化执行日志（ExecutionLogEntry），完整留存执行过程与
    结果，供未来的执行分析、复盘与优化使用。

    典型职责：
      1. 执行分派到本员工的任务（复用基础类 execute_task 的完整流程）。
      2. 为每次执行生成一条执行日志，记录耗时、结果状态、产出与异常等。
      3. 支持导出日志、按状态筛选、统计执行摘要。

    :param worker_type: 员工类型标识，固定为 "TaskExecutionWorker"
    :ivar _execution_logs: 执行日志列表
    :ivar _log_seq: 日志序号自增计数器
    """

    worker_type: str = Field(default="TaskExecutionWorker", description="智能员工类型标识")

    _execution_logs: List[ExecutionLogEntry] = PrivateAttr(default_factory=list)
    _log_seq: int = PrivateAttr(default=0)

    # ------------------------------------------------------------------
    # 覆写任务执行：在基础执行流程上叠加执行日志记录
    # ------------------------------------------------------------------
    def execute_task(self, task: "Task", role_registry: Dict[str, "AIWorker"]) -> None:
        """
        执行单个任务，并记录结构化执行日志。

        复用基础类 AIWorker.execute_task 的完整执行流程（思考、执行、状态更新、
        后续任务派发），在其前后包裹计时与结果捕获，生成一条 ExecutionLogEntry。

        :param task: 待执行的任务对象
        :param role_registry: 角色注册表，用于查找目标角色对应的员工
        """
        start_dt = datetime.now()
        t0 = time.time()
        status = ExecutionStatus.SUCCESS
        error_message: Optional[str] = None

        logger.info(f"员工{self.name}[任务执行]开始执行任务: {task.task_id}")
        try:
            # 复用基础类的执行流程，保留其全部行为（含后续任务派发）
            super().execute_task(task, role_registry)
        except Exception as e:  # noqa: BLE001 - 记录任意执行异常供分析
            status = ExecutionStatus.FAILED
            error_message = str(e)
            logger.error(f"员工{self.name}[任务执行]任务 {task.task_id} 执行失败: {e}")
            raise
        finally:
            end_dt = datetime.now()
            entry = self._build_log_entry(task, status, start_dt, end_dt, time.time() - t0, error_message)
            self._execution_logs.append(entry)
            logger.info(
                f"员工{self.name}[任务执行]已记录执行日志: {entry.log_id} "
                f"(任务={task.task_id}, 状态={entry.status}, 耗时={entry.duration_seconds:.3f}s)"
            )

    def _build_log_entry(
        self,
        task: "Task",
        status: str,
        start_dt: datetime,
        end_dt: datetime,
        duration_seconds: float,
        error_message: Optional[str],
    ) -> ExecutionLogEntry:
        """
        构造一条执行日志。

        :param task: 被执行任务
        :param status: 执行结果状态
        :param start_dt: 实际开始时间
        :param end_dt: 实际结束时间
        :param duration_seconds: 执行耗时（秒）
        :param error_message: 失败时的错误信息
        :return: ExecutionLogEntry 对象
        """
        self._log_seq += 1
        return ExecutionLogEntry(
            log_id=f"EXECLOG_{self.employee_id}_{self._log_seq:04d}",
            task_id=task.task_id,
            task_name=getattr(task, "task_name", None),
            employee_id=self.employee_id,
            employee_name=self.name,
            execute_role=getattr(task, "execute_role", None),
            status=status,
            start_time=getattr(task, "actual_start_time", None) or start_dt,
            end_time=getattr(task, "actual_end_time", None) or end_dt,
            duration_seconds=round(duration_seconds, 3),
            resource_consumption=getattr(task, "resource_consumption", 0.0) or 0.0,
            raw_value=getattr(task, "content", None),
            remark=None,
            error_message=error_message,
        )

    # ------------------------------------------------------------------
    # 执行日志访问 / 分析
    # ------------------------------------------------------------------
    def get_execution_logs(self) -> List[ExecutionLogEntry]:
        """
        获取全部执行日志。

        :return: ExecutionLogEntry 列表
        """
        return list(self._execution_logs)

    def get_logs_by_status(self, status: str) -> List[ExecutionLogEntry]:
        """
        按执行结果状态筛选日志。

        :param status: 执行结果状态（success/failed/skipped）
        :return: 匹配的日志列表
        """
        return [log for log in self._execution_logs if log.status == status]

    def get_log_by_task(self, task_id: str) -> Optional[ExecutionLogEntry]:
        """
        获取指定任务的最近一条执行日志。

        :param task_id: 任务ID
        :return: 执行日志，未找到返回 None
        """
        for log in reversed(self._execution_logs):
            if log.task_id == task_id:
                return log
        return None

    def get_execution_summary(self) -> Dict[str, Any]:
        """
        获取执行摘要统计，供未来分析使用。

        :return: 包含总执行数、成功/失败数、总耗时、平均耗时等的字典
        """
        total = len(self._execution_logs)
        success = len(self.get_logs_by_status(ExecutionStatus.SUCCESS))
        failed = len(self.get_logs_by_status(ExecutionStatus.FAILED))
        total_duration = round(sum(log.duration_seconds for log in self._execution_logs), 3)
        avg_duration = round(total_duration / total, 3) if total else 0.0
        return {
            "employee_id": self.employee_id,
            "employee_name": self.name,
            "total_executions": total,
            "success_count": success,
            "failed_count": failed,
            "success_rate": round(success / total, 4) if total else 0.0,
            "total_duration_seconds": total_duration,
            "avg_duration_seconds": avg_duration,
        }

    def export_logs(self) -> str:
        """
        导出全部执行日志为 JSON 字符串，供持久化或离线分析。

        :return: JSON 字符串
        """
        return json.dumps(
            [log.model_dump(mode='json') for log in self._execution_logs],
            ensure_ascii=False,
            indent=2,
        )

    def clear_logs(self) -> None:
        """清空执行日志缓存。"""
        self._execution_logs.clear()
        self._log_seq = 0
        logger.info(f"员工{self.name}[任务执行]已清空执行日志")

    def __str__(self) -> str:
        """返回任务执行智能员工的字符串表示。"""
        return (
            f"TaskExecutionWorker(工号={self.employee_id}, 姓名={self.name}, "
            f"部门={self.department}, 角色={self.roles}, 执行日志={len(self._execution_logs)}条)"
        )


# 延迟导入以更新前向引用（Task 位于 bo/task.py）
from ...task import Task  # noqa: E402
TaskExecutionWorker.update_forward_refs()


if __name__ == "__main__":
    from datetime import timedelta
    from ...task import Task as _Task, Priority as _Priority

    worker = TaskExecutionWorker(
        employee_id="EMP_TE_001",
        name="任务执行员",
        department="执行部",
        roles=["EXECUTOR"],
    )

    now = datetime.now()
    task = _Task(
        task_id="T_EXEC_001",
        task_name="执行数据同步",
        expected_start_time=now,
        expected_end_time=now + timedelta(hours=1),
        content="从源库同步数据到目标库",
        execute_role="EXECUTOR",
        resource_consumption=0.01,
        priority=_Priority.HIGH,
        output_target_role="",
        task_destinations=[],
    )

    print("=== 测试：执行任务并记录日志 ===")
    worker.add_task(task)
    worker.work({"EXECUTOR": worker})

    print("\n执行日志：")
    for log in worker.get_execution_logs():
        print(log.to_json())

    print("\n执行摘要：")
    print(json.dumps(worker.get_execution_summary(), ensure_ascii=False, indent=2))
