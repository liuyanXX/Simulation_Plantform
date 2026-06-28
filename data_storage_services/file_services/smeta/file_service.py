"""方案元空间 · 实体文件存储服务 (SmetaFileStorage)

物理布局（相对于 Simulation_Plantform/）:
    Files/Solutions/<solution_id>/<文件类别(中文)>/<file_id>__<文件名>

同时在根下维护 smeta_file 表 (SQLite), 提供完整的方案文件元数据 CRUD。

两类使用方式:
  1) 实体文件 = 二进制/文本, 存磁盘, content_text 可以存也可以不存 (按需传)
  2) 纯文本文件 = 直接把文本写进实体文件 + 写 content_text

目录结构遵循用户要求: Files/Solutions/$方案ID/$文件类别/
"""
from __future__ import annotations
import logging
import mimetypes
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from data_storage_services.file_services.common.file_utils import (
    b64_decode_str,
    b64_encode_bytes,
    compute_md5,
    delete_file,
    ensure_dir,
    file_exists,
    file_size,
    generate_file_id,
    read_bytes,
    read_text,
    safe_filename,
    safe_join,
    write_bytes,
    write_text,
)
from bo.smeta.file import File, FileCategory, FileCategoryEn, _category_to_cn


logger = logging.getLogger("SmetaFileStorage")


def _now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


class SmetaFileStorage:
    """方案元空间 · 实体文件存储服务 (纯文件 + 元数据 CRUD)。"""

    ROOT = "Files/Solutions"

    def __init__(self, root_dir: Optional[str] = None) -> None:
        self.root_dir = root_dir if root_dir is not None else self.ROOT
        ensure_dir(self.root_dir)

    # ---------- 路径构造 ----------
    def _build_dir(self, solution_id: str, file_category: str) -> str:
        cn = _category_to_cn(file_category)
        return safe_join(self.root_dir, solution_id, cn)

    def _build_path(self, solution_id: str, file_category: str, file_id: str, file_name: str) -> str:
        d = self._build_dir(solution_id, file_category)
        safe_name = safe_filename(file_name, fallback="file")
        if file_id:
            fname = f"{file_id}__{safe_name}"
        else:
            fname = safe_name
        return safe_join(d, fname)

    # ---------- 核心保存 ----------
    def save(
        self,
        file: File,
        content: Optional[Union[str, bytes]] = None,
        *,
        is_text: Optional[bool] = None,
        overwrite: bool = False,
    ) -> File:
        """保存文件 (同时写实体文件 + 回填 DB 元数据字段)。

        :param file: Pydantic File (file_id 若为空则自动生成 UUID4)
        :param content: 文本(str) 或 二进制(bytes) 或 None
        :param is_text: 如果 content 为 None 时指定; 否则自动推断
        :param overwrite: 路径已存在时是否覆盖
        :return: 回填后的 File
        """
        if not file.id:
            file.id = generate_file_id()
        if not file.created_at:
            file.created_at = _now_iso()
        file.updated_at = _now_iso()
        file.file_category = _category_to_cn(file.file_category)
        if not file.solution_name:
            file.solution_name = ""

        target = self._build_path(
            file.solution_id, file.file_category, file.id, file.file_name
        )

        exists = file_exists(target)
        if exists and not overwrite:
            raise FileExistsError(f"文件已存在且 overwrite=False: {target}")

        size = 0
        if content is not None:
            if isinstance(content, str):
                size = write_text(target, content)
                file.content_text = content
            else:
                size = write_bytes(target, content)
                if is_text:
                    try:
                        file.content_text = content.decode("utf-8")
                    except UnicodeDecodeError:
                        file.content_text = None
                else:
                    file.content_text = None
        else:
            ensure_dir(os.path.dirname(target))

        file.file_size = size or file_size(target) if exists else size
        file.physical_path = os.path.relpath(target).replace("\\", "/")
        file.mime_type = mimetypes.guess_type(file.file_name)[0] or "application/octet-stream"
        return file

    def save_bytes(
        self,
        solution_id: str,
        file_name: str,
        file_category: str,
        content: bytes,
        file_id: Optional[str] = None,
        version_no: str = "1.0",
        solution_name: Optional[str] = None,
        description: Optional[str] = None,
        overwrite: bool = False,
    ) -> File:
        f = File(
            id=file_id or generate_file_id(),
            file_name=file_name,
            version_no=version_no,
            file_category=_category_to_cn(file_category),
            solution_id=solution_id,
            solution_name=solution_name or solution_id,
            description=description,
        )
        return self.save(f, content=content, is_text=False, overwrite=overwrite)

    def save_text(
        self,
        solution_id: str,
        file_name: str,
        file_category: str,
        content: str,
        file_id: Optional[str] = None,
        version_no: str = "1.0",
        solution_name: Optional[str] = None,
        description: Optional[str] = None,
        overwrite: bool = False,
    ) -> File:
        f = File(
            id=file_id or generate_file_id(),
            file_name=file_name,
            version_no=version_no,
            file_category=_category_to_cn(file_category),
            solution_id=solution_id,
            solution_name=solution_name or solution_id,
            description=description,
        )
        return self.save(f, content=content, is_text=True, overwrite=overwrite)

    def save_b64(
        self,
        solution_id: str,
        file_name: str,
        file_category: str,
        b64_content: str,
        file_id: Optional[str] = None,
        version_no: str = "1.0",
        solution_name: Optional[str] = None,
        description: Optional[str] = None,
        overwrite: bool = False,
    ) -> File:
        raw = b64_decode_str(b64_content)
        return self.save_bytes(
            solution_id, file_name, file_category, raw,
            file_id=file_id, version_no=version_no,
            solution_name=solution_name, description=description,
            overwrite=overwrite,
        )

    # ---------- 读取 ----------
    def read_text(self, physical_path: str) -> Optional[str]:
        return read_text(physical_path)

    def read_bytes(self, physical_path: str) -> Optional[bytes]:
        return read_bytes(physical_path)

    def exists(self, physical_path: str) -> bool:
        return file_exists(physical_path)

    def delete(self, physical_path: str) -> bool:
        return delete_file(physical_path)

    def md5(self, physical_path: str) -> str:
        return compute_md5(physical_path)
