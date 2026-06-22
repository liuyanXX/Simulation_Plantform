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
from bo.solution import Solution, SolutionDocument, SolutionStatus, SolutionPriority, DocumentType


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
        # 解析JSON字段
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
            metadata=parse_json(data.get("metadata"))
        )
    
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
        # SQLite使用LIKE进行模糊查询
        all_solutions = self.read_all()
        return [s for s in all_solutions if keyword.lower() in s.name.lower()]


class SolutionDocumentService(SQLDatabaseService[SolutionDocument]):
    """
    方案文档服务类
    
    提供方案文档对象的数据库CRUD操作服务。
    """
    
    def _get_table_name(self) -> str:
        return "solution_documents"
    
    def _get_id_field(self) -> str:
        return "document_id"
    
    def _get_id_value(self, obj: SolutionDocument) -> str:
        return obj.document_id
    
    def _to_db_dict(self, obj: SolutionDocument) -> Dict[str, Any]:
        """将文档对象转换为数据库字典"""
        return {
            "document_id": obj.document_id,
            "file_name": obj.file_name,
            "version": obj.version,
            "document_type": obj.document_type.value if isinstance(obj.document_type, DocumentType) else obj.document_type,
            "file_content": obj.file_content if isinstance(obj.file_content, bytes) else None,
            "text_content": obj.text_content,
            "description": obj.description,
            "format": obj.format,
            "size": obj.size,
            "created_by": obj.created_by,
            "created_at": obj.created_at.isoformat() if isinstance(obj.created_at, datetime) else obj.created_at,
            "updated_at": obj.updated_at.isoformat() if isinstance(obj.updated_at, datetime) else obj.updated_at,
            "related_solution_ids": json.dumps(obj.related_solution_ids, ensure_ascii=False) if obj.related_solution_ids else None,
            "metadata": json.dumps(obj.metadata, ensure_ascii=False) if obj.metadata else None
        }
    
    def _from_db_dict(self, data: Dict[str, Any]) -> SolutionDocument:
        """将数据库字典转换为文档对象"""
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
            file_content=data.get("file_content"),
            text_content=data.get("text_content"),
            description=data.get("description"),
            format=data.get("format"),
            size=data.get("size"),
            created_by=data.get("created_by"),
            created_at=parse_datetime(data.get("created_at")) or datetime.now(),
            updated_at=parse_datetime(data.get("updated_at")) or datetime.now(),
            related_solution_ids=parse_json(data.get("related_solution_ids"), []),
            metadata=parse_json(data.get("metadata"))
        )
    
    def get_by_solution(self, solution_id: str) -> List[SolutionDocument]:
        """
        获取方案的所有文档
        
        :param solution_id: 方案ID
        :return: 文档列表
        """
        # 查询主文档或关联文档中包含该方案ID的文档
        all_docs = self.read_all()
        result = []
        for doc in all_docs:
            if doc.related_solution_ids and solution_id in doc.related_solution_ids:
                result.append(doc)
        return result


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 测试方案服务
    service = SolutionService()
    
    # 创建测试方案
    solution = Solution(
        solution_id="TEST001",
        name="测试方案",
        version="1.0",
        status=SolutionStatus.DRAFT,
        priority=SolutionPriority.HIGH,
        purpose="测试数据存储服务"
    )
    
    # 保存
    service.create(solution)
    print(f"创建方案: {solution.solution_id}")
    
    # 读取
    loaded = service.read("TEST001")
    print(f"读取方案: {loaded}")
    
    # 删除
    service.delete("TEST001")
    print("删除方案成功")
    
    service.disconnect()
