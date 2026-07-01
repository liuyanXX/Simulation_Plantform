"""知识空间域 · 指标管理库业务对象

指标管理库由三类核心对象组成:
  - 指标分类分级目录 (IndicatorCategory)  -> 树形结构, 所有指标挂载至该分类树下
  - 通用指标 (Indicator)                   -> 全局唯一基础指标, 跨模板复用
  - 指标配套附件 (IndicatorAttach)          -> 指标打分细则/行业规范/示例文档

对应数据表 (前缀 km_, 归属知识空间):
  - km_indicator_category
  - km_indicator_info
  - km_indicator_attach

说明:
  - 数据类型/枚举字段统一使用 int 存储 (与需求文档 tinyint 对齐), 业务层通过 Enum 提供语义。
  - scene_tag / tag_list 等逗号分隔字符串字段, 业务对象层以 List[str] 承载,
    Service 层负责与 DB 的 varchar 之间序列化/反序列化。
"""
from __future__ import annotations

from datetime import datetime
from enum import IntEnum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


def _now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


class CommonStatus(IntEnum):
    """通用启停用状态。"""

    DISABLED = 0
    ENABLED = 1


class IndicatorInfoStatus(IntEnum):
    """指标主表状态: 0停用 1正常 2草稿。"""

    DISABLED = 0
    NORMAL = 1
    DRAFT = 2


class IndicatorDataType(IntEnum):
    """指标数据类型: 1定量数值 2定性打分 3布尔合规 4枚举选项。"""

    QUANTITATIVE = 1
    QUALITATIVE = 2
    BOOLEAN = 3
    ENUM = 4


class AttachType(IntEnum):
    """附件类型: 1行业标准 2打分示例 3评估细则。"""

    INDUSTRY_STANDARD = 1
    SCORE_EXAMPLE = 2
    EVALUATION_RULE = 3


class IndicatorCategory(BaseModel):
    """指标分类分级目录 (km_indicator_category)。

    树形存储指标目录, 所有指标挂载至该分类树下。
    """

    model_config = ConfigDict(populate_by_name=True)

    category_id: Optional[int] = Field(default=None, description="分类唯一ID (PK自增)")
    parent_id: int = Field(default=0, description="父分类ID, 根节点值为0")
    category_name: str = Field(min_length=1, max_length=128, description="分类名称")
    category_code: str = Field(min_length=1, max_length=64, description="全局唯一分类编码")
    level: int = Field(default=1, ge=1, description="层级: 1一级大类 2二级分类 3三级分组")
    sort: int = Field(default=0, description="同层级展示排序序号")
    scene_tag: List[str] = Field(default_factory=list, description="适用场景标签(列表), 如 绩效/系统/需求/流程")
    remark: Optional[str] = Field(default=None, max_length=512, description="分类业务描述")
    status: int = Field(default=CommonStatus.ENABLED.value, description="0停用 1启用")
    create_time: str = Field(default_factory=_now_iso, description="创建时间")
    update_time: str = Field(default_factory=_now_iso, description="更新时间")


class Indicator(BaseModel):
    """通用指标主表 (km_indicator_info)。

    全局唯一基础指标, 跨模板复用, 包含评估口径/阈值/标准。
    """

    model_config = ConfigDict(populate_by_name=True)

    indicator_id: Optional[int] = Field(default=None, description="指标唯一主键 (PK自增)")
    category_id: int = Field(description="归属分类ID, 关联 km_indicator_category")
    indicator_name: str = Field(min_length=1, max_length=256, description="指标名称")
    indicator_code: str = Field(min_length=1, max_length=64, description="全局唯一指标编码")
    indicator_desc: Optional[str] = Field(default=None, description="指标定义/评估统计口径/计算说明")
    data_type: int = Field(default=IndicatorDataType.QUANTITATIVE.value, description="1定量数值 2定性打分 3布尔合规 4枚举选项")
    unit: Optional[str] = Field(default=None, max_length=32, description="指标单位: %/天/ms/万元/分 等")
    standard_value: Optional[str] = Field(default=None, max_length=256, description="行业/企业基准标准值")
    min_threshold: Optional[float] = Field(default=None, description="最低合格阈值")
    max_threshold: Optional[float] = Field(default=None, description="最优达标阈值")
    positive_flag: int = Field(default=1, description="1正向指标(越大越好) 0负向指标(越小越好)")
    default_score_rule_id: Optional[int] = Field(default=None, description="指标默认配套计分规则ID")
    tag_list: List[str] = Field(default_factory=list, description="场景标签(列表), 标记适用评估场景")
    version: int = Field(default=1, ge=1, description="指标版本号")
    status: int = Field(default=IndicatorInfoStatus.NORMAL.value, description="0停用 1正常 2草稿")
    create_user: Optional[int] = Field(default=None, description="创建人用户ID")
    create_time: str = Field(default_factory=_now_iso, description="创建时间")
    update_time: str = Field(default_factory=_now_iso, description="更新时间")


class IndicatorAttach(BaseModel):
    """指标配套附件标准表 (km_indicator_attach)。

    存储指标打分细则/行业规范/示例文档, 支撑开箱查阅。
    """

    model_config = ConfigDict(populate_by_name=True)

    attach_id: Optional[int] = Field(default=None, description="附件主键ID (PK自增)")
    indicator_id: int = Field(description="关联指标ID")
    file_name: str = Field(min_length=1, max_length=256, description="附件展示名称")
    file_url: str = Field(min_length=1, max_length=1024, description="对象存储文件访问地址")
    attach_type: int = Field(default=AttachType.INDUSTRY_STANDARD.value, description="1行业标准 2打分示例 3评估细则")
    create_time: str = Field(default_factory=_now_iso, description="上传时间")


def new_category(
    category_name: str,
    category_code: str,
    parent_id: int = 0,
    level: int = 1,
    sort: int = 0,
    scene_tag: Optional[List[str]] = None,
    remark: Optional[str] = None,
) -> IndicatorCategory:
    """快捷构造指标分类。"""
    return IndicatorCategory(
        category_name=category_name.strip(),
        category_code=category_code.strip(),
        parent_id=parent_id,
        level=level,
        sort=sort,
        scene_tag=scene_tag or [],
        remark=remark,
    )


def new_indicator(
    category_id: int,
    indicator_name: str,
    indicator_code: str,
    data_type: int = IndicatorDataType.QUANTITATIVE.value,
    indicator_desc: Optional[str] = None,
    unit: Optional[str] = None,
) -> Indicator:
    """快捷构造通用指标。"""
    return Indicator(
        category_id=category_id,
        indicator_name=indicator_name.strip(),
        indicator_code=indicator_code.strip(),
        data_type=data_type,
        indicator_desc=indicator_desc,
        unit=unit,
    )
