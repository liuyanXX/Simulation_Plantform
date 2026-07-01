"""结果空间域 · 指标评估管理业务对象

覆盖需求文档 2.2 ~ 2.6 各域, 对应数据表 (前缀 srlt_, 归属结果空间):
  - srlt_object_type_dict        评估对象类型字典
  - srlt_evaluate_object         评估对象主表
  - srlt_evaluate_template       评估模板主表
  - srlt_template_indicator_rel  模板指标关联权重表
  - srlt_score_rule              指标计分规则表
  - srlt_evaluate_task           评估任务主表
  - srlt_task_indicator_record   评估指标填报明细表
  - srlt_evaluate_snapshot       评估结果快照宽表

说明:
  - 枚举字段统一使用 int 存储 (与需求 tinyint 对齐), 业务层通过 IntEnum 提供语义。
  - ext_json / rule_config_json / level_1_category_score 等 JSON 字段业务层以
    dict/list 承载, Service 层负责与 DB TEXT 之间序列化/反序列化。
  - attach_ids 逗号分隔字符串业务层以 List[str] 承载。
"""
from __future__ import annotations

from datetime import datetime
from enum import IntEnum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


def _now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


# ======================================================================
# 枚举
# ======================================================================
class ObjectStatus(IntEnum):
    """评估对象状态: 0作废 1正常。"""

    VOID = 0
    NORMAL = 1


class TemplateStatus(IntEnum):
    """模板状态: 0停用 1启用。"""

    DISABLED = 0
    ENABLED = 1


class SceneType(IntEnum):
    """模板适用场景: 1企业绩效 2软件系统 3需求评审 4流程效能。"""

    PERFORMANCE = 1
    SOFTWARE_SYSTEM = 2
    REQUIREMENT_REVIEW = 3
    PROCESS_EFFICIENCY = 4


class CalcType(IntEnum):
    """计分规则计算类型: 1固定分档 2线性公式 3阶梯阈值 4自定义表达式。"""

    FIXED_LEVEL = 1
    LINEAR = 2
    STEP_THRESHOLD = 3
    EXPRESSION = 4


class TaskStatus(IntEnum):
    """评估任务状态: 0草稿 1填报中 2待审核 3已完成 4作废。"""

    DRAFT = 0
    FILLING = 1
    AUDITING = 2
    FINISHED = 3
    VOID = 4


# ======================================================================
# 2.2 维度对象域
# ======================================================================
class ObjectTypeDict(BaseModel):
    """评估对象类型字典 (srlt_object_type_dict)。"""

    model_config = ConfigDict(populate_by_name=True)

    type_id: Optional[int] = Field(default=None, description="对象类型ID (PK)")
    type_code: str = Field(min_length=1, max_length=32, description="类型编码, 如 org/system/requirement")
    type_name: str = Field(min_length=1, max_length=64, description="对象类型中文名称")
    remark: Optional[str] = Field(default=None, max_length=256, description="对象类型业务说明")


class EvaluateObject(BaseModel):
    """评估对象主表 (srlt_evaluate_object)。"""

    model_config = ConfigDict(populate_by_name=True)

    object_id: Optional[int] = Field(default=None, description="对象唯一ID (PK自增)")
    object_type: int = Field(description="关联 srlt_object_type_dict.type_id")
    object_name: str = Field(min_length=1, max_length=256, description="对象名称")
    object_code: str = Field(min_length=1, max_length=64, description="业务系统内实体编码")
    org_id: Optional[int] = Field(default=None, description="所属组织ID, 用于数据权限隔离")
    ext_json: Dict[str, Any] = Field(default_factory=dict, description="扩展属性(差异化字段)")
    status: int = Field(default=ObjectStatus.NORMAL.value, description="0作废 1正常")
    create_time: str = Field(default_factory=_now_iso, description="创建时间")


# ======================================================================
# 2.3 评估模板域
# ======================================================================
class EvaluateTemplate(BaseModel):
    """评估模板主表 (srlt_evaluate_template)。"""

    model_config = ConfigDict(populate_by_name=True)

    template_id: Optional[int] = Field(default=None, description="模板唯一ID (PK自增)")
    template_name: str = Field(min_length=1, max_length=256, description="模板名称")
    template_code: str = Field(min_length=1, max_length=64, description="全局模板编码")
    scene_type: int = Field(default=SceneType.PERFORMANCE.value, description="适用场景 1企业绩效 2软件系统 3需求评审 4流程效能")
    template_desc: Optional[str] = Field(default=None, description="模板适用范围/评估操作指引")
    total_score: int = Field(default=100, description="模板总分, 默认100")
    is_preset: int = Field(default=0, description="1系统预制开箱模板 0用户自定义模板")
    version: int = Field(default=1, ge=1, description="模板版本号")
    status: int = Field(default=TemplateStatus.ENABLED.value, description="0停用 1启用")
    create_user: Optional[int] = Field(default=None, description="创建人ID")
    create_time: str = Field(default_factory=_now_iso, description="创建时间")


class TemplateIndicatorRel(BaseModel):
    """模板指标关联权重表 (srlt_template_indicator_rel)。"""

    model_config = ConfigDict(populate_by_name=True)

    rel_id: Optional[int] = Field(default=None, description="关联主键 (PK自增)")
    template_id: int = Field(description="关联模板ID")
    indicator_id: int = Field(description="关联指标ID (km_indicator_info.indicator_id)")
    weight: float = Field(default=0.0, description="指标权重, 全部指标权重总和为100")
    template_score_rule_id: Optional[int] = Field(default=None, description="模板内独立计分规则, 覆盖指标默认规则")
    sort: int = Field(default=0, description="指标在模板内展示顺序")
    must_fill: int = Field(default=1, description="1必填 0选填")


