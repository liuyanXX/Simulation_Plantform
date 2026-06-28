"""方案服务类

提供方案对象的数据库CRUD操作服务。
"""

import json
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from .base_service import SQLDatabaseService
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from bo.solution import Solution, SolutionDocument, SolutionFile, SolutionStatus, SolutionPriority, DocumentType, UnderstandingStatus


class SolutionService(SQLDatabaseService[Solution]):
    """
    方案服务类
    
    提供方案对象的数据库CRUD操作服务。
    """
    
    def _get_table_name(self) -> str:
        return "solutions"
    
    def _get_id_field(self) -> str:
        return "solution_id"
    
    def _get_id_value(self, obj: Solution) -> str:
        return obj.solution_id
    
    def _to_db_dict(self, obj: Solution) -> Dict[str, Any]:
        """将方案对象转换为数据库字典"""
        return {
            "solution_id": obj.solution_id,
            "name": obj.name,
            "version": obj.version,
            "status": obj.status.value if isinstance(obj.status, SolutionStatus) else obj.status,
            "priority": obj.priority.value if isinstance(obj.priority, SolutionPriority) else obj.priority,
            "purpose": obj.purpose,
            "objectives": json.dumps(obj.objectives, ensure_ascii=False) if obj.objectives else None,
            "initiatives": json.dumps(obj.initiatives, ensure_ascii=False) if obj.initiatives else None,
            "working_mechanism": obj.working_mechanism,
            "organization": json.dumps(obj.organization, ensure_ascii=False) if obj.organization else None,
            "personnel": json.dumps(obj.personnel, ensure_ascii=False) if obj.personnel else None,
            "roles": json.dumps(obj.roles, ensure_ascii=False) if obj.roles else None,
            "work_content": obj.work_content,
            "constraints": json.dumps(obj.constraints, ensure_ascii=False) if obj.constraints else None,
            "risks": json.dumps(obj.risks, ensure_ascii=False) if obj.risks else None,
            "issues": json.dumps(obj.issues, ensure_ascii=False) if obj.issues else None,
            "other_notes": obj.other_notes,
            "main_document_id": obj.main_document_id,
            "auxiliary_document_ids": json.dumps(obj.auxiliary_document_ids, ensure_ascii=False) if obj.auxiliary_document_ids else None,
            "description": obj.description,
            "owner": obj.owner,
            "created_by": obj.created_by,
            "created_at": obj.created_at.isoformat() if isinstance(obj.created_at, datetime) else obj.created_at,
            "updated_at": obj.updated_at.isoformat() if isinstance(obj.updated_at, datetime) else obj.updated_at,
            "effective_date": obj.effective_date.isoformat() if obj.effective_date else None,
            "expiry_date": obj.expiry_date.isoformat() if obj.expiry_date else None,
            "tags": json.dumps(obj.tags, ensure_ascii=False) if obj.tags else None,
            "metadata": json.dumps(obj.metadata, ensure_ascii=False) if obj.metadata else None
        }
    
    def _from_db_dict(self, data: Dict[str, Any]) -> Solution:
        """将数据库字典转换为方案对象"""
        def parse_json(value, default=None):
            if value is None:
                return default or []
            if isinstance(value, str):
                try:
                    return json.loads(value)
                except:
                    return value
            return value
        
        def parse_datetime(value):
            if value is None:
                return None
            if isinstance(value, str):
                return datetime.fromisoformat(value.replace('Z', '+00:00'))
            return value
        
        return Solution(
            solution_id=data["solution_id"],
            name=data["name"],
            version=data["version"],
            status=SolutionStatus(data["status"]) if data.get("status") else SolutionStatus.DRAFT,
            priority=SolutionPriority(data["priority"]) if data.get("priority") else SolutionPriority.MEDIUM,
            purpose=data.get("purpose"),
            objectives=parse_json(data.get("objectives"), []),
            initiatives=parse_json(data.get("initiatives"), []),
            working_mechanism=data.get("working_mechanism"),
            organization=parse_json(data.get("organization"), []),
            personnel=parse_json(data.get("personnel"), []),
            roles=parse_json(data.get("roles"), []),
            work_content=data.get("work_content"),
            constraints=parse_json(data.get("constraints"), []),
            risks=parse_json(data.get("risks"), []),
            issues=parse_json(data.get("issues"), []),
            other_notes=data.get("other_notes"),
            main_document_id=data.get("main_document_id"),
            auxiliary_document_ids=parse_json(data.get("auxiliary_document_ids"), []),
            description=data.get("description"),
            owner=data.get("owner"),
            created_by=data.get("created_by"),
            created_at=parse_datetime(data.get("created_at")) or datetime.now(),
            updated_at=parse_datetime(data.get("updated_at")) or datetime.now(),
            effective_date=parse_datetime(data.get("effective_date")),
            expiry_date=parse_datetime(data.get("expiry_date")),
            tags=parse_json(data.get("tags"), []),
            metadata=(parse_json(data.get("metadata")) or None) if isinstance(parse_json(data.get("metadata"), {}), dict) else None
        )
    
    def list(self, page: int = 1, page_size: int = 10, keyword: str = "") -> List[Solution]:
        """
        分页查询方案列表
        
        :param page: 页码（从1开始）
        :param page_size: 每页条数
        :param keyword: 关键词（模糊匹配名称）
        :return: 方案列表
        """
        all_solutions = self.read_all()
        
        if keyword:
            all_solutions = [s for s in all_solutions if keyword.lower() in s.name.lower()]
        
        all_solutions.sort(key=lambda x: x.created_at or datetime.now(), reverse=True)
        
        start = (page - 1) * page_size
        end = start + page_size
        
        return all_solutions[start:end]
    
    def count(self, keyword: str = "") -> int:
        """
        统计方案数量
        
        :param keyword: 关键词（可选）
        :return: 方案数量
        """
        all_solutions = self.read_all()
        
        if keyword:
            all_solutions = [s for s in all_solutions if keyword.lower() in s.name.lower()]
        
        return len(all_solutions)
    
    def count_documents(self, solution_id: str) -> int:
        """
        统计方案关联的文档数量
        
        :param solution_id: 方案ID
        :return: 文档数量
        """
        doc_service = SolutionDocumentService()
        docs = doc_service.get_by_solution(solution_id)
        count = len(docs)
        doc_service.disconnect()
        return count
    
    def get_documents(self, solution_id: str) -> List[SolutionDocument]:
        """
        获取方案关联的所有文档
        
        :param solution_id: 方案ID
        :return: 文档列表
        """
        doc_service = SolutionDocumentService()
        docs = doc_service.get_by_solution(solution_id)
        doc_service.disconnect()
        return docs
    
    def create_document(self, document: SolutionDocument):
        """
        创建方案文档
        
        :param document: 文档对象
        """
        doc_service = SolutionDocumentService()
        doc_service.create(document)
        doc_service.disconnect()
    
    def get_by_status(self, status: SolutionStatus) -> List[Solution]:
        """
        按状态查询方案
        
        :param status: 方案状态
        :return: 方案列表
        """
        return self.read_all(where={"status": status.value})
    
    def get_by_owner(self, owner: str) -> List[Solution]:
        """
        按负责人查询方案
        
        :param owner: 负责人
        :return: 方案列表
        """
        return self.read_all(where={"owner": owner})
    
    def search_by_name(self, keyword: str) -> List[Solution]:
        """
        按名称模糊查询方案
        
        :param keyword: 关键词
        :return: 方案列表
        """
        all_solutions = self.read_all()
        return [s for s in all_solutions if keyword.lower() in s.name.lower()]


