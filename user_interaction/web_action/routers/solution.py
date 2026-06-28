"""方案管理路由模块

提供方案列表、详情、上传、下载、删除等API接口。
"""

import os
import sys
import base64
from datetime import datetime
from typing import Optional, Dict, Any, List

from fastapi import APIRouter, Request, Query, Body, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse, StreamingResponse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from bo.solution import Solution, SolutionDocument, DocumentType, SolutionStatus, SolutionPriority, UnderstandingStatus

router = APIRouter()


@router.get("/list")
async def list_solutions(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    keyword: str = Query("")
):
    """获取方案文档列表（分页）"""
    try:
        from data_storage_services.sql_db_services.solution_service import SolutionDocumentService
        
        service = SolutionDocumentService()
        docs = service.list(page=page, page_size=page_size, keyword=keyword)
        total = service.count(keyword=keyword)
        
        result_list = []
        for doc in docs:
            files_info = []
            for file in doc.files:
                files_info.append({
                    "file_id": file.file_id,
                    "file_name": file.file_name,
                    "format": file.format,
                    "size": file.size,
                    "file_type": file.file_type.value,
                    "understanding_status": file.understanding_status.value
                })
            
            result_list.append({
                "document_id": doc.document_id,
                "file_name": doc.file_name,
                "version": doc.version,
                "document_type": doc.document_type.value,
                "description": doc.description,
                "created_by": doc.created_by,
                "understanding_status": doc.understanding_status.value,
                "created_at": doc.created_at.isoformat() if doc.created_at else None,
                "updated_at": doc.updated_at.isoformat() if doc.updated_at else None,
                "files_count": len(doc.files),
                "files": files_info
            })
        
        service.disconnect()
        
        return JSONResponse({
            "success": True,
            "message": "查询成功",
            "data": {
                "list": result_list,
                "total": total,
                "page": page,
                "page_size": page_size
            }
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "message": f"查询失败: {str(e)}",
            "data": None
        })


@router.get("/detail")
async def get_solution_detail(solution_id: str = Query(...)):
    """获取方案详情"""
    try:
        from data_storage_services.sql_db_services.solution_service import SolutionService
        
        service = SolutionService()
        solution = service.get(solution_id)
        
        if not solution:
            service.disconnect()
            return JSONResponse({
                "success": False,
                "message": "方案不存在",
                "data": None
            })
        
        documents = service.get_documents(solution_id)
        doc_list = []
        for doc in documents:
            doc_list.append({
                "document_id": doc.document_id,
                "file_name": doc.file_name,
                "version": doc.version,
                "document_type": doc.document_type.value,
                "format": doc.format,
                "size": doc.size,
                "created_at": doc.created_at.isoformat() if doc.created_at else None
            })
        
        service.disconnect()
        
        return JSONResponse({
            "success": True,
            "message": "查询成功",
            "data": {
                "solution_id": solution.solution_id,
                "name": solution.name,
                "version": solution.version,
                "status": solution.status.value,
                "priority": solution.priority.value,
                "purpose": solution.purpose,
                "objectives": solution.objectives,
                "initiatives": solution.initiatives,
                "working_mechanism": solution.working_mechanism,
                "organization": solution.organization,
                "personnel": solution.personnel,
                "roles": solution.roles,
                "work_content": solution.work_content,
                "constraints": solution.constraints,
                "risks": solution.risks,
                "issues": solution.issues,
                "other_notes": solution.other_notes,
                "tags": solution.tags,
                "description": solution.description,
                "owner": solution.owner,
                "created_by": solution.created_by,
                "effective_date": solution.effective_date.isoformat() if solution.effective_date else None,
                "expiry_date": solution.expiry_date.isoformat() if solution.expiry_date else None,
                "created_at": solution.created_at.isoformat() if solution.created_at else None,
                "updated_at": solution.updated_at.isoformat() if solution.updated_at else None,
                "documents": doc_list
            }
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "message": f"查询失败: {str(e)}",
            "data": None
        })


