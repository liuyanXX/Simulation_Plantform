"""方案理解智能员工模块

定义 SolutionUnderstandingWorker（方案理解智能员工）类，继承自 AIWorker 基础类，
负责对原始方案信息（原始文本 / 字典 / 文档内容）进行理解，抽取并生成结构化的
方案信息（Solution 对象）。

归属：系统空间（ssys），对象代码位于 bo/ssys/aiworker/ 目录下。
"""
from pydantic import Field, PrivateAttr
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
import re
import uuid

from .ai_worker import AIWorker, logger


class SolutionUnderstandingWorker(AIWorker):
    """
    方案理解智能员工

    继承 AIWorker 基础类的全部能力（任务清单、排期、持续工作、任务传递等），
    并在此基础上扩展“方案理解”能力：接收原始方案信息，抽取关键要素，
    生成结构化的 Solution 对象。

    典型职责：
      1. 接收原始方案信息（纯文本、字典或方案文档内容）。
      2. 解析并抽取方案目的、目标、举措、组织、人员、角色、限制、风险、问题等要素。
      3. 输出结构化 Solution 对象，供后续拆解、评估等环节使用。

    :param worker_type: 员工类型标识，固定为 "SolutionUnderstandingWorker"
    :ivar _understood_solutions: 已理解生成的结构化方案缓存
    """

    worker_type: str = Field(default="SolutionUnderstandingWorker", description="智能员工类型标识")

    _understood_solutions: List["Solution"] = PrivateAttr(default_factory=list)

    # ------------------------------------------------------------------
    # 核心能力：方案理解
    # ------------------------------------------------------------------
    def understand(
        self,
        raw_solution_info: Union[str, Dict[str, Any]],
        solution_id: Optional[str] = None,
        name: Optional[str] = None,
        version: str = "1.0",
    ) -> "Solution":
        """
        对原始方案信息进行理解，生成结构化方案信息（Solution 对象）。

        支持两类输入：
          - dict：结构化程度较高的原始信息，按键名直接映射到 Solution 字段。
          - str：非结构化纯文本，按分段/关键词启发式抽取要素。

        :param raw_solution_info: 原始方案信息（字典或纯文本）
        :param solution_id: 指定方案ID；不传则自动生成
        :param name: 指定方案名称；不传则从原始信息中推断
        :param version: 方案版本号，默认 1.0
        :return: 结构化的 Solution 对象
        :raises ValueError: 原始方案信息为空时抛出
        """
        from ...solution import Solution

        if raw_solution_info is None or (isinstance(raw_solution_info, str) and not raw_solution_info.strip()):
            raise ValueError("原始方案信息不能为空")

        logger.info(f"员工{self.name}开始理解原始方案信息...")

        if isinstance(raw_solution_info, dict):
            fields = self._understand_from_dict(raw_solution_info)
        else:
            fields = self._understand_from_text(raw_solution_info)

        resolved_id = solution_id or fields.pop("solution_id", None) or f"SOL_{uuid.uuid4().hex[:12].upper()}"
        resolved_name = name or fields.pop("name", None) or "未命名方案"

        solution = Solution(
            solution_id=resolved_id,
            name=resolved_name,
            version=fields.pop("version", version) or version,
            purpose=fields.get("purpose"),
            objectives=fields.get("objectives", []),
            initiatives=fields.get("initiatives", []),
            working_mechanism=fields.get("working_mechanism"),
            organization=fields.get("organization", []),
            personnel=fields.get("personnel", []),
            roles=fields.get("roles", []),
            work_content=fields.get("work_content"),
            constraints=fields.get("constraints", []),
            risks=fields.get("risks", []),
            issues=fields.get("issues", []),
            other_notes=fields.get("other_notes"),
            description=fields.get("description"),
            owner=fields.get("owner"),
            created_by=self.name,
            tags=fields.get("tags", []),
        )

        self._understood_solutions.append(solution)
        logger.info(
            f"员工{self.name}完成方案理解：{solution.solution_id} {solution.name} "
            f"(目标{len(solution.objectives)}项/举措{len(solution.initiatives)}项)"
        )
        return solution

    def understand_document(self, document: Any) -> "Solution":
        """
        理解方案文档对象（SolutionDocument / SolutionFile），生成结构化方案信息。

        自动汇总文档下所有文件的文本内容后进行理解。

        :param document: 方案文档对象（需含 file_name 及 text_content / files）
        :return: 结构化的 Solution 对象
        """
        name = getattr(document, "file_name", None)
        texts: List[str] = []

        # SolutionDocument 含 files 列表；SolutionFile 直接含 text_content
        files = getattr(document, "files", None)
        if files:
            for f in files:
                if getattr(f, "text_content", None):
                    texts.append(f.text_content)
        elif getattr(document, "text_content", None):
            texts.append(document.text_content)

        raw_text = "\n".join(texts) if texts else (name or "")
        return self.understand(raw_text, name=name)

    def get_understood_solutions(self) -> List["Solution"]:
        """
        获取本员工已理解生成的全部结构化方案。

        :return: Solution 对象列表
        """
        return list(self._understood_solutions)

    # ------------------------------------------------------------------
    # 内部解析逻辑
    # ------------------------------------------------------------------
    def _understand_from_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        从结构化字典中抽取方案要素。

        兼容中英文键名（如 purpose/方案目的、objectives/方案目标 等）。

        :param data: 原始方案信息字典
        :return: 归一化后的方案字段字典
        """
        alias = {
            "solution_id": ["solution_id", "id", "方案ID", "方案编号"],
            "name": ["name", "title", "方案名称", "名称"],
            "version": ["version", "版本", "版本号"],
            "purpose": ["purpose", "方案目的", "目的"],
            "objectives": ["objectives", "方案目标", "目标"],
            "initiatives": ["initiatives", "方案举措", "举措"],
            "working_mechanism": ["working_mechanism", "工作机制"],
            "organization": ["organization", "organizations", "涉及组织", "组织"],
            "personnel": ["personnel", "涉及人员", "人员"],
            "roles": ["roles", "涉及角色", "角色"],
            "work_content": ["work_content", "工作内容"],
            "constraints": ["constraints", "限制条件", "约束"],
            "risks": ["risks", "风险", "风险清单"],
            "issues": ["issues", "问题", "问题清单"],
            "other_notes": ["other_notes", "其他说明", "备注"],
            "description": ["description", "方案描述", "描述"],
            "owner": ["owner", "负责人", "方案负责人"],
            "tags": ["tags", "标签"],
        }
        list_fields = {
            "objectives", "initiatives", "organization", "personnel",
            "roles", "constraints", "risks", "issues", "tags",
        }

        result: Dict[str, Any] = {}
        for field, keys in alias.items():
            value = None
            for k in keys:
                if k in data and data[k] is not None:
                    value = data[k]
                    break
            if value is None:
                continue
            if field in list_fields:
                result[field] = self._to_list(value)
            else:
                result[field] = value if isinstance(value, str) else str(value)
        return result

    def _understand_from_text(self, text: str) -> Dict[str, Any]:
        """
        从非结构化纯文本中启发式抽取方案要素。

        识别常见分节标题（方案名称/目的/目标/举措/组织/人员/角色/工作机制/
        工作内容/限制条件/风险/问题/其他说明），并按行拆分列表型字段。

        :param text: 原始方案纯文本
        :return: 归一化后的方案字段字典
        """
        section_patterns = {
            "name": r"(?:方案名称|名称)",
            "purpose": r"(?:方案目的|目的)",
            "objectives": r"(?:方案目标|目标)",
            "initiatives": r"(?:方案举措|举措)",
            "working_mechanism": r"(?:工作机制)",
            "organization": r"(?:涉及组织|组织)",
            "personnel": r"(?:涉及人员|人员)",
            "roles": r"(?:涉及角色|角色)",
            "work_content": r"(?:工作内容)",
            "constraints": r"(?:限制条件|约束条件|约束)",
            "risks": r"(?:风险清单|风险)",
            "issues": r"(?:问题清单|问题)",
            "other_notes": r"(?:其他说明|其它说明|备注)",
        }
        list_fields = {
            "objectives", "initiatives", "organization",
            "personnel", "roles", "constraints", "risks", "issues",
        }
        scalar_fields = {"name", "purpose", "working_mechanism", "work_content", "other_notes"}

        # 构建“标题 -> 字段名”的匹配，逐行归入当前分节
        title_regex = re.compile(
            r"^\s*(?:\d+[\.、]?\s*)?(" + "|".join(p for p in section_patterns.values()) + r")\s*[:：]?\s*(.*)$"
        )
        field_by_pattern = {v: k for k, v in section_patterns.items()}

        result: Dict[str, Any] = {}
        buffer: Dict[str, List[str]] = {}
        current_field: Optional[str] = None

        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            matched_field = None
            inline_value = ""
            for pat, field in field_by_pattern.items():
                m = re.match(r"^\s*(?:\d+[\.、]?\s*)?" + pat + r"\s*[:：]\s*(.*)$", line)
                if m:
                    matched_field = field
                    inline_value = m.group(1).strip()
                    break
            if matched_field:
                current_field = matched_field
                buffer.setdefault(current_field, [])
                if inline_value:
                    buffer[current_field].append(inline_value)
            elif current_field:
                buffer[current_field].append(line)
            # 未匹配到任何分节的行归入描述
            elif "description" not in result:
                result["description"] = line
            else:
                result["description"] += " " + line

        for field, lines in buffer.items():
            if field in list_fields:
                items: List[str] = []
                for ln in lines:
                    items.extend(self._split_list_line(ln))
                result[field] = [x for x in items if x]
            elif field in scalar_fields:
                result[field] = " ".join(lines).strip()

        return result

    @staticmethod
    def _to_list(value: Any) -> List[str]:
        """将任意值归一化为字符串列表。"""
        if value is None:
            return []
        if isinstance(value, list):
            return [str(v).strip() for v in value if str(v).strip()]
        return SolutionUnderstandingWorker._split_list_line(str(value))

    @staticmethod
    def _split_list_line(line: str) -> List[str]:
        """按常见分隔符（顿号/逗号/分号/换行/项目符号）拆分为列表项。"""
        line = re.sub(r"^\s*(?:\d+[\.、)]|[-*•·]+)\s*", "", line).strip()
        parts = re.split(r"[、,，;；\n]+", line)
        return [p.strip() for p in parts if p.strip()]

    def __str__(self) -> str:
        """返回方案理解智能员工的字符串表示。"""
        return (
            f"SolutionUnderstandingWorker(工号={self.employee_id}, 姓名={self.name}, "
            f"部门={self.department}, 角色={self.roles}, 已理解方案={len(self._understood_solutions)})"
        )


# 延迟导入以更新前向引用（Solution 位于 bo/solution.py）
from ...solution import Solution  # noqa: E402
SolutionUnderstandingWorker.update_forward_refs()


if __name__ == "__main__":
    worker = SolutionUnderstandingWorker(
        employee_id="EMP_SU_001",
        name="方案理解员",
        department="方案理解部",
        roles=["SOLUTION_UNDERSTANDING"],
    )

    print("=== 测试：从纯文本理解方案 ===")
    raw_text = """
    方案名称：企业数字化转型实施方案
    方案目的：推动企业数字化转型，提升整体运营效率
    方案目标：
    1. 实现核心业务流程数字化
    2. 建立数据驱动的决策体系
    3. 提升客户服务体验
    方案举措：引入云平台、建设大数据分析系统、开展员工数字化培训
    涉及组织：研发部、运营部、财务部
    涉及人员：张三、李四、王五
    涉及角色：项目经理、技术负责人、业务顾问
    工作机制：项目制管理，跨部门协作
    工作内容：完成数字化转型的规划、实施与推广
    限制条件：预算有限；时间紧迫
    风险清单：技术选型风险、项目进度风险
    问题清单：系统集成复杂度高、数据迁移难度大
    其他说明：需要高层领导支持
    """
    solution = worker.understand(raw_text)
    print(solution.to_json())

    print("\n=== 测试：从字典理解方案 ===")
    raw_dict = {
        "方案名称": "智能客服升级方案",
        "方案目的": "提升客服自动化水平",
        "方案目标": ["降低人工成本", "缩短响应时间"],
        "涉及组织": "客服部,技术部",
        "风险": ["模型误答风险"],
    }
    solution2 = worker.understand(raw_dict, solution_id="SOL_DEMO_002")
    print(solution2.to_json())

    print(f"\n已理解方案总数：{len(worker.get_understood_solutions())}")
