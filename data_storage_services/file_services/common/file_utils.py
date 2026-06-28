"""文件存储通用工具 (file_services/common)。

通用文件操作: 编码、路径构造、安全写入、删除、存在检查等。
"""
from __future__ import annotations
import base64
import hashlib
import logging
import os
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger("file_utils")


def generate_file_id() -> str:
    """生成业务唯一文件ID (UUID4 去掉连字符, 32位)。"""
    return uuid.uuid4().hex


def ensure_dir(path: str) -> str:
    """确保目录存在, 返回绝对路径。"""
    Path(path).mkdir(parents=True, exist_ok=True)
    return str(Path(path).resolve())


def safe_join(base_dir: str, *parts: str) -> str:
    """安全拼接路径 (阻止 `..` 路径穿越)。"""
    base = Path(base_dir).resolve()
    full = (base.joinpath(*parts)).resolve()
    try:
        full.relative_to(base)
    except ValueError:
        raise ValueError(f"路径穿越被拒绝: {base_dir} + {parts}")
    ensure_dir(str(full.parent))
    return str(full)


def write_text(path: str, content: str, encoding: str = "utf-8") -> int:
    """写入文本文件, 返回字节大小。"""
    ensure_dir(str(Path(path).parent))
    Path(path).write_text(content, encoding=encoding)
    return os.path.getsize(path)


def write_bytes(path: str, data: bytes) -> int:
    """写入二进制文件, 返回字节大小。"""
    ensure_dir(str(Path(path).parent))
    Path(path).write_bytes(data)
    return os.path.getsize(path)


def read_text(path: str, encoding: str = "utf-8") -> Optional[str]:
    """读取文本文件 (不存在返回 None)。"""
    if not os.path.isfile(path):
        return None
    return Path(path).read_text(encoding=encoding)


def read_bytes(path: str) -> Optional[bytes]:
    if not os.path.isfile(path):
        return None
    return Path(path).read_bytes()


def delete_file(path: str) -> bool:
    """删除文件 (不存在返回 False)。"""
    try:
        if os.path.isfile(path):
            os.remove(path)
            return True
    except Exception as ex:
        logger.warning("delete_file failed: %s", ex)
    return False


def delete_dir(path: str, recursive: bool = True) -> bool:
    try:
        if os.path.isdir(path):
            shutil.rmtree(path) if recursive else os.rmdir(path)
            return True
    except Exception as ex:
        logger.warning("delete_dir failed: %s", ex)
    return False


def file_exists(path: str) -> bool:
    return os.path.isfile(path)


def file_size(path: str) -> int:
    return os.path.getsize(path) if os.path.isfile(path) else 0


def compute_md5(path: str) -> str:
    h = hashlib.md5()
    if not os.path.isfile(path):
        return ""
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def b64_encode_bytes(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def b64_decode_str(s: str) -> bytes:
    return base64.b64decode(s.encode("ascii"))


def safe_filename(name: str, fallback: str = "file") -> str:
    """去除 Windows 非法字符。"""
    for ch in '<>:"/\\|?*\x00-\x1f':
        name = name.replace(ch, "_")
    name = name.strip(" .")
    return name or fallback