@router.post("/upload_document")
async def upload_document(
    document_id: str = Form(...),
    version: str = Form("1.0"),
    document_type: str = Form("main"),
    description: str = Form(""),
    created_by: str = Form(""),
    files: List[UploadFile] = File(None)
):
    """上传方案文档（SolutionDocument）"""
    try:
        from bo.solution import SolutionDocument, SolutionFile, DocumentType, UnderstandingStatus
        from data_storage_services.sql_db_services.solution_service import SolutionDocumentService
        
        service = SolutionDocumentService()
        
        if service.exists(document_id):
            service.disconnect()
            return JSONResponse({
                "success": False,
                "message": "文档ID已存在",
                "data": None
            })
        
        if not files:
            service.disconnect()
            return JSONResponse({
                "success": False,
                "message": "请至少上传一个文件",
                "data": None
            })
        
        doc_obj = SolutionDocument(
            document_id=document_id,
            file_name=files[0].filename.rsplit('.', 1)[0] if '.' in files[0].filename else files[0].filename,
            version=version,
            document_type=DocumentType(document_type),
            description=description,
            created_by=created_by,
            understanding_status=UnderstandingStatus.PENDING,
            related_solution_ids=[],
            files=[]
        )
        
        for idx, file in enumerate(files):
            content = await file.read()
            file_ext = file.filename.split('.')[-1].lower() if '.' in file.filename else 'unknown'
            file_type = DocumentType.MAIN if idx == 0 else DocumentType.ATTACHMENT
            
            file_obj = SolutionFile(
                file_id=f"{document_id}_FILE_{idx}",
                file_name=file.filename,
                version=version,
                file_type=file_type,
                file_content=content,
                text_content=None,
                description=description,
                format=file_ext,
                size=len(content),
                created_by=created_by,
                related_solution_ids=[],
                understanding_status=UnderstandingStatus.PENDING,
                document_id=document_id
            )
            
            doc_obj.add_file(file_obj)
        
        service.create(doc_obj)
        service.disconnect()
        
        return JSONResponse({
            "success": True,
            "message": f"文档 [{document_id}] 上传成功，共 {len(files)} 个文件",
            "data": {"document_id": document_id, "files_count": len(files)}
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "message": f"上传失败: {str(e)}",
            "data": None
        })


@router.delete("/delete_document")
async def delete_document(document_id: str = Query(...)):
    """删除单个方案文档"""
    try:
        from data_storage_services.sql_db_services.solution_service import SolutionDocumentService
        
        service = SolutionDocumentService()
        
        if not service.exists(document_id):
            service.disconnect()
            return JSONResponse({
                "success": False,
                "message": "文档不存在",
                "data": None
            })
        
        service.delete(document_id)
        service.disconnect()
        
        return JSONResponse({
            "success": True,
            "message": "文档删除成功",
            "data": {"document_id": document_id}
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "message": f"删除失败: {str(e)}",
            "data": None
        })


@router.post("/batch_delete_documents")
async def batch_delete_documents(request: Request):
    """批量删除方案文档"""
    try:
        import json
        
        body = await request.body()
        data = json.loads(body.decode('utf-8'))
        document_ids = data.get('document_ids', [])
        
        if not document_ids:
            return JSONResponse({
                "success": False,
                "message": "请选择要删除的文档",
                "data": None
            })
        
        from data_storage_services.sql_db_services.solution_service import SolutionDocumentService
        
        service = SolutionDocumentService()
        
        for did in document_ids:
            if service.exists(did):
                service.delete(did)
        
        service.disconnect()
        
        return JSONResponse({
            "success": True,
            "message": f"成功删除 {len(document_ids)} 个文档",
            "data": {"count": len(document_ids)}
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "message": f"删除失败: {str(e)}",
            "data": None
        })


