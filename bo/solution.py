"""方案模块

定义 Solution 和 SolutionDocument 类，用于描述业务方案及其关联文档。
"""
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum
import json


class DocumentType(str, Enum):
    """文档类型枚举"""
    MAIN = "main"
    ATTACHMENT = "attachment"
    REFERENCE = "reference"


class UnderstandingStatus(str, Enum):
    """文档理解状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    UNDERSTOOD = "understood"
    FAILED = "failed"


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


class SolutionDocument(BaseModel):
    """
    方案文档对象类
    
    用于描述一个业务方案文档，包含文档的基本信息和一个或多个方案文件。
    
    :param document_id: 文档唯一标识
    :param file_name: 文档名称（主文档名称）
    :param version: 版本号
    :param document_type: 文档类型（主文档/附件/参考文档）
    :param description: 文档描述
    :param created_by: 创建人
    :param created_at: 创建时间
    :param updated_at: 更新时间
    :param related_solution_ids: 关联的方案对象ID列表
    :param understanding_status: 文档理解状态
    :param metadata: 文档元数据（可选扩展信息）
    :param files: 包含的方案文件对象列表
    
    示例用法：
        doc = SolutionDocument(
            document_id="DOC001",
            file_name="项目实施方案",
            version="1.0",
            document_type="main",
            description="项目实施方案的完整文档集合"
        )
        
        file1 = SolutionFile(
            file_id="FILE001",
            file_name="项目实施方案.docx",
            version="1.0",
            file_type="main",
            text_content="项目实施方案的完整内容...",
            format="docx"
        )
        doc.add_file(file1)
    """
    document_id: str = Field(description="文档唯一标识")
    file_name: str = Field(description="文档名称（主文档名称）")
    version: str = Field(description="版本号")
    document_type: DocumentType = Field(default=DocumentType.ATTACHMENT, description="文档类型")
    description: Optional[str] = Field(default=None, description="文档描述")
    created_by: Optional[str] = Field(default=None, description="创建人")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    related_solution_ids: List[str] = Field(default_factory=list, description="关联的方案对象ID列表")
    understanding_status: UnderstandingStatus = Field(default=UnderstandingStatus.PENDING, description="文档理解状态")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="文档元数据")
    files: List['SolutionFile'] = Field(default_factory=list, description="包含的方案文件对象列表")
    
    @field_validator('version')
    @classmethod
    def version_must_be_valid(cls, v: str) -> str:
        """验证版本号格式"""
        if not v or not v.strip():
            raise ValueError("版本号不能为空")
        return v.strip()
    
    @field_validator('document_id', 'file_name')
    @classmethod
    def id_and_name_must_not_be_empty(cls, v: str) -> str:
        """验证ID和文件名不能为空"""
        if not v or not v.strip():
            raise ValueError("ID和文件名不能为空")
        return v.strip()
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.model_dump(mode='json'), ensure_ascii=False, indent=2)
    
    def add_file(self, file: 'SolutionFile') -> None:
        """
        添加方案文件到文档
        
        :param file: 方案文件对象
        """
        self.files.append(file)
        self.updated_at = datetime.now()
    
    def remove_file(self, file_id: str) -> bool:
        """
        从文档中移除方案文件
        
        :param file_id: 文件ID
        :return: 移除成功返回True
        """
        for i, file in enumerate(self.files):
            if file.file_id == file_id:
                del self.files[i]
                self.updated_at = datetime.now()
                return True
        return False
    
    def get_file_by_id(self, file_id: str) -> Optional['SolutionFile']:
        """
        按文件ID获取文件
        
        :param file_id: 文件ID
        :return: 文件对象，未找到返回None
        """
        for file in self.files:
            if file.file_id == file_id:
                return file
        return None
    
    def get_main_file(self) -> Optional['SolutionFile']:
        """
        获取主文件（file_type为main的文件）
        
        :return: 主文件对象，未找到返回None
        """
        for file in self.files:
            if file.file_type == DocumentType.MAIN:
                return file
        return None
    
    def get_attachment_files(self) -> List['SolutionFile']:
        """
        获取所有附件文件
        
        :return: 附件文件列表
        """
        return [file for file in self.files if file.file_type == DocumentType.ATTACHMENT]
    
    def get_reference_files(self) -> List['SolutionFile']:
        """
        获取所有参考文件
        
        :return: 参考文件列表
        """
        return [file for file in self.files if file.file_type == DocumentType.REFERENCE]
    
    def add_related_solution(self, solution_id: str) -> None:
        """
        添加关联的方案对象
        
        :param solution_id: 方案对象ID
        """
        if solution_id not in self.related_solution_ids:
            self.related_solution_ids.append(solution_id)
            self.updated_at = datetime.now()
    
    def remove_related_solution(self, solution_id: str) -> None:
        """
        移除关联的方案对象
        
        :param solution_id: 方案对象ID
        """
        if solution_id in self.related_solution_ids:
            self.related_solution_ids.remove(solution_id)
            self.updated_at = datetime.now()
    
    def update_files(self, files: List['SolutionFile']) -> None:
        """
        更新文档的文件列表
        
        :param files: 新的文件列表
        """
        self.files = files
        self.updated_at = datetime.now()
    
    def __str__(self) -> str:
        """返回文档的字符串表示"""
        return f"SolutionDocument(ID={self.document_id}, 名称={self.file_name}, 版本={self.version}, 文件数={len(self.files)})"

    def save(self) -> bool:
        """
        保存文档到数据库（新增或更新），级联保存关联的文件
        
        :return: 保存成功返回True
        """
        from data_storage_services.sql_db_services.solution_service import SolutionDocumentService
        
        service = SolutionDocumentService()
        try:
            if service.exists(self.document_id):
                service.update(self)
            else:
                service.create(self)
            return True
        finally:
            service.disconnect()

    def delete(self) -> bool:
        """
        从数据库删除文档，级联删除关联的文件
        
        :return: 删除成功返回True
        """
        from data_storage_services.sql_db_services.solution_service import SolutionDocumentService
        
        service = SolutionDocumentService()
        try:
            return service.delete(self.document_id) == 1
        finally:
            service.disconnect()

    @classmethod
    def get_by_id(cls, document_id: str) -> Optional['SolutionDocument']:
        """
        按文档ID查询文档，同时加载关联的文件
        
        :param document_id: 文档ID
        :return: 文档对象，未找到返回None
        """
        from data_storage_services.sql_db_services.solution_service import SolutionDocumentService
        
        service = SolutionDocumentService()
        try:
            return service.read(document_id)
        finally:
            service.disconnect()

    @classmethod
    def query(cls, where: Dict[str, Any] = None, order_by: str = None, 
              limit: int = None) -> List['SolutionDocument']:
        """
        按条件查询文档，同时加载关联的文件
        
        :param where: 查询条件，如 {"file_name": "方案"}
        :param order_by: 排序字段
        :param limit: 返回数量限制
        :return: 文档列表
        """
        from data_storage_services.sql_db_services.solution_service import SolutionDocumentService
        
        service = SolutionDocumentService()
        try:
            return service.read_all(where=where, order_by=order_by, limit=limit)
        finally:
            service.disconnect()

    @classmethod
    def get_all(cls, order_by: str = None, limit: int = None) -> List['SolutionDocument']:
        """
        全量查询文档，同时加载关联的文件
        
        :param order_by: 排序字段
        :param limit: 返回数量限制
        :return: 文档列表
        """
        from data_storage_services.sql_db_services.solution_service import SolutionDocumentService
        
        service = SolutionDocumentService()
        try:
            return service.read_all(order_by=order_by, limit=limit)
        finally:
            service.disconnect()

    @classmethod
    def get_by_solution(cls, solution_id: str) -> List['SolutionDocument']:
        """
        获取方案的所有文档，同时加载关联的文件
        
        :param solution_id: 方案ID
        :return: 文档列表
        """
        from data_storage_services.sql_db_services.solution_service import SolutionDocumentService
        
        service = SolutionDocumentService()
        try:
            return service.get_by_solution(solution_id)
        finally:
            service.disconnect()

    @classmethod
    def exists(cls, document_id: str) -> bool:
        """
        检查文档是否存在
        
        :param document_id: 文档ID
        :return: 存在返回True
        """
        from data_storage_services.sql_db_services.solution_service import SolutionDocumentService
        
        service = SolutionDocumentService()
        try:
            return service.exists(document_id)
        finally:
            service.disconnect()

    @classmethod
    def count(cls, where: Dict[str, Any] = None) -> int:
        """
        统计文档数量
        
        :param where: 查询条件
        :return: 文档数量
        """
        from data_storage_services.sql_db_services.solution_service import SolutionDocumentService
        
        service = SolutionDocumentService()
        try:
            return service.count(where=where)
        finally:
            service.disconnect()


class SolutionFile(BaseModel):
    """
    方案文件对象类
    
    用于描述一个业务方案文件，包含文件的基本信息和内容。
    与SolutionDocument结构保持一致，用于存储方案相关的文件数据。
    
    :param file_id: 文件唯一标识
    :param document_id: 关联的文档ID
    :param file_name: 文件名
    :param version: 版本号
    :param file_type: 文件类型（主文件/附件/参考文件）
    :param file_content: 文件对象（二进制内容或文件路径）
    :param text_content: 纯文本格式内容描述
    :param description: 文件描述
    :param format: 文件格式（如 PDF、Word、Markdown 等）
    :param size: 文件大小（字节）
    :param created_by: 创建人
    :param created_at: 创建时间
    :param updated_at: 更新时间
    :param related_solution_ids: 关联的方案对象ID列表
    :param understanding_status: 文件理解状态
    :param metadata: 文件元数据（可选扩展信息）
    
    示例用法：
        file = SolutionFile(
            file_id="FILE001",
            document_id="DOC001",
            file_name="项目实施方案.docx",
            version="1.0",
            file_type="main",
            text_content="项目实施方案的完整内容...",
            format="docx",
            related_solution_ids=["SOL001"]
        )
    """
    file_id: str = Field(description="文件唯一标识")
    document_id: Optional[str] = Field(default=None, description="关联的文档ID")
    file_name: str = Field(description="文件名")
    version: str = Field(description="版本号")
    file_type: DocumentType = Field(default=DocumentType.ATTACHMENT, description="文件类型")
    file_content: Optional[Union[bytes, str]] = Field(default=None, description="文件对象")
    text_content: Optional[str] = Field(default=None, description="纯文本格式内容描述")
    description: Optional[str] = Field(default=None, description="文件描述")
    format: Optional[str] = Field(default=None, description="文件格式")
    size: Optional[int] = Field(default=None, description="文件大小（字节）")
    created_by: Optional[str] = Field(default=None, description="创建人")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    related_solution_ids: List[str] = Field(default_factory=list, description="关联的方案对象ID列表")
    understanding_status: UnderstandingStatus = Field(default=UnderstandingStatus.PENDING, description="文件理解状态")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="文件元数据")
    
    @field_validator('version')
    @classmethod
    def version_must_be_valid(cls, v: str) -> str:
        """验证版本号格式"""
        if not v or not v.strip():
            raise ValueError("版本号不能为空")
        return v.strip()
    
    @field_validator('file_id', 'file_name')
    @classmethod
    def id_and_name_must_not_be_empty(cls, v: str) -> str:
        """验证ID和文件名不能为空"""
        if not v or not v.strip():
            raise ValueError("ID和文件名不能为空")
        return v.strip()
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.model_dump(mode='json'), ensure_ascii=False, indent=2)
    
    def update_content(self, text_content: str, file_content: Optional[Union[bytes, str]] = None) -> None:
        """
        更新文件内容
        
        :param text_content: 纯文本内容
        :param file_content: 文件对象（可选）
        """
        self.text_content = text_content
        if file_content is not None:
            self.file_content = file_content
        self.updated_at = datetime.now()
    
    def add_related_solution(self, solution_id: str) -> None:
        """
        添加关联的方案对象
        
        :param solution_id: 方案对象ID
        """
        if solution_id not in self.related_solution_ids:
            self.related_solution_ids.append(solution_id)
            self.updated_at = datetime.now()
    
    def remove_related_solution(self, solution_id: str) -> None:
        """
        移除关联的方案对象
        
        :param solution_id: 方案对象ID
        """
        if solution_id in self.related_solution_ids:
            self.related_solution_ids.remove(solution_id)
            self.updated_at = datetime.now()
    
    def __str__(self) -> str:
        """返回文件的字符串表示"""
        return f"SolutionFile(ID={self.file_id}, 文件名={self.file_name}, 版本={self.version}, 类型={self.file_type})"

    def save(self) -> bool:
        """
        保存文件到数据库（新增或更新）
        
        数据库配置从 db_config.json 文件读取。
        
        :return: 保存成功返回True
        """
        from data_storage_services.sql_db_services.solution_service import SolutionFileService
        
        service = SolutionFileService()
        try:
            if service.exists(self.file_id):
                service.update(self)
            else:
                service.create(self)
            return True
        finally:
            service.disconnect()

    def delete(self) -> bool:
        """
        从数据库删除文件
        
        数据库配置从 db_config.json 文件读取。
        
        :return: 删除成功返回True
        """
        from data_storage_services.sql_db_services.solution_service import SolutionFileService
        
        service = SolutionFileService()
        try:
            return service.delete(self.file_id) == 1
        finally:
            service.disconnect()

    @classmethod
    def get_by_id(cls, file_id: str) -> Optional['SolutionFile']:
        """
        按文件ID查询文件
        
        数据库配置从 db_config.json 文件读取。
        
        :param file_id: 文件ID
        :return: 文件对象，未找到返回None
        """
        from data_storage_services.sql_db_services.solution_service import SolutionFileService
        
        service = SolutionFileService()
        try:
            return service.read(file_id)
        finally:
            service.disconnect()

    @classmethod
    def query(cls, where: Dict[str, Any] = None, order_by: str = None, 
              limit: int = None) -> List['SolutionFile']:
        """
        按条件查询文件
        
        数据库配置从 db_config.json 文件读取。
        
        :param where: 查询条件，如 {"file_name": "方案"}
        :param order_by: 排序字段
        :param limit: 返回数量限制
        :return: 文件列表
        """
        from data_storage_services.sql_db_services.solution_service import SolutionFileService
        
        service = SolutionFileService()
        try:
            return service.read_all(where=where, order_by=order_by, limit=limit)
        finally:
            service.disconnect()

    @classmethod
    def get_all(cls, order_by: str = None, limit: int = None) -> List['SolutionFile']:
        """
        全量查询文件
        
        数据库配置从 db_config.json 文件读取。
        
        :param order_by: 排序字段
        :param limit: 返回数量限制
        :return: 文件列表
        """
        from data_storage_services.sql_db_services.solution_service import SolutionFileService
        
        service = SolutionFileService()
        try:
            return service.read_all(order_by=order_by, limit=limit)
        finally:
            service.disconnect()

    @classmethod
    def get_by_solution(cls, solution_id: str) -> List['SolutionFile']:
        """
        获取方案的所有文件
        
        数据库配置从 db_config.json 文件读取。
        
        :param solution_id: 方案ID
        :return: 文件列表
        """
        from data_storage_services.sql_db_services.solution_service import SolutionFileService
        
        service = SolutionFileService()
        try:
            return service.get_by_solution(solution_id)
        finally:
            service.disconnect()

    @classmethod
    def exists(cls, file_id: str) -> bool:
        """
        检查文件是否存在
        
        数据库配置从 db_config.json 文件读取。
        
        :param file_id: 文件ID
        :return: 存在返回True
        """
        from data_storage_services.sql_db_services.solution_service import SolutionFileService
        
        service = SolutionFileService()
        try:
            return service.exists(file_id)
        finally:
            service.disconnect()

    @classmethod
    def count(cls, where: Dict[str, Any] = None) -> int:
        """
        统计文件数量
        
        数据库配置从 db_config.json 文件读取。
        
        :param where: 查询条件
        :return: 文件数量
        """
        from data_storage_services.sql_db_services.solution_service import SolutionFileService
        
        service = SolutionFileService()
        try:
            return service.count(where=where)
        finally:
            service.disconnect()


class Solution(BaseModel):
    """
    方案对象类
    
    用于描述一个业务方案，包含方案的完整信息。
    
    :param solution_id: 方案唯一标识
    :param name: 方案名称
    :param version: 版本号
    :param status: 方案状态
    :param priority: 方案优先级
    :param purpose: 方案目的
    :param objectives: 方案目标列表
    :param initiatives: 方案举措列表
    :param working_mechanism: 工作机制描述
    :param organization: 涉及组织（组织ID或名称列表）
    :param personnel: 涉及人员（人员ID或姓名列表）
    :param roles: 涉及角色（角色名称列表）
    :param work_content: 工作内容描述
    :param constraints: 限制条件列表
    :param risks: 风险列表
    :param issues: 问题列表
    :param other_notes: 其他说明
    :param main_document_id: 主文档对象ID
    :param auxiliary_document_ids: 辅助文档对象ID列表
    :param description: 方案描述
    :param owner: 方案负责人
    :param created_by: 创建人
    :param created_at: 创建时间
    :param updated_at: 更新时间
    :param effective_date: 生效日期
    :param expiry_date: 到期日期
    :param tags: 标签列表
    :param metadata: 方案元数据（可选扩展信息）
    
    示例用法：
        solution = Solution(
            solution_id="SOL001",
            name="数字化转型实施方案",
            version="1.0",
            status="draft",
            purpose="推动企业数字化转型",
            objectives=["目标1", "目标2"],
            initiatives=["举措1", "举措2"],
            main_document_id="DOC001"
        )
    """
    solution_id: str = Field(description="方案唯一标识")
    name: str = Field(description="方案名称")
    version: str = Field(description="版本号")
    status: SolutionStatus = Field(default=SolutionStatus.DRAFT, description="方案状态")
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
    main_document_id: Optional[str] = Field(default=None, description="主文档对象ID")
    auxiliary_document_ids: List[str] = Field(default_factory=list, description="辅助文档对象ID列表")
    description: Optional[str] = Field(default=None, description="方案描述")
    owner: Optional[str] = Field(default=None, description="方案负责人")
    created_by: Optional[str] = Field(default=None, description="创建人")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    effective_date: Optional[datetime] = Field(default=None, description="生效日期")
    expiry_date: Optional[datetime] = Field(default=None, description="到期日期")
    tags: List[str] = Field(default_factory=list, description="标签列表")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="方案元数据")
    
    @field_validator('solution_id', 'name', 'version')
    @classmethod
    def required_fields_must_not_be_empty(cls, v: str) -> str:
        """验证必填字段不能为空"""
        if not v or not v.strip():
            raise ValueError("方案ID、名称和版本号不能为空")
        return v.strip()
    
    @field_validator('effective_date', 'expiry_date', mode='before')
    @classmethod
    def parse_datetime(cls, v: Any) -> datetime:
        """解析日期时间字符串"""
        if isinstance(v, str):
            return datetime.fromisoformat(v.replace('Z', '+00:00').replace(' ', 'T'))
        return v
    
    @model_validator(mode='after')
    def validate_dates(self) -> 'Solution':
        """验证日期逻辑"""
        if self.effective_date and self.expiry_date:
            if self.effective_date > self.expiry_date:
                raise ValueError("生效日期不能晚于到期日期")
        return self
    
    @model_validator(mode='after')
    def validate_document_association(self) -> 'Solution':
        """验证文档关联约束"""
        if self.auxiliary_document_ids and not self.main_document_id:
            raise ValueError("关联辅助文档前必须先关联主文档")
        return self
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.model_dump(mode='json'), ensure_ascii=False, indent=2)
    
    def add_objective(self, objective: str) -> None:
        """
        添加方案目标
        
        :param objective: 目标描述
        """
        if objective and objective.strip() not in self.objectives:
            self.objectives.append(objective.strip())
            self.updated_at = datetime.now()
    
    def remove_objective(self, objective: str) -> None:
        """
        移除方案目标
        
        :param objective: 目标描述
        """
        if objective in self.objectives:
            self.objectives.remove(objective)
            self.updated_at = datetime.now()
    
    def add_initiative(self, initiative: str) -> None:
        """
        添加方案举措
        
        :param initiative: 举措描述
        """
        if initiative and initiative.strip() not in self.initiatives:
            self.initiatives.append(initiative.strip())
            self.updated_at = datetime.now()
    
    def remove_initiative(self, initiative: str) -> None:
        """
        移除方案举措
        
        :param initiative: 举措描述
        """
        if initiative in self.initiatives:
            self.initiatives.remove(initiative)
            self.updated_at = datetime.now()
    
    def add_constraint(self, constraint: str) -> None:
        """
        添加限制条件
        
        :param constraint: 限制条件描述
        """
        if constraint and constraint.strip() not in self.constraints:
            self.constraints.append(constraint.strip())
            self.updated_at = datetime.now()
    
    def add_risk(self, risk: str) -> None:
        """
        添加风险
        
        :param risk: 风险描述
        """
        if risk and risk.strip() not in self.risks:
            self.risks.append(risk.strip())
            self.updated_at = datetime.now()
    
    def add_issue(self, issue: str) -> None:
        """
        添加问题
        
        :param issue: 问题描述
        """
        if issue and issue.strip() not in self.issues:
            self.issues.append(issue.strip())
            self.updated_at = datetime.now()
    
    def set_main_document(self, document_id: str) -> None:
        """
        设置主文档
        
        :param document_id: 主文档对象ID
        """
        self.main_document_id = document_id
        self.updated_at = datetime.now()
    
    def add_auxiliary_document(self, document_id: str) -> None:
        """
        添加辅助文档
        
        :param document_id: 辅助文档对象ID
        :raises ValueError: 如果未设置主文档
        """
        if not self.main_document_id:
            raise ValueError("请先设置主文档")
        if document_id not in self.auxiliary_document_ids:
            self.auxiliary_document_ids.append(document_id)
            self.updated_at = datetime.now()
    
    def remove_auxiliary_document(self, document_id: str) -> None:
        """
        移除辅助文档
        
        :param document_id: 辅助文档对象ID
        """
        if document_id in self.auxiliary_document_ids:
            self.auxiliary_document_ids.remove(document_id)
            self.updated_at = datetime.now()
    
    def add_tag(self, tag: str) -> None:
        """
        添加标签
        
        :param tag: 标签名称
        """
        if tag and tag.strip() not in self.tags:
            self.tags.append(tag.strip())
            self.updated_at = datetime.now()
    
    def get_document_count(self) -> int:
        """
        获取关联文档总数
        
        :return: 主文档数 + 辅助文档数
        """
        count = 0
        if self.main_document_id:
            count += 1
        count += len(self.auxiliary_document_ids)
        return count
    
    def get_summary(self) -> Dict[str, Any]:
        """
        获取方案摘要信息
        
        :return: 方案摘要字典
        """
        return {
            "solution_id": self.solution_id,
            "name": self.name,
            "version": self.version,
            "status": self.status,
            "priority": self.priority,
            "owner": self.owner,
            "objectives_count": len(self.objectives),
            "initiatives_count": len(self.initiatives),
            "document_count": self.get_document_count(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    def __str__(self) -> str:
        """返回方案的字符串表示"""
        return (
            f"Solution(ID={self.solution_id}, 名称={self.name}, 版本={self.version}, "
            f"状态={self.status}, 优先级={self.priority}, 负责人={self.owner})"
        )

    def save(self) -> bool:
        """
        保存方案到数据库（新增或更新）
        
        数据库配置从 db_config.json 文件读取。
        
        :return: 保存成功返回True
        """
        from data_storage_services.sql_db_services.solution_service import SolutionService
        
        service = SolutionService()
        try:
            if service.exists(self.solution_id):
                service.update(self)
            else:
                service.create(self)
            return True
        finally:
            service.disconnect()

    def delete(self) -> bool:
        """
        从数据库删除方案
        
        数据库配置从 db_config.json 文件读取。
        
        :return: 删除成功返回True
        """
        from data_storage_services.sql_db_services.solution_service import SolutionService
        
        service = SolutionService()
        try:
            return service.delete(self.solution_id) == 1
        finally:
            service.disconnect()

    @classmethod
    def get_by_id(cls, solution_id: str) -> Optional['Solution']:
        """
        按方案ID查询方案
        
        数据库配置从 db_config.json 文件读取。
        
        :param solution_id: 方案ID
        :return: 方案对象，未找到返回None
        """
        from data_storage_services.sql_db_services.solution_service import SolutionService
        
        service = SolutionService()
        try:
            return service.read(solution_id)
        finally:
            service.disconnect()

    @classmethod
    def query(cls, where: Dict[str, Any] = None, order_by: str = None, 
              limit: int = None) -> List['Solution']:
        """
        按条件查询方案
        
        数据库配置从 db_config.json 文件读取。
        
        :param where: 查询条件，如 {"status": "active"}
        :param order_by: 排序字段
        :param limit: 返回数量限制
        :return: 方案列表
        """
        from data_storage_services.sql_db_services.solution_service import SolutionService
        
        service = SolutionService()
        try:
            return service.read_all(where=where, order_by=order_by, limit=limit)
        finally:
            service.disconnect()

    @classmethod
    def get_all(cls, order_by: str = None, limit: int = None) -> List['Solution']:
        """
        全量查询方案
        
        数据库配置从 db_config.json 文件读取。
        
        :param order_by: 排序字段
        :param limit: 返回数量限制
        :return: 方案列表
        """
        from data_storage_services.sql_db_services.solution_service import SolutionService
        
        service = SolutionService()
        try:
            return service.read_all(order_by=order_by, limit=limit)
        finally:
            service.disconnect()

    @classmethod
    def get_by_status(cls, status: SolutionStatus) -> List['Solution']:
        """
        按状态查询方案
        
        数据库配置从 db_config.json 文件读取。
        
        :param status: 方案状态
        :return: 方案列表
        """
        from data_storage_services.sql_db_services.solution_service import SolutionService
        
        service = SolutionService()
        try:
            return service.get_by_status(status)
        finally:
            service.disconnect()

    @classmethod
    def get_by_owner(cls, owner: str) -> List['Solution']:
        """
        按负责人查询方案
        
        数据库配置从 db_config.json 文件读取。
        
        :param owner: 负责人
        :return: 方案列表
        """
        from data_storage_services.sql_db_services.solution_service import SolutionService
        
        service = SolutionService()
        try:
            return service.get_by_owner(owner)
        finally:
            service.disconnect()

    @classmethod
    def search_by_name(cls, keyword: str) -> List['Solution']:
        """
        按名称模糊查询方案
        
        数据库配置从 db_config.json 文件读取。
        
        :param keyword: 关键词
        :return: 方案列表
        """
        from data_storage_services.sql_db_services.solution_service import SolutionService
        
        service = SolutionService()
        try:
            return service.search_by_name(keyword)
        finally:
            service.disconnect()

    @classmethod
    def exists(cls, solution_id: str) -> bool:
        """
        检查方案是否存在
        
        数据库配置从 db_config.json 文件读取。
        
        :param solution_id: 方案ID
        :return: 存在返回True
        """
        from data_storage_services.sql_db_services.solution_service import SolutionService
        
        service = SolutionService()
        try:
            return service.exists(solution_id)
        finally:
            service.disconnect()

    @classmethod
    def count(cls, where: Dict[str, Any] = None) -> int:
        """
        统计方案数量
        
        数据库配置从 db_config.json 文件读取。
        
        :param where: 查询条件
        :return: 方案数量
        """
        from data_storage_services.sql_db_services.solution_service import SolutionService
        
        service = SolutionService()
        try:
            return service.count(where=where)
        finally:
            service.disconnect()


if __name__ == "__main__":
    print("=== 测试方案文档对象 ===")
    doc = SolutionDocument(
        document_id="DOC001",
        file_name="项目实施方案.docx",
        version="1.0",
        document_type=DocumentType.MAIN,
        text_content="这是项目实施方案的完整内容...",
        format="docx",
        size=1024000,
        created_by="管理员",
        related_solution_ids=["SOL001"]
    )
    print(doc)
    print(doc.to_json())
    
    print("\n=== 测试方案对象 ===")
    solution = Solution(
        solution_id="SOL001",
        name="数字化转型实施方案",
        version="1.0",
        status=SolutionStatus.DRAFT,
        priority=SolutionPriority.HIGH,
        purpose="推动企业数字化转型，提升运营效率",
        objectives=[
            "实现业务流程数字化",
            "建立数据驱动决策体系",
            "提升客户体验"
        ],
        initiatives=[
            "引入云计算平台",
            "建设大数据分析系统",
            "培训员工数字化技能"
        ],
        working_mechanism="项目制管理，跨部门协作",
        organization=["研发部", "运营部", "财务部"],
        personnel=["张三", "李四", "王五"],
        roles=["项目经理", "技术负责人", "业务顾问"],
        work_content="完成数字化转型的规划、实施和推广",
        constraints=[
            "预算限制",
            "技术资源有限",
            "时间紧迫"
        ],
        risks=[
            "技术选型风险",
            "项目进度风险",
            "人员流失风险"
        ],
        issues=[
            "系统集成复杂度高",
            "数据迁移难度大"
        ],
        other_notes="需要高层领导支持",
        main_document_id="DOC001",
        auxiliary_document_ids=["DOC002", "DOC003"],
        description="企业数字化转型的全面实施方案",
        owner="张三",
        created_by="李四",
        effective_date="2026-07-01",
        expiry_date="2027-12-31",
        tags=["数字化", "转型", "战略"]
    )
    print(solution)
    print(json.dumps(solution.get_summary(), ensure_ascii=False, indent=2))
    print(solution.to_json())