class SolutionDocumentService(SQLDatabaseService[SolutionDocument]):
    """
    方案文档服务类
    
    提供方案文档对象的数据库CRUD操作服务，支持级联操作。
    """
    
    def _get_table_name(self) -> str:
        return "solution_documents"
    
    def _get_id_field(self) -> str:
        return "document_id"
    
    def _get_id_value(self, obj: SolutionDocument) -> str:
        return obj.document_id
    
    def _to_db_dict(self, obj: SolutionDocument) -> Dict[str, Any]:
        """将文档对象转换为数据库字典（不包含files字段）"""
        return {
            "document_id": obj.document_id,
            "file_name": obj.file_name,
            "version": obj.version,
            "document_type": obj.document_type.value if isinstance(obj.document_type, DocumentType) else obj.document_type,
            "description": obj.description,
            "created_by": obj.created_by,
            "created_at": obj.created_at.isoformat() if isinstance(obj.created_at, datetime) else obj.created_at,
            "updated_at": obj.updated_at.isoformat() if isinstance(obj.updated_at, datetime) else obj.updated_at,
            "related_solution_ids": json.dumps(obj.related_solution_ids, ensure_ascii=False) if obj.related_solution_ids else None,
            "understanding_status": obj.understanding_status.value if isinstance(obj.understanding_status, UnderstandingStatus) else obj.understanding_status,
            "metadata": json.dumps(obj.metadata, ensure_ascii=False) if obj.metadata else None
        }
    
    def _from_db_dict(self, data: Dict[str, Any]) -> SolutionDocument:
        """将数据库字典转换为文档对象（不包含files，files通过read方法加载）"""
        def parse_json(value, default=None):
            if value is None:
                return default or []
            if isinstance(value, str):
                try:
                    return json.loads(value)
                except:
                    return value
            return value
        
        def parse_datetime(value):
            if value is None:
                return None
            if isinstance(value, str):
                return datetime.fromisoformat(value.replace('Z', '+00:00'))
            return value
        
        return SolutionDocument(
            document_id=data["document_id"],
            file_name=data["file_name"],
            version=data["version"],
            document_type=DocumentType(data["document_type"]) if data.get("document_type") else DocumentType.ATTACHMENT,
            description=data.get("description"),
            created_by=data.get("created_by"),
            created_at=parse_datetime(data.get("created_at")) or datetime.now(),
            updated_at=parse_datetime(data.get("updated_at")) or datetime.now(),
            related_solution_ids=parse_json(data.get("related_solution_ids"), []),
            understanding_status=UnderstandingStatus(data.get("understanding_status")) if data.get("understanding_status") else UnderstandingStatus.PENDING,
            metadata=parse_json(data.get("metadata")),
            files=[]
        )
    
    def _load_files(self, document_id: str) -> List[SolutionFile]:
        """加载文档关联的所有文件"""
        file_service = SolutionFileService()
        files = file_service.read_all(where={"document_id": document_id})
        file_service.disconnect()
        return files
    
    def create(self, obj: SolutionDocument) -> bool:
        """
        创建文档记录，级联创建关联的文件
        
        :param obj: 文档对象
        :return: 创建成功返回True
        """
        if super().create(obj):
            # 级联创建关联文件
            file_service = SolutionFileService()
            for file in obj.files:
                file.updated_at = datetime.now()
                file_service.create(file)
            file_service.disconnect()
            return True
        return False
    
    def read(self, document_id: str) -> Optional[SolutionDocument]:
        """
        读取文档记录，同时加载关联的文件
        
        :param document_id: 文档ID
        :return: 文档对象，未找到返回None
        """
        doc = super().read(document_id)
        if doc:
            doc.files = self._load_files(document_id)
        return doc
    
    def update(self, obj: SolutionDocument) -> bool:
        """
        更新文档记录，级联更新关联的文件
        
        :param obj: 文档对象
        :return: 更新成功返回True
        """
        if super().update(obj):
            # 级联更新关联文件
            file_service = SolutionFileService()
            
            # 获取现有文件列表
            existing_files = file_service.read_all(where={"document_id": obj.document_id})
            existing_file_ids = {f.file_id for f in existing_files}
            
            # 更新或创建文件
            for file in obj.files:
                file.document_id = obj.document_id
                file.updated_at = datetime.now()
                if file.file_id in existing_file_ids:
                    file_service.update(file)
                    existing_file_ids.remove(file.file_id)
                else:
                    file_service.create(file)
            
            # 删除不在新列表中的文件
            for file_id in existing_file_ids:
                file_service.delete(file_id)
            
            file_service.disconnect()
            return True
        return False
    
    def delete(self, document_id: str) -> int:
        """
        删除文档记录，级联删除关联的文件
        
        :param document_id: 文档ID
        :return: 删除的记录数
        """
        # 先删除关联的文件
        file_service = SolutionFileService()
        existing_files = file_service.read_all(where={"document_id": document_id})
        for file in existing_files:
            file_service.delete(file.file_id)
        file_service.disconnect()
        
        # 删除文档
        return super().delete(document_id)
    
    def read_all(self, where: Dict[str, Any] = None, order_by: str = None, 
                 limit: int = None) -> List[SolutionDocument]:
        """
        读取所有文档记录，同时加载关联的文件
        
        :param where: 查询条件
        :param order_by: 排序字段
        :param limit: 返回数量限制
        :return: 文档列表
        """
        docs = super().read_all(where=where, order_by=order_by, limit=limit)
        for doc in docs:
            doc.files = self._load_files(doc.document_id)
        return docs
    
    def get_by_solution(self, solution_id: str) -> List[SolutionDocument]:
        """
        获取方案的所有文档
        
        :param solution_id: 方案ID
        :return: 文档列表
        """
        all_docs = self.read_all()
        result = []
        for doc in all_docs:
            if doc.related_solution_ids and solution_id in doc.related_solution_ids:
                result.append(doc)
        return result
    
    def list(self, page: int = 1, page_size: int = 10, keyword: str = "") -> List[SolutionDocument]:
        """
        分页查询文档列表
        
        :param page: 页码（从1开始）
        :param page_size: 每页条数
        :param keyword: 关键词（模糊匹配文件名）
        :return: 文档列表
        """
        all_docs = self.read_all()
        
        if keyword:
            all_docs = [d for d in all_docs if keyword.lower() in d.file_name.lower()]
        
        all_docs.sort(key=lambda x: x.created_at or datetime.now(), reverse=True)
        
        start = (page - 1) * page_size
        end = start + page_size
        
        return all_docs[start:end]
    
    def count(self, keyword: str = "") -> int:
        """
        统计文档数量
        
        :param keyword: 关键词（可选）
        :return: 文档数量
        """
        all_docs = self.read_all()
        
        if keyword:
            all_docs = [d for d in all_docs if keyword.lower() in d.file_name.lower()]
        
        return len(all_docs)
    
    def get_pending_documents(self, page: int = 1, page_size: int = 5) -> List[SolutionDocument]:
        """
        获取待理解的文档列表（分页）
        
        :param page: 页码
        :param page_size: 每页条数
        :return: 待理解文档列表
        """
        all_docs = self.read_all()
        pending_docs = [d for d in all_docs if d.understanding_status == UnderstandingStatus.PENDING]
        pending_docs.sort(key=lambda x: x.created_at or datetime.now(), reverse=True)
        
        start = (page - 1) * page_size
        end = start + page_size
        
        return pending_docs[start:end]
    
    def count_pending_documents(self) -> int:
        """
        统计待理解文档数量
        
        :return: 待理解文档数量
        """
        all_docs = self.read_all()
        return len([d for d in all_docs if d.understanding_status == UnderstandingStatus.PENDING])
    
    def update_understanding_status(self, document_id: str, status: UnderstandingStatus):
        """
        更新文档理解状态
        
        :param document_id: 文档ID
        :param status: 理解状态
        """
        doc = self.read(document_id)
        if doc:
            doc.understanding_status = status
            doc.updated_at = datetime.now()
            self.update(doc)