@router.post("/upload")
async def upload_solution(
    solution_id: str = Form(...),
    name: str = Form(...),
    version: str = Form("1.0"),
    status: str = Form("draft"),
    priority: str = Form("medium"),
    purpose: str = Form(""),
    objectives: str = Form("[]"),
    initiatives: str = Form("[]"),
    working_mechanism: str = Form(""),
    organization: str = Form("[]"),
    personnel: str = Form("[]"),
    roles: str = Form("[]"),
    work_content: str = Form(""),
    constraints: str = Form("[]"),
    risks: str = Form("[]"),
    issues: str = Form("[]"),
    other_notes: str = Form(""),
    tags: str = Form("[]"),
    description: str = Form(""),
    owner: str = Form(""),
    created_by: str = Form(""),
    effective_date: str = Form(""),
    expiry_date: str = Form(""),
    files: List[UploadFile] = File(None)
):
    """上传方案（支持多文档上传）"""
    try:
        import json
        
        from bo.solution import Solution, SolutionDocument, DocumentType, SolutionStatus, SolutionPriority
        from data_storage_services.sql_db_services.solution_service import SolutionService
        
        objectives_list = json.loads(objectives) if objectives else []
        initiatives_list = json.loads(initiatives) if initiatives else []
        organization_list = json.loads(organization) if organization else []
        personnel_list = json.loads(personnel) if personnel else []
        roles_list = json.loads(roles) if roles else []
        constraints_list = json.loads(constraints) if constraints else []
        risks_list = json.loads(risks) if risks else []
        issues_list = json.loads(issues) if issues else []
        tags_list = json.loads(tags) if tags else []
        
        solution_obj = Solution(
            solution_id=solution_id,
            name=name,
            version=version,
            status=SolutionStatus(status),
            priority=SolutionPriority(priority),
            purpose=purpose,
            objectives=objectives_list,
            initiatives=initiatives_list,
            working_mechanism=working_mechanism,
            organization=organization_list,
            personnel=personnel_list,
            roles=roles_list,
            work_content=work_content,
            constraints=constraints_list,
            risks=risks_list,
            issues=issues_list,
            other_notes=other_notes,
            tags=tags_list,
            description=description,
            owner=owner,
            created_by=created_by
        )
        
        if effective_date:
            solution_obj.effective_date = datetime.fromisoformat(effective_date)
        if expiry_date:
            solution_obj.expiry_date = datetime.fromisoformat(expiry_date)
        
        service = SolutionService()
        
        if service.exists(solution_id):
            service.update(solution_obj)
        else:
            service.create(solution_obj)
        
        if files:
            for idx, file in enumerate(files):
                content = await file.read()
                
                doc_type = DocumentType.MAIN if idx == 0 else DocumentType.ATTACHMENT
                file_ext = file.filename.split('.')[-1].lower() if '.' in file.filename else 'unknown'
                
                doc_obj = SolutionDocument(
                    document_id=f"DOC_{solution_id}_{idx}_{int(datetime.now().timestamp())}",
                    file_name=file.filename,
                    version="1.0",
                    document_type=doc_type,
                    file_content=content,
                    format=file_ext,
                    size=len(content),
                    related_solution_ids=[solution_id]
                )
                
                service.create_document(doc_obj)
        
        service.disconnect()
        
        return JSONResponse({
            "success": True,
            "message": f"方案 [{name}] 上传成功",
            "data": {"solution_id": solution_id}
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "message": f"上传失败: {str(e)}",
            "data": None
        })


@router.delete("/delete")
async def delete_solution(solution_id: str = Query(...)):
    """删除单个方案"""
    try:
        from data_storage_services.sql_db_services.solution_service import SolutionService
        
        service = SolutionService()
        
        if not service.exists(solution_id):
            service.disconnect()
            return JSONResponse({
                "success": False,
                "message": "方案不存在",
                "data": None
            })
        
        service.delete(solution_id)
        service.disconnect()
        
        return JSONResponse({
            "success": True,
            "message": "方案删除成功",
            "data": {"solution_id": solution_id}
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "message": f"删除失败: {str(e)}",
            "data": None
        })


@router.post("/batch_delete")
async def batch_delete_solutions(
    request: Request
):
    """批量删除方案"""
    try:
        import json
        
        body = await request.body()
        data = json.loads(body.decode('utf-8'))
        solution_ids = data.get('solution_ids', [])
        
        if not solution_ids:
            return JSONResponse({
                "success": False,
                "message": "请选择要删除的方案",
                "data": None
            })
        
        from data_storage_services.sql_db_services.solution_service import SolutionService
        
        service = SolutionService()
        
        for sid in solution_ids:
            if service.exists(sid):
                service.delete(sid)
        
        service.disconnect()
        
        return JSONResponse({
            "success": True,
            "message": f"成功删除 {len(solution_ids)} 个方案",
            "data": {"count": len(solution_ids)}
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "message": f"删除失败: {str(e)}",
            "data": None
        })


