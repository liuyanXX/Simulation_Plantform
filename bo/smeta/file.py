"""方案元空间 · 方案文件对象业务模型

文件对象既持久化到关系数据库 (smeta_file)，又有对应的实体文件存在于
Simulation_Plantform/Files/Solutions/<solution_id>/<file_category_cn>/ 目录下。
"""
from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


class FileCategory(str, Enum):
    """文件类别（中文业务枚举，同时作为物理子目录名）。"""

    MAIN_DOC = "主文档"
    ATTACHMENT = "附件文档"
    REFERENCE = "参考文档"


class FileCategoryEn(str, Enum):
    """英文内部标识（便于数据库存储/目录）。"""

    MAIN_DOC = "main_doc"
    ATTACHMENT = "attachment"
    REFERENCE = "reference"

    @classmethod
    def from_cn(cls, cn: str) -> "FileCategoryEn":
        mapping = {
            FileCategory.MAIN_DOC.value: cls.MAIN_DOC,
            FileCategory.ATTACHMENT.value: cls.ATTACHMENT,
            FileCategory.REFERENCE.value: cls.REFERENCE,
        }
        return mapping.get(cn, cls.MAIN_DOC)

    def to_cn(self) -> str:
        mapping = {
            FileCategoryEn.MAIN_DOC: FileCategory.MAIN_DOC.value,
            FileCategoryEn.ATTACHMENT: FileCategory.ATTACHMENT.value,
            FileCategoryEn.REFERENCE: FileCategory.REFERENCE.value,
        }
        return mapping[self]


def _category_to_cn(category: str) -> str:
    if category in {e.value for e in FileCategory}:
        return category
    if category in {e.value for e in FileCategoryEn}:
        return FileCategoryEn(category).to_cn()
    raise ValueError(f"无效的文件类别: {category}")


class File(BaseModel):
    """方案元空间 · 文件对象 (对应表 smeta_file)。"""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    id: str = Field(
        default="",
        description="文件ID(UUID4 字符串, 业务唯一, 数据库 UNIQUE)",
    )
    file_name: str = Field(min_length=1, max_length=256, description="文件名称(含扩展名)")
    version_no: str = Field(default="1.0", max_length=64, description="版本号")
    file_category: str = Field(
        default=FileCategory.MAIN_DOC.value,
        description="文件类别: 主文档/附件文档/参考文档",
    )
    solution_id: str = Field(max_length=64, description="方案ID")
    solution_name: Optional[str] = Field(default=None, max_length=128, description="方案名称")
    physical_path: str = Field(default="", max_length=512, description="物理存放相对路径(相对于项目根)")
    content_text: Optional[str] = Field(default=None, description="文件内容(长文本, 可选)")
    file_size: Optional[int] = Field(default=None, description="实体文件字节大小")
    mime_type: Optional[str] = Field(default=None, max_length=64, description="MIME 类型")
    description: Optional[str] = Field(default=None, description="文件说明")
    created_at: str = Field(default_factory=_now_iso, description="创建时间(ISO)")
    updated_at: str = Field(default_factory=_now_iso, description="更新时间(ISO)")

    @field_validator("file_name", "solution_id")
    @classmethod
    def _trim_str(cls, v: str) -> str:
        return v.strip()

    @field_validator("file_category")
    @classmethod
    def _valid_category(cls, v: str) -> str:
        return _category_to_cn(v)

    def to_dict(self, include_content: bool = True) -> Dict[str, Any]:
        data = self.model_dump()
        if not include_content:
            data.pop("content_text", None)
        return data