class SolutionFileService(SQLDatabaseService[SolutionFile]):
    """
    方案文件服务类
    
    提供方案文件对象的数据库CRUD操作服务。
    """
    
    def _get_table_name(self) -> str:
        return "solution_files"
    
    def _get_id_field(self) -> str:
        return "file_id"
    
    def _get_id_value(self, obj: SolutionFile) -> str:
        return obj.file_id
    
    def _to_db_dict(self, obj: SolutionFile) -> Dict[str, Any]:
        """将文件对象转换为数据库字典"""
        return {
            "file_id": obj.file_id,
            "document_id": obj.document_id,
            "file_name": obj.file_name,
            "version": obj.version,
            "file_type": obj.file_type.value if isinstance(obj.file_type, DocumentType) else obj.file_type,
            "file_content": obj.file_content if isinstance(obj.file_content, bytes) else None,
            "text_content": obj.text_content,
            "description": obj.description,
            "format": obj.format,
            "size": obj.size,
            "created_by": obj.created_by,
            "created_at": obj.created_at.isoformat() if isinstance(obj.created_at, datetime) else obj.created_at,
            "updated_at": obj.updated_at.isoformat() if isinstance(obj.updated_at, datetime) else obj.updated_at,
            "related_solution_ids": json.dumps(obj.related_solution_ids, ensure_ascii=False) if obj.related_solution_ids else None,
            "understanding_status": obj.understanding_status.value if isinstance(obj.understanding_status, UnderstandingStatus) else obj.understanding_status,
            "metadata": json.dumps(obj.metadata, ensure_ascii=False) if obj.metadata else None
        }
    
    def _from_db_dict(self, data: Dict[str, Any]) -> SolutionFile:
        """将数据库字典转换为文件对象"""
        def parse_json(value, default=None):
            if value is None:
                return default or []
            if isinstance(value, str):
                try:
                    return json.loads(value)
                except:
                    return value
            return value
        
        def parse_datetime(value):
            if value is None:
                return None
            if isinstance(value, str):
                return datetime.fromisoformat(value.replace('Z', '+00:00'))
            return value
        
        metadata = parse_json(data.get("metadata"))
        if isinstance(metadata, list) and len(metadata) == 0:
            metadata = None
        
        return SolutionFile(
            file_id=data["file_id"],
            document_id=data.get("document_id"),
            file_name=data["file_name"],
            version=data["version"],
            file_type=DocumentType(data["file_type"]) if data.get("file_type") else DocumentType.ATTACHMENT,
            file_content=data.get("file_content"),
            text_content=data.get("text_content"),
            description=data.get("description"),
            format=data.get("format"),
            size=data.get("size"),
            created_by=data.get("created_by"),
            created_at=parse_datetime(data.get("created_at")) or datetime.now(),
            updated_at=parse_datetime(data.get("updated_at")) or datetime.now(),
            related_solution_ids=parse_json(data.get("related_solution_ids"), []),
            understanding_status=UnderstandingStatus(data.get("understanding_status")) if data.get("understanding_status") else UnderstandingStatus.PENDING,
            metadata=metadata
        )
    
    def get_by_solution(self, solution_id: str) -> List[SolutionFile]:
        """
        获取方案的所有文件
        
        :param solution_id: 方案ID
        :return: 文件列表
        """
        all_files = self.read_all()
        result = []
        for file in all_files:
            if file.related_solution_ids and solution_id in file.related_solution_ids:
                result.append(file)
        return result
    
    def list(self, page: int = 1, page_size: int = 10, keyword: str = "") -> List[SolutionFile]:
        """
        分页查询文件列表
        
        :param page: 页码（从1开始）
        :param page_size: 每页条数
        :param keyword: 关键词（模糊匹配文件名）
        :return: 文件列表
        """
        all_files = self.read_all()
        
        if keyword:
            all_files = [f for f in all_files if keyword.lower() in f.file_name.lower()]
        
        all_files.sort(key=lambda x: x.created_at or datetime.now(), reverse=True)
        
        start = (page - 1) * page_size
        end = start + page_size
        
        return all_files[start:end]
    
    def count(self, keyword: str = "") -> int:
        """
        统计文件数量
        
        :param keyword: 关键词（可选）
        :return: 文件数量
        """
        all_files = self.read_all()
        
        if keyword:
            all_files = [f for f in all_files if keyword.lower() in f.file_name.lower()]
        
        return len(all_files)
    
    def get_pending_files(self, page: int = 1, page_size: int = 5) -> List[SolutionFile]:
        """
        获取待理解的文件列表（分页）
        
        :param page: 页码
        :param page_size: 每页条数
        :return: 待理解文件列表
        """
        all_files = self.read_all()
        pending_files = [f for f in all_files if f.understanding_status == UnderstandingStatus.PENDING]
        pending_files.sort(key=lambda x: x.created_at or datetime.now(), reverse=True)
        
        start = (page - 1) * page_size
        end = start + page_size
        
        return pending_files[start:end]
    
    def count_pending_files(self) -> int:
        """
        统计待理解文件数量
        
        :return: 待理解文件数量
        """
        all_files = self.read_all()
        return len([f for f in all_files if f.understanding_status == UnderstandingStatus.PENDING])
    
    def update_understanding_status(self, file_id: str, status: UnderstandingStatus):
        """
        更新文件理解状态
        
        :param file_id: 文件ID
        :param status: 理解状态
        """
        file_obj = self.read(file_id)
        if file_obj:
            file_obj.understanding_status = status
            file_obj.updated_at = datetime.now()
            self.update(file_obj)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    service = SolutionService()
    
    solution = Solution(
        solution_id="TEST001",
        name="测试方案",
        version="1.0",
        status=SolutionStatus.DRAFT,
        priority=SolutionPriority.HIGH,
        purpose="测试数据存储服务"
    )
    
    service.create(solution)
    print(f"创建方案: {solution.solution_id}")
    
    loaded = service.read("TEST001")
    print(f"读取方案: {loaded}")
    
    service.delete("TEST001")
    print("删除方案成功")
    
    service.disconnect()