@router.get("/download")
async def download_document(document_id: str = Query(...)):
    """下载文档"""
    try:
        from data_storage_services.sql_db_services.solution_service import SolutionDocumentService, SolutionFileService
        
        doc_service = SolutionDocumentService()
        document = doc_service.get(document_id)
        
        if not document:
            doc_service.disconnect()
            return JSONResponse({
                "success": False,
                "message": "文档不存在",
                "data": None
            })
        
        # 如果文档有文件，下载第一个文件
        if document.files and len(document.files) > 0:
            file_obj = document.files[0]
            file_service = SolutionFileService()
            full_file = file_service.read(file_obj.file_id)
            file_service.disconnect()
            
            if full_file and full_file.file_content:
                file_content = full_file.file_content
                file_name = full_file.file_name
            else:
                file_content = b""
                file_name = document.file_name or "document"
        else:
            # 如果没有文件，使用文档字段（兼容旧数据）
            file_content = document.file_content or b""
            file_name = document.file_name or "document"
        
        doc_service.disconnect()
        
        if isinstance(file_content, str):
            try:
                file_content = base64.b64decode(file_content)
            except:
                file_content = file_content.encode('utf-8')
        
        from fastapi.responses import StreamingResponse
        import io
        
        return StreamingResponse(
            io.BytesIO(file_content),
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f"attachment; filename={file_name}"
            }
        )
    except Exception as e:
        return JSONResponse({
            "success": False,
            "message": f"下载失败: {str(e)}",
            "data": None
        })


@router.get("/download_file")
async def download_file(file_id: str = Query(...)):
    """下载指定文件"""
    try:
        from data_storage_services.sql_db_services.solution_service import SolutionFileService
        
        service = SolutionFileService()
        file_obj = service.read(file_id)
        
        if not file_obj:
            service.disconnect()
            return JSONResponse({
                "success": False,
                "message": "文件不存在",
                "data": None
            })
        
        file_content = file_obj.file_content or b""
        file_name = file_obj.file_name or "file"
        
        service.disconnect()
        
        if isinstance(file_content, str):
            try:
                file_content = base64.b64decode(file_content)
            except:
                file_content = file_content.encode('utf-8')
        
        from fastapi.responses import StreamingResponse
        import io
        
        return StreamingResponse(
            io.BytesIO(file_content),
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f"attachment; filename={file_name}"
            }
        )
    except Exception as e:
        return JSONResponse({
            "success": False,
            "message": f"下载失败: {str(e)}",
            "data": None
        })


@router.post("/save")
async def save_solution(request: Request):
    """保存方案（兼容旧接口）"""
    try:
        import json
        
        body = await request.body()
        data = json.loads(body.decode('utf-8'))
        
        from bo.solution import Solution, SolutionStatus, SolutionPriority
        from data_storage_services.sql_db_services.solution_service import SolutionService
        
        solution_obj = Solution(
            solution_id=data.get('solution_id', ''),
            name=data.get('name', ''),
            version=data.get('version', '1.0'),
            priority=SolutionPriority(data.get('priority', 'medium')),
            purpose=data.get('purpose', ''),
            objectives=data.get('objectives', []),
            initiatives=data.get('initiatives', []),
            working_mechanism=data.get('working_mechanism', ''),
            organization=data.get('organization', []),
            personnel=data.get('personnel', []),
            roles=data.get('roles', []),
            work_content=data.get('work_content', ''),
            constraints=data.get('constraints', []),
            risks=data.get('risks', []),
            issues=data.get('issues', []),
            other_notes=data.get('other_notes', ''),
            tags=data.get('tags', []),
            description=data.get('description', ''),
            owner=data.get('owner', ''),
            created_by=data.get('created_by', '')
        )
        
        service = SolutionService()
        
        if service.exists(solution_obj.solution_id):
            service.update(solution_obj)
        else:
            service.create(solution_obj)
        
        service.disconnect()
        
        return JSONResponse({
            "success": True,
            "message": f"方案 [{solution_obj.name}] 保存成功",
            "data": {"solution_id": solution_obj.solution_id}
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "message": f"保存失败: {str(e)}",
            "data": None
        })