# ======================================================================
# 2.4 计分规则域
# ======================================================================
class ScoreRule(BaseModel):
    """指标计分规则表 (srlt_score_rule)。"""

    model_config = ConfigDict(populate_by_name=True)

    rule_id: Optional[int] = Field(default=None, description="规则ID (PK自增)")
    rule_name: str = Field(min_length=1, max_length=128, description="规则名称")
    calc_type: int = Field(default=CalcType.FIXED_LEVEL.value, description="1固定分档 2线性公式 3阶梯阈值 4自定义表达式")
    rule_config_json: Dict[str, Any] = Field(default_factory=dict, description="分档/阈值区间配置JSON")
    expression: Optional[str] = Field(default=None, max_length=1024, description="自定义四则运算计算公式")
    remark: Optional[str] = Field(default=None, max_length=512, description="规则业务说明")


# ======================================================================
# 2.5 评估实例域
# ======================================================================
class EvaluateTask(BaseModel):
    """评估任务主表 (srlt_evaluate_task)。"""

    model_config = ConfigDict(populate_by_name=True)

    task_id: Optional[int] = Field(default=None, description="评估任务ID (PK自增)")
    template_id: int = Field(description="使用的评估模板ID")
    object_id: int = Field(description="待评估对象ID")
    task_name: str = Field(min_length=1, max_length=256, description="任务名称")
    evaluate_cycle: Optional[str] = Field(default=None, max_length=64, description="评估周期: 月度/季度/年度/单次评审")
    start_time: Optional[str] = Field(default=None, description="填报开始时间")
    end_time: Optional[str] = Field(default=None, description="填报截止时间")
    task_status: int = Field(default=TaskStatus.DRAFT.value, description="0草稿 1填报中 2待审核 3已完成 4作废")
    total_score: Optional[float] = Field(default=None, description="本次评估最终总分")
    evaluate_conclusion: Optional[str] = Field(default=None, description="综合评估结论/优化改进建议")
    fill_user: Optional[int] = Field(default=None, description="填报评估人员ID")
    audit_user: Optional[int] = Field(default=None, description="审核人员ID")
    org_id: Optional[int] = Field(default=None, description="所属组织, 数据隔离")
    create_time: str = Field(default_factory=_now_iso, description="任务创建时间")
    finish_time: Optional[str] = Field(default=None, description="评估完成时间")


class TaskIndicatorRecord(BaseModel):
    """评估指标填报明细表 (srlt_task_indicator_record)。"""

    model_config = ConfigDict(populate_by_name=True)

    record_id: Optional[int] = Field(default=None, description="填报记录主键 (PK自增)")
    task_id: int = Field(description="所属评估任务ID")
    indicator_id: int = Field(description="对应评估指标ID")
    raw_value: Optional[str] = Field(default=None, max_length=512, description="原始填报值")
    real_score: Optional[float] = Field(default=None, description="经规则计算后的单指标得分")
    score_rule_id: Optional[int] = Field(default=None, description="本次评估使用的计分规则ID")
    fill_remark: Optional[str] = Field(default=None, description="评估人员备注/指标情况说明")
    attach_ids: List[str] = Field(default_factory=list, description="佐证附件ID列表")
    create_time: str = Field(default_factory=_now_iso, description="填报提交时间")


# ======================================================================
# 2.6 评估结果快照
# ======================================================================
class EvaluateSnapshot(BaseModel):
    """评估结果快照宽表 (srlt_evaluate_snapshot)。"""

    model_config = ConfigDict(populate_by_name=True)

    snapshot_id: Optional[int] = Field(default=None, description="快照唯一ID (PK自增)")
    task_id: int = Field(description="关联评估任务ID, 一对一")
    object_id: int = Field(description="待评估对象ID")
    template_id: int = Field(description="使用模板ID")
    object_type: int = Field(description="评估对象类型")
    total_score: Optional[float] = Field(default=None, description="评估总得分")
    level_1_category_score: Dict[str, Any] = Field(default_factory=dict, description="一级分类汇总得分JSON")
    evaluate_rank: Optional[str] = Field(default=None, max_length=32, description="综合评级: 优秀/良好/合格/待改进/不合格")
    snapshot_time: str = Field(default_factory=_now_iso, description="快照生成时间")


# ======================================================================
# 快捷构造
# ======================================================================
def new_object(object_type: int, object_name: str, object_code: str, org_id: Optional[int] = None, ext_json: Optional[Dict[str, Any]] = None) -> EvaluateObject:
    return EvaluateObject(object_type=object_type, object_name=object_name.strip(), object_code=object_code.strip(), org_id=org_id, ext_json=ext_json or {})


def new_template(template_name: str, template_code: str, scene_type: int = SceneType.PERFORMANCE.value, total_score: int = 100, is_preset: int = 0) -> EvaluateTemplate:
    return EvaluateTemplate(template_name=template_name.strip(), template_code=template_code.strip(), scene_type=scene_type, total_score=total_score, is_preset=is_preset)


def new_task(template_id: int, object_id: int, task_name: str, evaluate_cycle: Optional[str] = None, org_id: Optional[int] = None) -> EvaluateTask:
    return EvaluateTask(template_id=template_id, object_id=object_id, task_name=task_name.strip(), evaluate_cycle=evaluate_cycle, org_id=org_id)