@router.get("/pending_documents")
async def list_pending_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(5, ge=1, le=100)
):
    """获取待理解文档列表（分页）"""
    try:
        from data_storage_services.sql_db_services.solution_service import SolutionDocumentService
        
        service = SolutionDocumentService()
        docs = service.get_pending_documents(page=page, page_size=page_size)
        total = service.count_pending_documents()
        
        result_list = []
        for doc in docs:
            # 获取文件信息
            files_info = []
            for file in doc.files:
                files_info.append({
                    "file_id": file.file_id,
                    "file_name": file.file_name,
                    "format": file.format,
                    "size": file.size,
                    "file_type": file.file_type.value,
                    "understanding_status": file.understanding_status.value
                })
            
            result_list.append({
                "document_id": doc.document_id,
                "file_name": doc.file_name,
                "version": doc.version,
                "document_type": doc.document_type.value,
                "description": doc.description,
                "created_by": doc.created_by,
                "understanding_status": doc.understanding_status.value,
                "created_at": doc.created_at.isoformat() if doc.created_at else None,
                "updated_at": doc.updated_at.isoformat() if doc.updated_at else None,
                "files_count": len(doc.files),
                "files": files_info
            })
        
        service.disconnect()
        
        return JSONResponse({
            "success": True,
            "message": "查询成功",
            "data": {
                "list": result_list,
                "total": total,
                "page": page,
                "page_size": page_size
            }
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "message": f"查询失败: {str(e)}",
            "data": None
        })


@router.post("/start_conversion")
async def start_conversion(request: Request):
    """启动方案理解转换"""
    try:
        import json
        
        body = await request.body()
        data = json.loads(body.decode('utf-8'))
        document_id = data.get('document_id')
        
        if not document_id:
            return JSONResponse({
                "success": False,
                "message": "文档ID不能为空",
                "data": None
            })
        
        from data_storage_services.sql_db_services.solution_service import SolutionDocumentService, SolutionService
        
        doc_service = SolutionDocumentService()
        document = doc_service.read(document_id)
        
        if not document:
            doc_service.disconnect()
            return JSONResponse({
                "success": False,
                "message": "文档不存在",
                "data": None
            })
        
        doc_service.update_understanding_status(document_id, UnderstandingStatus.PROCESSING)
        doc_service.disconnect()
        
        from solution_management_services.solution_understanding_service import SolutionUnderstandingService
        
        understanding_service = SolutionUnderstandingService()
        result = understanding_service.understand_document(document)
        
        doc_service = SolutionDocumentService()
        
        if result.success and result.solution:
            solution = result.solution
            solution.main_document_id = document_id
            solution.created_at = datetime.now()
            solution.updated_at = datetime.now()
            
            sol_service = SolutionService()
            
            if sol_service.exists(solution.solution_id):
                sol_service.update(solution)
            else:
                sol_service.create(solution)
            
            sol_service.disconnect()
            
            document.add_related_solution(solution.solution_id)
            document.understanding_status = UnderstandingStatus.UNDERSTOOD
            document.updated_at = datetime.now()
            doc_service.update(document)
            
            doc_service.disconnect()
            
            return JSONResponse({
                "success": True,
                "message": "方案理解成功",
                "data": {
                    "solution_id": solution.solution_id,
                    "solution_name": solution.name
                }
            })
        else:
            doc_service.update_understanding_status(document_id, UnderstandingStatus.FAILED)
            doc_service.disconnect()
            
            return JSONResponse({
                "success": False,
                "message": result.error_message or "方案理解失败",
                "data": None
            })
    except Exception as e:
        try:
            from data_storage_services.sql_db_services.solution_service import SolutionDocumentService
            doc_service = SolutionDocumentService()
            body = await request.body()
            data = json.loads(body.decode('utf-8'))
            document_id = data.get('document_id')
            if document_id:
                doc_service.update_understanding_status(document_id, UnderstandingStatus.FAILED)
            doc_service.disconnect()
        except:
            pass
        
        return JSONResponse({
            "success": False,
            "message": f"转换失败: {str(e)}",
            "data": None
        })


@router.post("/update")
async def update_solution(request: Request):
    """更新方案对象"""
    try:
        import json
        
        body = await request.body()
        data = json.loads(body.decode('utf-8'))
        
        from bo.solution import Solution, SolutionStatus, SolutionPriority
        from data_storage_services.sql_db_services.solution_service import SolutionService
        
        solution_id = data.get('solution_id')
        
        if not solution_id:
            return JSONResponse({
                "success": False,
                "message": "方案ID不能为空",
                "data": None
            })
        
        service = SolutionService()
        
        if not service.exists(solution_id):
            service.disconnect()
            return JSONResponse({
                "success": False,
                "message": "方案不存在",
                "data": None
            })
        
        existing_solution = service.read(solution_id)
        
        solution_obj = Solution(
            solution_id=solution_id,
            name=data.get('name', existing_solution.name),
            version=data.get('version', existing_solution.version),
            status=SolutionStatus(data.get('status', existing_solution.status.value)),
            priority=SolutionPriority(data.get('priority', existing_solution.priority.value)),
            purpose=data.get('purpose', existing_solution.purpose),
            objectives=data.get('objectives', existing_solution.objectives),
            initiatives=data.get('initiatives', existing_solution.initiatives),
            working_mechanism=data.get('working_mechanism', existing_solution.working_mechanism),
            organization=data.get('organization', existing_solution.organization),
            personnel=data.get('personnel', existing_solution.personnel),
            roles=data.get('roles', existing_solution.roles),
            work_content=data.get('work_content', existing_solution.work_content),
            constraints=data.get('constraints', existing_solution.constraints),
            risks=data.get('risks', existing_solution.risks),
            issues=data.get('issues', existing_solution.issues),
            other_notes=data.get('other_notes', existing_solution.other_notes),
            tags=data.get('tags', existing_solution.tags),
            description=data.get('description', existing_solution.description),
            owner=data.get('owner', existing_solution.owner),
            created_by=data.get('created_by', existing_solution.created_by),
            created_at=existing_solution.created_at,
            updated_at=datetime.now(),
            effective_date=data.get('effective_date', existing_solution.effective_date),
            expiry_date=data.get('expiry_date', existing_solution.expiry_date)
        )
        
        service.update(solution_obj)
        service.disconnect()
        
        return JSONResponse({
            "success": True,
            "message": f"方案 [{solution_obj.name}] 更新成功",
            "data": {"solution_id": solution_id}
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "message": f"更新失败: {str(e)}",
            "data": None
        })


@router.post("/batch_delete_with_rollback")
async def batch_delete_solutions_with_rollback(request: Request):
    """批量删除方案并回退文档状态"""
    try:
        import json
        
        body = await request.body()
        data = json.loads(body.decode('utf-8'))
        solution_ids = data.get('solution_ids', [])
        
        if not solution_ids:
            return JSONResponse({
                "success": False,
                "message": "请选择要删除的方案",
                "data": None
            })
        
        from data_storage_services.sql_db_services.solution_service import SolutionService, SolutionDocumentService
        
        sol_service = SolutionService()
        doc_service = SolutionDocumentService()
        
        for sid in solution_ids:
            if sol_service.exists(sid):
                documents = doc_service.get_by_solution(sid)
                
                for doc in documents:
                    doc.understanding_status = UnderstandingStatus.PENDING
                    doc.remove_related_solution(sid)
                    doc.updated_at = datetime.now()
                    doc_service.update(doc)
                
                sol_service.delete(sid)
        
        sol_service.disconnect()
        doc_service.disconnect()
        
        return JSONResponse({
            "success": True,
            "message": f"成功删除 {len(solution_ids)} 个方案，相关文档状态已回退",
            "data": {"count": len(solution_ids)}
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "message": f"删除失败: {str(e)}",
            "data": None
        })
